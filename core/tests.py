from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from core.models import Project, Category, Subcategory, UnitOfMeasure, PurchaseUnit


class CoreModelsTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Materiales")
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

    def test_subcategories_filtering(self):
        response = self.client.get(f'/api/core/subcategories/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
