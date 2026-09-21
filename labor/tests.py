from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status

from core.models import Project, ProjectStatus, Category, Subcategory, UnitOfMeasure
from labor.models import LaborCatalogItem, LaborBudgetItem
from labor.services import LaborBudgetService, LaborBudgetMetricsService


class LaborModelAndServiceTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Mano de Obra')
        self.subcategory = Subcategory.objects.create(category=self.category, name='Obra Gris')
        self.unit_m2 = UnitOfMeasure.objects.create(name='Metro Cuadrado', abbreviation='m2')

        self.project = Project.objects.create(
            name='Proyecto Zabalaga',
            status=ProjectStatus.ACTIVE,
            built_area=Decimal('229.50'),
            exchange_rate=Decimal('6.9700')
        )

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

    def test_budget_item_from_catalog(self):
        item = LaborBudgetService.create_from_catalog(
            project=self.project,
            catalog_item=self.catalog_item,
            quantity=Decimal('260.00'),
            contractor_name='Contratista Obra Gris'
        )
        self.assertEqual(item.quantity, Decimal('260.00'))
        self.assertEqual(item.unit_cost, Decimal('25.00'))
        self.assertEqual(item.estimated_cost, Decimal('6500.00'))
        self.assertEqual(item.contractor_name, 'Contratista Obra Gris')

    def test_budget_item_custom(self):
        item = LaborBudgetService.create_custom_item(
            project=self.project,
            subcategory=self.subcategory,
            name='Trabajo Especial Refuerzo',
            unit=self.unit_m2,
            quantity=Decimal('10.00'),
            unit_cost=Decimal('150.00'),
            contractor_name='Especialista'
        )
        self.assertEqual(item.estimated_cost, Decimal('1500.00'))
        self.assertIsNone(item.catalog_item)

    def test_validation_rejects_negative_values(self):
        item = LaborBudgetItem(
            project=self.project,
            subcategory=self.subcategory,
            name='Tarea Invalida',
            unit=self.unit_m2,
            quantity=Decimal('-5.00'),
            unit_cost=Decimal('10.00')
        )
        with self.assertRaises(ValidationError):
            item.clean()

    def test_metrics_service_calculations(self):
        # Crear 2 items
        LaborBudgetService.create_from_catalog(
            project=self.project,
            catalog_item=self.catalog_item,
            quantity=Decimal('260.00'), # 260 * 25 = 6500 Bs
        )
        LaborBudgetService.create_custom_item(
            project=self.project,
            subcategory=self.subcategory,
            name='Revoque',
            unit=self.unit_m2,
            quantity=Decimal('100.00'),
            unit_cost=Decimal('35.00'), # 100 * 35 = 3500 Bs
        )
        # Total Bs: 10,000.00 Bs
        # Exchange rate: 6.97 -> Total USD: 10000 / 6.97 = 1434.72 USD
        # Built area: 229.50 -> Cost per m2 USD: 1434.72 / 229.50 = 6.25 USD/m2
        summary = LaborBudgetMetricsService.get_project_budget_summary(self.project.id)
        self.assertEqual(summary['total_labor_cost_bs'], Decimal('10000.00'))
        self.assertEqual(summary['total_labor_cost_usd'], Decimal('1434.72'))
        self.assertEqual(summary['cost_per_m2_usd'], Decimal('6.25'))
        self.assertEqual(summary['total_items'], 2)
        self.assertEqual(summary['from_catalog_count'], 1)
        self.assertEqual(summary['custom_items_count'], 1)

        grouped = LaborBudgetMetricsService.get_project_budget_grouped_by_subcategory(self.project.id)
        self.assertEqual(len(grouped['groups']), 1)
        self.assertEqual(grouped['groups'][0]['subtotal_cost_bs'], Decimal('10000.00'))
        self.assertEqual(grouped['groups'][0]['subtotal_cost_usd'], Decimal('1434.72'))


class LaborAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Mano de Obra')
        self.subcategory = Subcategory.objects.create(category=self.category, name='Obra Gris')
        self.unit_m2 = UnitOfMeasure.objects.create(name='Metro Cuadrado', abbreviation='m2')

        self.project = Project.objects.create(
            name='Proyecto Zabalaga',
            status=ProjectStatus.ACTIVE,
            built_area=Decimal('229.50'),
            exchange_rate=Decimal('6.9700')
        )

        self.catalog_item = LaborCatalogItem.objects.create(
            subcategory=self.subcategory,
            name='Muro de Ladrillo cerámico e=10',
            unit=self.unit_m2,
            suggested_cost=Decimal('25.00'),
            contractor_type='Albañilería'
        )

    def test_post_from_catalog(self):
        url = '/api/labor/budget/from-catalog/'
        data = {
            'project': self.project.id,
            'catalog_item': self.catalog_item.id,
            'quantity': '260.0000',
            'contractor_name': 'Contratista Albañil',
            'detail': 'Todos arrancan desde vigas'
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Muro de Ladrillo cerámico e=10')
        self.assertEqual(Decimal(res.data['estimated_cost']), Decimal('6500.00'))

    def test_post_custom_item(self):
        url = '/api/labor/budget/custom/'
        data = {
            'project': self.project.id,
            'subcategory': self.subcategory.id,
            'name': 'Pintura Fachada',
            'unit': self.unit_m2.id,
            'quantity': '50.0000',
            'unit_cost': '40.00',
            'contractor_name': 'Pintor Especializado'
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(res.data['estimated_cost']), Decimal('2000.00'))

    def test_by_project_and_summary_endpoints(self):
        LaborBudgetService.create_from_catalog(
            project=self.project,
            catalog_item=self.catalog_item,
            quantity=Decimal('100.00')
        )

        summary_url = f'/api/labor/budget/summary/?project_id={self.project.id}'
        res_sum = self.client.get(summary_url)
        self.assertEqual(res_sum.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(res_sum.data['total_labor_cost_bs']), Decimal('2500.00'))

        by_proj_url = f'/api/labor/budget/by-project/?project_id={self.project.id}'
        res_proj = self.client.get(by_proj_url)
        self.assertEqual(res_proj.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_proj.data['groups']), 1)
