"""
================================================================================
RUTAS API - MÓDULO MATERIALS
================================================================================

COPIAR Y PEGAR EN POSTMAN:

1. CATÁLOGO MAESTRO DE MATERIALES (Inventario Global):
   - LIST / CREATE:            GET / POST   http://127.0.0.1:8000/api/materials/catalog/
   - DETAIL / EDIT / DELETE:   GET / PUT / PATCH / DELETE http://127.0.0.1:8000/api/materials/catalog/{id}/
   - Filtrar por Subcategoría: GET          http://127.0.0.1:8000/api/materials/catalog/?subcategory=1
   - Filtrar solo Activos:     GET          http://127.0.0.1:8000/api/materials/catalog/?is_active=true
   - Búsqueda por Nombre:      GET          http://127.0.0.1:8000/api/materials/catalog/?search=fierro
   - Agrupado por Subcategoría:GET          http://127.0.0.1:8000/api/materials/catalog/grouped-by-subcategory/

2. PRESUPUESTO DE MATERIALES POR OBRA (BudgetItem / Snapshots):
   - LIST (todos):             GET          http://127.0.0.1:8000/api/materials/budget/
   - Filtrar por Proyecto:     GET          http://127.0.0.1:8000/api/materials/budget/?project=1
   - Filtrar por Subcategoría: GET          http://127.0.0.1:8000/api/materials/budget/?project=1&subcategory=2
   - DETAIL / EDIT / DELETE:   GET / PUT / PATCH / DELETE http://127.0.0.1:8000/api/materials/budget/{id}/

3. ENDPOINTS ESPECIALES DE CREACIÓN EN PRESUPUESTO:
   - Crear NORMAL desde Catálogo:
     POST http://127.0.0.1:8000/api/materials/budget/from-catalog/
     Body (JSON):
     {
       "project": 1,
       "catalog_item": 1,
       "quantity_obra": 100.00,
       "detail": "Fierro para vigas principales",
       "waste_pct": 0.10,
       "price_override": 55.00
     }

   - Crear GLOBAL desde Catálogo (Paquete cerrado / Compra preventiva):
     POST http://127.0.0.1:8000/api/materials/budget/from-catalog-global/
     Body (JSON):
     {
       "project": 1,
       "catalog_item": 2,
       "quantity_purchase": 1.00,
       "price_per_purchase_unit": 800.00,
       "detail": "Paquete de brochas y rodillos"
     }

   - Crear ÍTEM PERSONALIZADO / AD-HOC (Sin catálogo):
     POST http://127.0.0.1:8000/api/materials/budget/custom/
     Body (JSON):
     {
       "project": 1,
       "subcategory": 1,
       "name": "Aditivo Impermeabilizante Especial",
       "unit_measure": 1,
       "unit_purchase": 2,
       "price_per_purchase_unit": 120.00,
       "is_global": false,
       "quantity_obra": 50.00,
       "conversion_factor": 5.00,
       "waste_pct": 0.05,
       "detail": "Importado para foso de ascensor"
     }

4. REPORTES Y VISTAS PARA FRONTEND (Por Proyecto):
   - Presupuesto Agrupado con Subtotales por Subcategoría:
     GET http://127.0.0.1:8000/api/materials/budget/by-project/?project_id=1

   - Resumen y Métricas Clave de la Obra (Totales, Peso, Cantidades):
     GET http://127.0.0.1:8000/api/materials/budget/summary/?project_id=1
================================================================================
"""

from rest_framework.routers import DefaultRouter
from materials.api import MaterialCatalogItemViewSet, MaterialBudgetItemViewSet

router = DefaultRouter()
router.register(r'catalog', MaterialCatalogItemViewSet, basename='material-catalog')
router.register(r'budget', MaterialBudgetItemViewSet, basename='material-budget')

urlpatterns = router.urls
