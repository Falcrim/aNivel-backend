from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models.project import Project
from inventory.models.location import Location, LocationType
from inventory.models.tool_category import ToolCategory
from inventory.models.tool import Tool, ToolStatus
from inventory.models.tool_transfer import ToolTransfer
from inventory.services.transfer_service import ToolTransferService


class ProjectLocationSignalTest(TestCase):
    """Prueba la sincronización automática de Locaciones al crear/modificar Obras."""

    def test_auto_creates_location_on_project_creation(self):
        project = Project.objects.create(name="Torre Titanium")
        location = Location.objects.filter(project=project).first()

        self.assertIsNotNone(location)
        self.assertEqual(location.name, "Obra: Torre Titanium")
        self.assertEqual(location.location_type, LocationType.PROJECT)
        self.assertTrue(location.is_active)

    def test_syncs_location_name_on_project_update(self):
        project = Project.objects.create(name="Edificio Las Palmas")
        project.name = "Edificio Las Palmas - Fase 2"
        project.save()

        location = Location.objects.get(project=project)
        self.assertEqual(location.name, "Obra: Edificio Las Palmas - Fase 2")


class InventoryAPITestCase(TestCase):
    """Pruebas para los endpoints REST del módulo de inventario."""

    def setUp(self):
        self.client = APIClient()

        # Locación almacén central
        self.central_warehouse = Location.objects.create(
            name="Almacén Central",
            code="ALM-01",
            location_type=LocationType.WAREHOUSE
        )

        # Categoría
        self.cat_electric = ToolCategory.objects.create(
            name="Herramientas Eléctricas",
            description="Equipos a batería y cable"
        )

        # Proyecto (dispara la creación de su locación)
        self.project = Project.objects.create(name="Residencial Los Sauces")
        self.project_location = Location.objects.get(project=self.project)

        # Herramienta inicial en Almacén Central
        self.tool = Tool.objects.create(
            code="TAL-001",
            name="Taladro Percutor DeWalt 20V",
            category=self.cat_electric,
            detail="Incluye 2 baterías y cargador rápido",
            brand="DeWalt",
            model_name="DCD996",
            serial_number="DW-2024-8899",
            current_location=self.central_warehouse,
            status=ToolStatus.AVAILABLE,
            purchase_price=250.00
        )

    def test_list_locations(self):
        response = self.client.get('/api/inventory/locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Almacén + Obra

    def test_filter_locations_by_type(self):
        response = self.client.get('/api/inventory/locations/?location_type=WAREHOUSE')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Almacén Central")

    def test_create_tool_api(self):
        payload = {
            "code": "PAL-001",
            "name": "Pala de punta Truper",
            "category": self.cat_electric.pk,
            "detail": "Mango de madera reforzado",
            "current_location": self.central_warehouse.pk,
            "status": ToolStatus.AVAILABLE,
            "purchase_price": "25.50"
        }
        response = self.client.post('/api/inventory/tools/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], "PAL-001")
        self.assertEqual(response.data['current_location_name'], "Almacén Central")

    def test_prevent_duplicate_tool_code(self):
        payload = {
            "code": "tal-001",  # Mismo código en minúscula
            "name": "Otro Taladro",
            "current_location": self.central_warehouse.pk,
            "status": ToolStatus.AVAILABLE
        }
        response = self.client.post('/api/inventory/tools/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data)

    def test_transfer_tool_to_project_updates_location_and_status(self):
        """Trasladar una herramienta a una obra debe actualizar su ubicación y cambiar su estado a IN_USE."""
        payload = {
            "tool_id": self.tool.pk,
            "destination_location_id": self.project_location.pk,
            "responsible_person": "Ing. Carlos Mendoza",
            "notes": "Entrega para fase de muros"
        }
        response = self.client.post('/api/inventory/transfers/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verificar herramienta actualizada
        self.tool.refresh_from_db()
        self.assertEqual(self.tool.current_location_id, self.project_location.pk)
        self.assertEqual(self.tool.status, ToolStatus.IN_USE)

        # Verificar registro de transferencia
        transfer = ToolTransfer.objects.get(pk=response.data['id'])
        self.assertEqual(transfer.origin_location_id, self.central_warehouse.pk)
        self.assertEqual(transfer.destination_location_id, self.project_location.pk)
        self.assertEqual(transfer.responsible_person, "Ing. Carlos Mendoza")

    def test_transfer_inactive_tool_preserves_inactive_status(self):
        """Si una herramienta estaba inactiva/archivada y se traslada, se mueve pero permanece inactiva."""
        self.tool.is_active = False
        self.tool.save()

        payload = {
            "tool_id": self.tool.pk,
            "destination_location_id": self.project_location.pk,
            "responsible_person": "Capataz Juan",
        }
        response = self.client.post('/api/inventory/transfers/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.tool.refresh_from_db()
        self.assertFalse(self.tool.is_active)
        self.assertEqual(self.tool.current_location_id, self.project_location.pk)

    def test_tool_history_endpoint(self):
        # Ejecutar 2 traslados
        workshop = Location.objects.create(name="Taller Central", location_type=LocationType.WORKSHOP)
        
        # 1. De Almacén a Obra
        ToolTransferService.execute_transfer(
            tool=self.tool,
            destination_location=self.project_location,
            responsible_person="Capataz Juan"
        )
        
        # 2. De Obra a Taller
        ToolTransferService.execute_transfer(
            tool=self.tool,
            destination_location=workshop,
            responsible_person="Mecánico Pedro"
        )

        response = self.client.get(f'/api/inventory/tools/{self.tool.pk}/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # El más reciente primero
        self.assertEqual(response.data[0]['destination_location_name'], "Taller Central")
        self.assertEqual(response.data[1]['destination_location_name'], "Obra: Residencial Los Sauces")
