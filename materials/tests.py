from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from core.models import Project, Category, Subcategory, UnitOfMeasure, PurchaseUnit
from materials.models import MaterialCatalogItem, MaterialBudgetItem
from materials.services import MaterialBudgetService, MaterialBudgetMetricsService


class MaterialBudgetServiceTestCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Torre Titanium")
        self.category = Category.objects.create(name="Materiales")
        self.subcategory = Subcategory.objects.create(category=self.category, name="Fierros")
        self.uom_ml = UnitOfMeasure.objects.create(name="Metro lineal", abbreviation="ml")
        self.pu_barra = PurchaseUnit.objects.create(name="Barra 12m", abbreviation="barra")

        self.catalog_item = MaterialCatalogItem.objects.create(
            subcategory=self.subcategory,
            name="Fierro corrugado 12mm",
            unit_measure=self.uom_ml,
            unit_purchase=self.pu_barra,
            conversion_factor=Decimal('12.0000'),
            weight_per_purchase_unit=Decimal('10.6500'),
            waste_pct=Decimal('0.1000'),
            price_per_purchase_unit=Decimal('65.50'),
            is_active=True
        )

    def test_create_from_catalog_ceil_calculation(self):
        # 100 ml con 10% desperdicio = 110 ml. 110 / 12 = 9.1667 -> ceil = 10 barras
        item = MaterialBudgetService.create_from_catalog(
            project=self.project,
            catalog_item=self.catalog_item,
            quantity_obra=Decimal('100.0000'),
            detail="Para columnas piso 1"
        )
        self.assertEqual(item.quantity_purchase, Decimal('10'))
        self.assertEqual(item.estimated_cost, Decimal('655.00'))
        self.assertEqual(item.weight_total, Decimal('106.5000'))
        self.assertFalse(item.is_global)

    def test_create_global_from_catalog(self):
        item = MaterialBudgetService.create_global_from_catalog(
            project=self.project,
            catalog_item=self.catalog_item,
            quantity_purchase=Decimal('5.0000'),
            price_per_purchase_unit=Decimal('70.00'),
            detail="Reserva global"
        )
        self.assertTrue(item.is_global)
        self.assertIsNone(item.quantity_obra)
        self.assertEqual(item.quantity_purchase, Decimal('5.0000'))
        self.assertEqual(item.estimated_cost, Decimal('350.00'))

    def test_create_custom_item(self):
        item = MaterialBudgetService.create_custom_item(
            project=self.project,
            subcategory=self.subcategory,
            name="Clavos de 3 pulgadas",
            unit_measure=self.uom_ml,
            unit_purchase=self.pu_barra,
            price_per_purchase_unit=Decimal('25.00'),
            is_global=True,
            quantity_purchase=Decimal('10.0000'),
            detail="Para encofrado"
        )
        self.assertIsNone(item.catalog_item)
        self.assertEqual(item.name, "Clavos de 3 pulgadas")
        self.assertEqual(item.estimated_cost, Decimal('250.00'))


class MaterialBudgetAPITestCase(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Condominio El Prado")
        self.category = Category.objects.create(name="Obra Gruesa")
        self.subcategory = Subcategory.objects.create(category=self.category, name="Acero")
        self.uom_ml = UnitOfMeasure.objects.create(name="Metro lineal", abbreviation="ml")
        self.pu_barra = PurchaseUnit.objects.create(name="Barra 12m", abbreviation="barra")

        self.catalog_item = MaterialCatalogItem.objects.create(
            subcategory=self.subcategory,
            name="Fierro corrugado 8mm",
            unit_measure=self.uom_ml,
            unit_purchase=self.pu_barra,
            conversion_factor=Decimal('12.0000'),
            weight_per_purchase_unit=Decimal('4.7400'),
            waste_pct=Decimal('0.0500'),
            price_per_purchase_unit=Decimal('35.00'),
            is_active=True
        )

    def test_catalog_grouped_by_subcategory(self):
        response = self.client.get('/api/materials/catalog/grouped-by-subcategory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        group = response.data[0]
        self.assertIn('subcategory_name', group)
        self.assertIn('items', group)

    def test_from_catalog_endpoint(self):
        payload = {
            "project": self.project.id,
            "catalog_item": self.catalog_item.id,
            "quantity_obra": 60.0,
            "detail": "Estribos vigas",
            "waste_pct": 0.05,
            "price_override": 36.00
        }
        response = self.client.post('/api/materials/budget/from-catalog/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(str(response.data['price_per_purchase_unit'])), Decimal('36.00'))
        self.assertIsNotNone(response.data['catalog_item_detail'])

    def test_from_catalog_global_endpoint(self):
        payload = {
            "project": self.project.id,
            "catalog_item": self.catalog_item.id,
            "quantity_purchase": 4.0,
            "price_per_purchase_unit": 35.0,
            "detail": "Compra preventiva"
        }
        response = self.client.post('/api/materials/budget/from-catalog-global/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_global'])

    def test_custom_budget_item_endpoint(self):
        payload = {
            "project": self.project.id,
            "subcategory": self.subcategory.id,
            "name": "Alambre de amarre especial",
            "unit_measure": self.uom_ml.id,
            "unit_purchase": self.pu_barra.id,
            "price_per_purchase_unit": 50.0,
            "is_global": True,
            "quantity_purchase": 2.0,
            "detail": "Rollos de 1kg"
        }
        response = self.client.post('/api/materials/budget/custom/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Alambre de amarre especial")

    def test_by_project_and_summary_endpoints(self):
        # Crear 1 item normal y 1 global
        MaterialBudgetService.create_from_catalog(
            project=self.project,
            catalog_item=self.catalog_item,
            quantity_obra=Decimal('120.0000')  # 120 * 1.05 = 126 / 12 = 10.5 -> 11 barras * 35 = 385.00
        )
        MaterialBudgetService.create_global_from_catalog(
            project=self.project,
            catalog_item=self.catalog_item,
            quantity_purchase=Decimal('2.0000'),
            price_per_purchase_unit=Decimal('35.00')  # 2 * 35 = 70.00
        )

        # Probar endpoint by-project
        resp_by_proj = self.client.get(f'/api/materials/budget/by-project/?project_id={self.project.id}')
        self.assertEqual(resp_by_proj.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_by_proj.data['total_items_count'], 2)
        self.assertEqual(Decimal(str(resp_by_proj.data['total_materials_cost'])), Decimal('455.00'))

        # Probar endpoint summary (agregación SQL en PostgreSQL)
        resp_summary = self.client.get(f'/api/materials/budget/summary/?project_id={self.project.id}')
        self.assertEqual(resp_summary.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_summary.data['total_items'], 2)
        self.assertEqual(resp_summary.data['normal_items_count'], 1)
        self.assertEqual(resp_summary.data['global_items_count'], 1)
        self.assertEqual(Decimal(str(resp_summary.data['total_materials_cost'])), Decimal('455.00'))

    def test_validation_error_on_negative_quantity(self):
        payload = {
            "project": self.project.id,
            "catalog_item": self.catalog_item.id,
            "quantity_obra": -10.0,
        }
        response = self.client.post('/api/materials/budget/from-catalog/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
