from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status

from core.models import Category, Subcategory, UnitOfMeasure, PurchaseUnit, Supplier, SupplierType
from materials.models import MaterialCatalogItem


class MaterialCatalogSupplierTestCase(APITestCase):
    def setUp(self):
        self.category, _ = Category.objects.get_or_create(
            code="materials",
            defaults={"name": "Materiales", "is_active": True},
        )
        self.subcat = Subcategory.objects.create(category=self.category, name="Fierros")
        self.uom = UnitOfMeasure.objects.create(name="Metro lineal", abbreviation="ml")
        self.pu = PurchaseUnit.objects.create(name="Barra 12m", abbreviation="barra")
        self.supplier = Supplier.objects.create(name="Campero Aceros", supplier_type=SupplierType.MATERIAL)

    def test_create_catalog_item_with_supplier(self):
        payload = {
            "subcategory": self.subcat.id,
            "supplier": self.supplier.id,
            "name": "Fierro 1/2 Campero",
            "unit_measure": self.uom.id,
            "unit_purchase": self.pu.id,
            "conversion_factor": 12.0,
            "price_per_purchase_unit": 85.00,
            "waste_pct": 0.05,
        }
        response = self.client.post('/api/materials/catalog/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['supplier'], self.supplier.id)

        # Consultar catálogo con filtro de proveedor
        list_resp = self.client.get(f'/api/materials/catalog/?supplier={self.supplier.id}&paginate=false')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_resp.data), 1)
        self.assertEqual(list_resp.data[0]['supplier_name'], "Campero Aceros")

    def test_catalog_grouped_by_subcategory(self):
        MaterialCatalogItem.objects.create(
            subcategory=self.subcat,
            supplier=self.supplier,
            name="Fierro corrugado 8mm",
            unit_measure=self.uom,
            unit_purchase=self.pu,
            conversion_factor=Decimal('12.0000'),
            weight_per_purchase_unit=Decimal('4.7400'),
            waste_pct=Decimal('0.0500'),
            price_per_purchase_unit=Decimal('35.00'),
            is_active=True
        )
        response = self.client.get('/api/materials/catalog/grouped-by-subcategory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        group = response.data[0]
        self.assertIn('subcategory_name', group)
        self.assertIn('items', group)
