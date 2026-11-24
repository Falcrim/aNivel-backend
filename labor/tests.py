from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from core.models import Category, Subcategory, UnitOfMeasure, Supplier, SupplierType
from labor.models import LaborCatalogItem


class LaborCatalogModelTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Mano de Obra')
        self.subcategory = Subcategory.objects.create(category=self.category, name='Obra Gris')
        self.unit_m2 = UnitOfMeasure.objects.create(name='Metro Cuadrado', abbreviation='m2')

        self.catalog_item = LaborCatalogItem.objects.create(
            subcategory=self.subcategory,
            name='Muro de Ladrillo cerámico e=10',
            detail='soga o pandereta',
            unit=self.unit_m2,
            suggested_cost=Decimal('25.00'),
            contractor_type='Albañilería',
            is_active=True
        )

    def test_catalog_item_creation(self):
        self.assertEqual(str(self.catalog_item), "Muro de Ladrillo cerámico e=10 (m2 - Bs 25.00)")


class LaborCatalogSupplierTestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Mano de Obra')
        self.subcat = Subcategory.objects.create(category=self.category, name='Instalaciones')
        self.unit = UnitOfMeasure.objects.create(name='Punto', abbreviation='pto')
        self.contractor = Supplier.objects.create(
            name="Cuadrilla Electricistas Sánchez",
            supplier_type=SupplierType.LABOR,
            phone="78811223"
        )

    def test_create_labor_catalog_with_supplier(self):
        payload = {
            "subcategory": self.subcat.id,
            "supplier": self.contractor.id,
            "name": "Punto de iluminación LED",
            "detail": "Incluye cableado y caja",
            "unit": self.unit.id,
            "suggested_cost": "60.00",
            "contractor_type": "Electricidad"
        }
        res = self.client.post('/api/labor/catalog/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['supplier'], self.contractor.id)

        # Filtrar por contratista
        list_res = self.client.get(f'/api/labor/catalog/?supplier={self.contractor.id}&paginate=false')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)
        self.assertEqual(list_res.data[0]['supplier_name'], "Cuadrilla Electricistas Sánchez")
        self.assertEqual(list_res.data[0]['supplier_phone'], "78811223")

    def test_labor_catalog_grouped_by_subcategory(self):
        LaborCatalogItem.objects.create(
            subcategory=self.subcat,
            supplier=self.contractor,
            name="Punto de tomacorriente",
            detail="Punto simple",
            unit=self.unit,
            suggested_cost=Decimal('45.00'),
            contractor_type="Electricidad"
        )
        res = self.client.get('/api/labor/catalog/grouped-by-subcategory/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data, list)
        self.assertGreaterEqual(len(res.data), 1)
        group = next((g for g in res.data if g['subcategory_id'] == self.subcat.id), None)
        self.assertIsNotNone(group)
        self.assertEqual(group['subcategory_name'], "Instalaciones")
        self.assertEqual(group['items_count'], 1)
        self.assertEqual(len(group['items']), 1)
