import os
from decimal import Decimal
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from core.models import (
    Project,
    Category,
    Subcategory,
    UnitOfMeasure,
    PurchaseUnit,
    ProjectDocument,
    DocumentType,
    ProjectExpense,
    ExpenseCategoryType,
    PaymentStatus,
)


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


class ProjectDocumentAPITestCase(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Condominio El Prado")
        self.category = Category.objects.create(name="Materiales")
        self.subcat = Subcategory.objects.create(category=self.category, name="Acero y Fierro")

    def test_upload_project_document(self):
        dummy_pdf = SimpleUploadedFile(
            "cotizacion_fierro.pdf",
            b"%PDF-1.4 dummy pdf content for testing",
            content_type="application/pdf"
        )
        payload = {
            "project": self.project.id,
            "title": "Cotización Fierro Las Lomas",
            "document_type": DocumentType.QUOTATION,
            "file": dummy_pdf,
            "supplier_name": "Las Lomas SRL",
            "quoted_amount": "12500.50",
            "currency": "BOB",
            "subcategory": self.subcat.id,
            "notes": "Válida hasta fin de mes",
        }
        response = self.client.post('/api/core/project-documents/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "Cotización Fierro Las Lomas")
        self.assertEqual(response.data['supplier_name'], "Las Lomas SRL")
        self.assertEqual(response.data['file_extension'], "pdf")
        self.assertTrue(response.data['file_url'].endswith('.pdf'))

        doc_id = response.data['id']
        doc = ProjectDocument.objects.get(id=doc_id)
        self.assertTrue(os.path.exists(doc.file.path))

        file_path = doc.file.path
        del_resp = self.client.delete(f'/api/core/project-documents/{doc_id}/')
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(os.path.exists(file_path))

    def test_reject_invalid_file_extension(self):
        dummy_exe = SimpleUploadedFile(
            "malicious.exe",
            b"fake executable binary",
            content_type="application/octet-stream"
        )
        payload = {
            "project": self.project.id,
            "title": "Archivo Malicioso",
            "file": dummy_exe,
        }
        response = self.client.post('/api/core/project-documents/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_documents_summary_endpoint(self):
        dummy_pdf1 = SimpleUploadedFile("quote1.pdf", b"pdf content 1", content_type="application/pdf")
        dummy_pdf2 = SimpleUploadedFile("quote2.pdf", b"pdf content 2", content_type="application/pdf")

        ProjectDocument.objects.create(
            project=self.project,
            title="Cotización 1",
            document_type=DocumentType.QUOTATION,
            file=dummy_pdf1,
            file_name="quote1.pdf",
            file_size=100,
            file_extension="pdf",
            quoted_amount=Decimal('5000.00'),
            currency='BOB'
        )
        ProjectDocument.objects.create(
            project=self.project,
            title="Ficha Técnica 1",
            document_type=DocumentType.TECHNICAL_SHEET,
            file=dummy_pdf2,
            file_name="quote2.pdf",
            file_size=200,
            file_extension="pdf",
            quoted_amount=Decimal('800.00'),
            currency='USD'
        )

        response = self.client.get(f'/api/core/project-documents/summary/?project={self.project.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_documents'], 2)
        self.assertEqual(response.data['quotations_count'], 1)
        self.assertEqual(response.data['technical_sheets_count'], 1)
        self.assertEqual(response.data['total_quoted_bob'], 5000.0)
        self.assertEqual(response.data['total_quoted_usd'], 800.0)


class ProjectExpenseAPITestCase(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Complejo Habitacional Olivos")
        self.category = Category.objects.create(name="Materiales")
        self.subcat = Subcategory.objects.create(category=self.category, name="Acero Corrugado")

    def test_create_expense_with_receipt(self):
        dummy_receipt = SimpleUploadedFile(
            "factura_120.pdf",
            b"%PDF-1.4 factura content",
            content_type="application/pdf"
        )
        payload = {
            "project": self.project.id,
            "category_type": ExpenseCategoryType.MATERIALS,
            "subcategory": self.subcat.id,
            "item_name": 'Barra de acero corrugado 3/8"x12m. (10mm²)',
            "unit_name": "Barra",
            "quantity": "220.00",
            "unit_price": "55.00",
            "payment_status": PaymentStatus.PAID,
            "expense_date": "2026-06-24",
            "payment_method": "AL CONTADO",
            "details": "Comprado en Ferretería Central",
            "rendicion_number": "Nr° 04",
            "receipt_number": "FAC-8891",
            "receipt_file": dummy_receipt,
        }
        response = self.client.post('/api/core/project-expenses/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(str(response.data['total_price'])), Decimal('12100.00'))
        self.assertEqual(response.data['rendicion_number'], "Nr° 04")
        self.assertTrue(response.data['receipt_file_url'].endswith('.pdf'))

        expense_id = response.data['id']
        expense = ProjectExpense.objects.get(id=expense_id)
        self.assertTrue(os.path.exists(expense.receipt_file.path))

        # Check delete cleans up receipt
        file_path = expense.receipt_file.path
        del_resp = self.client.delete(f'/api/core/project-expenses/{expense_id}/')
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(os.path.exists(file_path))

    def test_expenses_summary_endpoint(self):
        ProjectExpense.objects.create(
            project=self.project,
            category_type=ExpenseCategoryType.MATERIALS,
            subcategory=self.subcat,
            item_name="Fierro 1/2",
            unit_name="Barra",
            quantity=Decimal('38.00'),
            unit_price=Decimal('93.00'),
            total_price=Decimal('3534.00'),
            payment_status=PaymentStatus.PAID,
            expense_date="2026-06-24",
            rendicion_number="Nr° 04"
        )
        ProjectExpense.objects.create(
            project=self.project,
            category_type=ExpenseCategoryType.LABOR,
            item_name="Estructura Hormigón Armado",
            unit_name="Gbl",
            quantity=Decimal('1.00'),
            unit_price=Decimal('40000.00'),
            total_price=Decimal('40000.00'),
            payment_status=PaymentStatus.PAID,
            expense_date="2026-07-04",
            rendicion_number="Nr° 04"
        )
        ProjectExpense.objects.create(
            project=self.project,
            category_type=ExpenseCategoryType.OPERATING,
            item_name="Transporte de material",
            unit_name="Gbl",
            quantity=Decimal('1.00'),
            unit_price=Decimal('1500.00'),
            total_price=Decimal('1500.00'),
            payment_status=PaymentStatus.IN_PROCESS,
            expense_date="2026-07-10",
            rendicion_number="Nr° 04"
        )

        response = self.client.get(f'/api/core/project-expenses/summary/?project={self.project.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 3)
        self.assertEqual(response.data['total_amount'], 45034.0)
        self.assertEqual(response.data['paid_amount'], 43534.0)
        self.assertEqual(response.data['in_process_amount'], 1500.0)
        self.assertEqual(response.data['materials_amount'], 3534.0)
        self.assertEqual(response.data['labor_amount'], 40000.0)
        self.assertEqual(response.data['operating_amount'], 1500.0)
        self.assertIn("Nr° 04", response.data['rendiciones'])
