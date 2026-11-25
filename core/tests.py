import os
from decimal import Decimal
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from core.models import (
    Project,
    Category,
    Subcategory,
    UnitOfMeasure,
    PurchaseUnit,
    Supplier,
    SupplierType,
    ConstructionStage,
    BudgetItem,
    BudgetCategoryType,
)


class CoreModelsTestCase(TestCase):
    def setUp(self):
        self.category, _ = Category.objects.get_or_create(
            code="materials",
            defaults={"name": "Materiales", "is_active": True},
        )
        self.subcat = Subcategory.objects.create(category=self.category, name="Fierros")
        self.uom = UnitOfMeasure.objects.create(name="Metros Lineales", abbreviation="ml")
        self.pu = PurchaseUnit.objects.create(name="Barra 12m", abbreviation="barra")

    def test_str_representations(self):
        self.assertEqual(str(self.category), "Materiales")
        self.assertEqual(str(self.subcat), "Materiales / Fierros")
        self.assertEqual(str(self.uom), "Metros Lineales (ml)")
        self.assertEqual(str(self.pu), "Barra 12m (barra)")


class CoreAPITestCase(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Edificio Los Pinos")
        self.category = Category.objects.create(name="Estructuras")
        self.subcat1 = Subcategory.objects.create(category=self.category, name="Hormigón")
        self.subcat2 = Subcategory.objects.create(category=self.category, name="Fierro Corrugado")
        self.uom = UnitOfMeasure.objects.create(name="Metro Cuadrado", abbreviation="m2")
        self.pu = PurchaseUnit.objects.create(name="Bolsa 50kg", abbreviation="bolsa")

    def test_list_projects(self):
        response = self.client.get('/api/core/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_project(self):
        payload = {"name": "Residencial Mirador"}
        response = self.client.post('/api/core/projects/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Residencial Mirador")

    def test_categories_with_annotated_subcategories_count(self):
        response = self.client.get('/api/core/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cat_data = next((c for c in response.data if c['id'] == self.category.id), None)
        self.assertIsNotNone(cat_data)
        self.assertEqual(cat_data['subcategories_count'], 2)
        self.assertEqual(len(cat_data['subcategories']), 2)

    def test_category_subcategories_action(self):
        response = self.client.get(f'/api/core/categories/{self.category.id}/subcategories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_default_categories_seeded_by_migration(self):
        response = self.client.get('/api/core/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_code = {c['code']: c for c in response.data}
        self.assertIn('materials', by_code)
        self.assertTrue(by_code['materials']['is_active'])
        self.assertIn('labor', by_code)
        self.assertTrue(by_code['labor']['is_active'])
        self.assertIn('operating', by_code)
        self.assertFalse(by_code['operating']['is_active'])
        self.assertIn('administrative', by_code)
        self.assertFalse(by_code['administrative']['is_active'])

    def test_category_create_and_delete_blocked(self):
        create_resp = self.client.post('/api/core/categories/', {'name': 'Nueva Categoria'})
        self.assertEqual(create_resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        delete_resp = self.client.delete(f'/api/core/categories/{self.category.id}/')
        self.assertEqual(delete_resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_category_rename_preserves_code_and_is_active(self):
        original_code = self.category.code
        original_active = self.category.is_active
        resp = self.client.patch(
            f'/api/core/categories/{self.category.id}/',
            {'name': 'Insumos Generales', 'code': 'hacked', 'is_active': False},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Insumos Generales')
        self.assertEqual(self.category.code, original_code)
        self.assertEqual(self.category.is_active, original_active)

    def test_subcategories_filtering(self):
        response = self.client.get(f'/api/core/subcategories/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_pagination_standard_response(self):
        for i in range(5):
            Project.objects.create(name=f"Proyecto Extra {i}")

        response = self.client.get('/api/core/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 6)
        self.assertIsInstance(response.data['results'], list)

    def test_pagination_custom_page_size(self):
        for i in range(5):
            Project.objects.create(name=f"Proyecto Paginado {i}")

        response = self.client.get('/api/core/projects/?page_size=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['next'])

    def test_pagination_disabled_via_query_param(self):
        for i in range(3):
            Project.objects.create(name=f"Proyecto Sin Paginacion {i}")

        response = self.client.get('/api/core/projects/?paginate=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 4)


class SupplierAPITestCase(APITestCase):
    def setUp(self):
        self.supplier_mat = Supplier.objects.create(
            name="Monterrey S.R.L.",
            supplier_type=SupplierType.MATERIAL,
            contact_name="Carlos Monterrey",
            phone="70012345",
            email="ventas@monterrey.com.bo",
            address="Av. Banzer 4to Anillo"
        )
        self.supplier_lab = Supplier.objects.create(
            name="Cuadrilla Hermanos Flores",
            supplier_type=SupplierType.LABOR,
            contact_name="Juan Flores",
            phone="71098765",
            email="cuadrilla.flores@gmail.com"
        )

    def test_list_suppliers(self):
        response = self.client.get('/api/core/suppliers/?paginate=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_filter_by_supplier_type(self):
        Supplier.objects.create(
            name="Constructora Integral Ambos",
            supplier_type=SupplierType.BOTH,
        )
        response_mat = self.client.get('/api/core/suppliers/?supplier_type=material&paginate=false')
        self.assertEqual(response_mat.status_code, status.HTTP_200_OK)
        names_mat = [s['name'] for s in response_mat.data]
        self.assertIn("Monterrey S.R.L.", names_mat)
        self.assertIn("Constructora Integral Ambos", names_mat)
        self.assertNotIn("Cuadrilla Hermanos Flores", names_mat)

        response_lab = self.client.get('/api/core/suppliers/?supplier_type=labor&paginate=false')
        self.assertEqual(response_lab.status_code, status.HTTP_200_OK)
        names_lab = [s['name'] for s in response_lab.data]
        self.assertIn("Cuadrilla Hermanos Flores", names_lab)
        self.assertIn("Constructora Integral Ambos", names_lab)
        self.assertNotIn("Monterrey S.R.L.", names_lab)

    def test_search_suppliers(self):
        response = self.client.get('/api/core/suppliers/?search=Flores&paginate=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Cuadrilla Hermanos Flores")

    def test_create_supplier_with_photo(self):
        dummy_img = SimpleUploadedFile(
            "logo_prometeo.png",
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRdummy",
            content_type="image/png"
        )
        payload = {
            "name": "Prometeo Aceros",
            "supplier_type": SupplierType.MATERIAL,
            "contact_name": "Ing. Marco Pérez",
            "phone": "77788990",
            "email": "contacto@prometeo.com",
            "address": "Parque Industrial Manzana 12",
            "photo": dummy_img,
            "notes": "Descuento 5% en compras mayores a 10 toneladas"
        }
        response = self.client.post('/api/core/suppliers/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Prometeo Aceros")
        self.assertTrue(response.data['photo_url'].endswith('.png'))

        sup_id = response.data['id']
        supplier = Supplier.objects.get(id=sup_id)
        self.assertTrue(os.path.exists(supplier.photo.path))

        photo_path = supplier.photo.path
        del_resp = self.client.delete(f'/api/core/suppliers/{sup_id}/')
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(os.path.exists(photo_path))

    def test_duplicate_supplier_name_rejected(self):
        payload = {
            "name": "Monterrey S.R.L.",
            "supplier_type": SupplierType.MATERIAL,
        }
        response = self.client.post('/api/core/suppliers/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)


class ConstructionStageAPITestCase(APITestCase):
    def setUp(self):
        ConstructionStage.objects.all().delete()
        self.stage1 = ConstructionStage.objects.create(
            name="Obra Bruta",
            description="Cimientos, estructura portante y losas",
            order=1,
            color="amber"
        )
        self.stage2 = ConstructionStage.objects.create(
            name="Obra Fina",
            description="Yeso, pinturas y porcelanatos",
            order=2,
            color="emerald"
        )

    def tearDown(self):
        ConstructionStage.objects.all().delete()

    def test_list_stages_ordered(self):
        response = self.client.get('/api/core/stages/?paginate=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], "Obra Bruta")
        self.assertEqual(response.data[1]['name'], "Obra Fina")

    def test_create_stage(self):
        payload = {
            "name": "Equipamiento",
            "description": "Luminarias y muebles empotrados",
            "order": 3,
            "color": "blue"
        }
        response = self.client.post('/api/core/stages/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Equipamiento")
        self.assertEqual(response.data['order'], 3)

    def test_unique_stage_name(self):
        payload = {"name": "Obra Bruta"}
        response = self.client.post('/api/core/stages/', payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UnifiedBudgetStrategyTestCase(TestCase):
    """Pruebas unitarias de las estrategias DDD del motor presupuestario."""

    def setUp(self):
        self.project = Project.objects.create(
            name="Condominio Los Robles",
            built_area=Decimal('200.00'),
            exchange_rate=Decimal('6.9700')
        )
        self.category, _ = Category.objects.get_or_create(
            code="materials",
            defaults={"name": "Materiales", "is_active": True},
        )
        self.subcategory = Subcategory.objects.create(category=self.category, name="Fierros")
        self.uom_ml = UnitOfMeasure.objects.create(name="Metro Lineal", abbreviation="ml")
        self.pu_barra = PurchaseUnit.objects.create(name="Barra 12m", abbreviation="barra")

    def test_material_strategy_ceil_enabled(self):
        # 100 ml con 10% merma = 110 ml. 110 / 12 = 9.1667 -> ceil = 10 barras
        item = BudgetItem.objects.create(
            project=self.project,
            category_type=BudgetCategoryType.MATERIALS,
            subcategory=self.subcategory,
            name="Fierro 12mm",
            unit_measure=self.uom_ml,
            unit_purchase=self.pu_barra,
            conversion_factor=Decimal('12.0000'),
            waste_pct=Decimal('0.1000'),
            quantity_obra=Decimal('100.0000'),
            unit_price=Decimal('70.00'),
            weight_per_purchase_unit=Decimal('10.5000'),
            apply_ceil=True
        )
        self.assertEqual(item.quantity_purchase, Decimal('10'))
        self.assertEqual(item.estimated_cost, Decimal('700.00'))
        self.assertEqual(item.weight_total, Decimal('105.0000'))
        self.assertEqual(item.cost_usd, Decimal('100.43'))

    def test_material_strategy_ceil_disabled(self):
        # 100 ml con 10% merma = 110 ml. 110 / 12 = 9.1667 barras exactas
        item = BudgetItem.objects.create(
            project=self.project,
            category_type=BudgetCategoryType.MATERIALS,
            subcategory=self.subcategory,
            name="Fierro 12mm Fraccional",
            unit_measure=self.uom_ml,
            unit_purchase=self.pu_barra,
            conversion_factor=Decimal('12.0000'),
            waste_pct=Decimal('0.1000'),
            quantity_obra=Decimal('100.0000'),
            unit_price=Decimal('70.00'),
            apply_ceil=False
        )
        self.assertEqual(item.quantity_purchase, Decimal('9.1667'))
        self.assertEqual(item.estimated_cost, Decimal('641.67'))

    def test_labor_strategy_metrics(self):
        item = BudgetItem.objects.create(
            project=self.project,
            category_type=BudgetCategoryType.LABOR,
            subcategory=self.subcategory,
            name="Encofrado de losas",
            unit_measure=self.uom_ml,
            quantity_obra=Decimal('150.0000'),
            unit_price=Decimal('80.00'),
            contractor_name="Cuadrilla Don Carlos"
        )
        self.assertEqual(item.estimated_cost, Decimal('12000.00'))
        self.assertIsNone(item.weight_total)
        # 12000 / 6.97 = 1721.66 USD. 1721.66 / 200 m2 = 8.61 $/m2
        self.assertEqual(item.cost_usd, Decimal('1721.66'))
        self.assertEqual(item.cost_per_m2_usd, Decimal('8.61'))

    def test_operating_and_admin_strategy_percentage(self):
        # Gasto administrativo / utilidad corporativa del 15% sobre base de 100,000 Bs
        admin_item = BudgetItem.objects.create(
            project=self.project,
            category_type=BudgetCategoryType.ADMINISTRATIVE,
            name="Utilidad de Obra 15%",
            percentage_applied=Decimal('0.1500'),
            target_base_cost=Decimal('100000.00')
        )
        self.assertEqual(admin_item.estimated_cost, Decimal('15000.00'))

    def test_operating_strategy_validations(self):
        item = BudgetItem(
            project=self.project,
            category_type=BudgetCategoryType.OPERATING,
            name="Gastos Legales",
            percentage_applied=Decimal('-0.05'),
            target_base_cost=Decimal('-1000.00')
        )
        with self.assertRaises(Exception):
            item.full_clean()

    def test_cached_property_memoization(self):
        item = BudgetItem.objects.create(
            project=self.project,
            category_type=BudgetCategoryType.LABOR,
            subcategory=self.subcategory,
            name="Pintura General",
            unit_measure=self.uom_ml,
            quantity_obra=Decimal('100.0000'),
            unit_price=Decimal('50.00')
        )
        # Primer acceso calcula y puebla el caché
        metrics = item.calculated_metrics
        self.assertIn('calculated_metrics', item.__dict__)
        self.assertIs(item.calculated_metrics, metrics)
        # Acceso sucesivo a propiedades no recrea el diccionario
        _ = item.estimated_cost
        _ = item.cost_usd
        _ = item.cost_per_m2_usd
        self.assertIs(item.calculated_metrics, metrics)


class BudgetItemAPITestCase(APITestCase):
    """Pruebas funcionales de los endpoints de BudgetItemViewSet."""

    def setUp(self):
        self.project = Project.objects.create(
            name="Residencial Magnolia",
            built_area=Decimal('150.00'),
            exchange_rate=Decimal('6.9700')
        )
        self.stage = ConstructionStage.objects.create(name="Obra Bruta", order=1)
        self.cat_mat, _ = Category.objects.get_or_create(
            code="materials",
            defaults={"name": "Materiales", "is_active": True},
        )
        self.subcat_cemento = Subcategory.objects.create(category=self.cat_mat, name="Cementos")
        self.subcat_acero = Subcategory.objects.create(category=self.cat_mat, name="Aceros")

        self.uom_bolsa = UnitOfMeasure.objects.create(name="Bolsa 50kg", abbreviation="bolsa")
        self.pu_bolsa = PurchaseUnit.objects.create(name="Bolsa", abbreviation="bolsa")

        self.supplier = Supplier.objects.create(
            name="Itacamba Cemento",
            supplier_type=SupplierType.MATERIAL
        )

        self.item = BudgetItem.objects.create(
            project=self.project,
            stage=self.stage,
            category_type=BudgetCategoryType.MATERIALS,
            subcategory=self.subcat_cemento,
            supplier=self.supplier,
            name="Cemento Estructural IP-40",
            unit_measure=self.uom_bolsa,
            unit_purchase=self.pu_bolsa,
            conversion_factor=Decimal('1.0000'),
            quantity_obra=Decimal('50.0000'),
            unit_price=Decimal('52.00'),
            apply_ceil=True
        )

    def test_list_budget_items_and_filter_stage(self):
        response = self.client.get(f'/api/core/budget-items/?project={self.project.id}&stage={self.stage.id}&paginate=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Cemento Estructural IP-40")
        self.assertEqual(response.data[0]['stage_name'], "Obra Bruta")
        self.assertEqual(response.data[0]['supplier_name'], "Itacamba Cemento")

    def test_reassign_subcategory_dynamically(self):
        # UC-005: Reasignación de subcategoría mediante edición directa
        payload = {"subcategory": self.subcat_acero.id}
        response = self.client.patch(f'/api/core/budget-items/{self.item.id}/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.subcategory_id, self.subcat_acero.id)

    def test_grouped_by_project_accordion_endpoint(self):
        # Endpoint consumido por la vista acordeón
        response = self.client.get(f'/api/core/budget-items/by-project/?project={self.project.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        group = response.data[0]
        self.assertEqual(group['subcategory_name'], "Cementos")
        self.assertEqual(Decimal(group['subtotal_cost_bs']), Decimal('2600.00'))
        self.assertIn("50 Bolsa", group['total_purchase_units_summary'])

    def test_summary_endpoint(self):
        response = self.client.get(f'/api/core/budget-items/summary/?project={self.project.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['total_budget_bs']), Decimal('2600.00'))
        self.assertEqual(response.data['materials']['items_count'], 1)

    def test_from_catalog_materials_and_supplier_photo_url(self):
        from materials.models import MaterialCatalogItem
        cat_item = MaterialCatalogItem.objects.create(
            subcategory=self.subcat_cemento,
            supplier=self.supplier,
            name="Cemento Camba IP-30",
            description="Bolsa de 50kg resistente a sulfatos",
            unit_measure=self.uom_bolsa,
            unit_purchase=self.pu_bolsa,
            conversion_factor=Decimal('1.0000'),
            waste_pct=Decimal('0.0500'),
            price_per_purchase_unit=Decimal('50.00')
        )
        # Verificar serialización del catálogo con proveedor adjunto (supplier_photo_url)
        cat_resp = self.client.get(f'/api/materials/catalog/{cat_item.id}/')
        self.assertEqual(cat_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(cat_resp.data['supplier_name'], "Itacamba Cemento")
        self.assertIsNone(cat_resp.data['supplier_photo_url'])

        # Instanciar en BudgetItem unificado desde catálogo de materiales
        payload = {
            "project": self.project.id,
            "catalog_type": "materials",
            "catalog_id": cat_item.id,
            "stage": self.stage.id,
            "quantity_obra": "20.0000",
            "apply_ceil": True
        }
        resp = self.client.post('/api/core/budget-items/from-catalog/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], "Cemento Camba IP-30")
        self.assertEqual(resp.data['detail'], "Bolsa de 50kg resistente a sulfatos")
        # 20 * 1.05 = 21 bolsas * 50 Bs = 1050.00 Bs
        self.assertEqual(Decimal(resp.data['quantity_purchase']), Decimal('21.0000'))
        self.assertEqual(Decimal(resp.data['estimated_cost']), Decimal('1050.00'))

    def test_budget_grouped_by_stage_endpoint(self):
        """Verifica el endpoint jerárquico by-stage (Etapas -> Subcategorías -> Partidas)."""
        response = self.client.get(f'/api/core/budget-items/by-stage/?project={self.project.id}&category_type=materials')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

        stage_group = response.data[0]
        self.assertEqual(stage_group['stage_id'], self.stage.id)
        self.assertEqual(stage_group['stage_name'], "Obra Bruta")
        self.assertIn('%', stage_group['percentage_of_family'])
        self.assertIn('cost_per_m2_usd', stage_group)
        self.assertIn('subcategories', stage_group)
        self.assertGreaterEqual(len(stage_group['subcategories']), 1)

        sub_group = stage_group['subcategories'][0]
        self.assertEqual(sub_group['subcategory_name'], "Cementos")
        self.assertGreaterEqual(len(sub_group['items']), 1)


class CustomExceptionHandlerTests(TestCase):
    """Pruebas unitarias para el manejador global de excepciones (core.exceptions)."""

    def setUp(self):
        self.client = APIClient()
        self.cat, _ = Category.objects.get_or_create(
            code="labor",
            defaults={"name": "Mano de Obra", "is_active": True},
        )
        self.sub = Subcategory.objects.create(name="Prueba Sub", category=self.cat)
        self.uom = UnitOfMeasure.objects.create(name="Metro", abbreviation="m")

    def test_protected_error_returns_clean_400_json(self):
        """Si un registro tiene dependencias protegidas, responde 400 JSON sin fugar datos del sistema."""
        from labor.models import LaborCatalogItem
        LaborCatalogItem.objects.create(
            subcategory=self.sub,
            name="Tarea Dependiente",
            unit=self.uom,
            suggested_cost=Decimal('50.00')
        )
        resp = self.client.delete(f'/api/core/subcategories/{self.sub.id}/')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data['code'], 'protected_dependency_error')
        self.assertIn('No se puede eliminar este registro porque actualmente está en uso', resp.data['detail'])
        self.assertEqual(resp.data['count'], 1)

    def test_unhandled_exception_returns_clean_500_json(self):
        """Cualquier excepción inesperada responde 500 JSON estético sin stacktrace."""
        from core.exceptions import custom_exception_handler
        resp = custom_exception_handler(Exception("Crash inesperado"), {'view': None})
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.data['code'], 'internal_server_error')
        self.assertIn('Ha ocurrido un error inesperado', resp.data['detail'])






