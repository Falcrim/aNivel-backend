"""
================================================================================
RUTAS API - MÓDULO CORE
================================================================================

COPIAR Y PEGAR EN POSTMAN:

1. PROYECTOS / OBRAS:
   - LIST / CREATE:  GET / POST   http://127.0.0.1:8000/api/core/projects/
   - DETAIL / EDIT:  GET / PUT / PATCH / DELETE http://127.0.0.1:8000/api/core/projects/{id}/
   - Búsqueda:       GET          http://127.0.0.1:8000/api/core/projects/?search=Palmas

2. CATEGORÍAS (Materiales, Mano de Obra, Gastos Generales, etc.):
   - LIST / CREATE:  GET / POST   http://127.0.0.1:8000/api/core/categories/
   - DETAIL / EDIT:  GET / PUT / PATCH / DELETE http://127.0.0.1:8000/api/core/categories/{id}/
   - Subcategorías:  GET          http://127.0.0.1:8000/api/core/categories/{id}/subcategories/

3. SUBCATEGORÍAS (Fierros, Cementos, Pinturas, etc.):
   - LIST / CREATE:  GET / POST   http://127.0.0.1:8000/api/core/subcategories/
   - DETAIL / EDIT:  GET / PUT / PATCH / DELETE http://127.0.0.1:8000/api/core/subcategories/{id}/
   - Filtrar por categoría: GET   http://127.0.0.1:8000/api/core/subcategories/?category=1
   - Búsqueda:       GET          http://127.0.0.1:8000/api/core/subcategories/?search=fierro

4. UNIDADES DE MEDIDA (ml, m2, m3, kg, pza):
   - LIST / CREATE:  GET / POST   http://127.0.0.1:8000/api/core/units-of-measure/
   - DETAIL / EDIT:  GET / PUT / PATCH / DELETE http://127.0.0.1:8000/api/core/units-of-measure/{id}/
   - Búsqueda:       GET          http://127.0.0.1:8000/api/core/units-of-measure/?search=ml

5. UNIDADES DE COMPRA COMERCIAL (barra, bolsa, tubo, balde, Gbl):
   - LIST / CREATE:  GET / POST   http://127.0.0.1:8000/api/core/purchase-units/
   - DETAIL / EDIT:  GET / PUT / PATCH / DELETE http://127.0.0.1:8000/api/core/purchase-units/{id}/
   - Búsqueda:       GET          http://127.0.0.1:8000/api/core/purchase-units/?search=barra
================================================================================
"""

from rest_framework.routers import DefaultRouter
from core.api import (
    ProjectViewSet,
    CategoryViewSet,
    SubcategoryViewSet,
    UnitOfMeasureViewSet,
    PurchaseUnitViewSet,
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'subcategories', SubcategoryViewSet, basename='subcategory')
router.register(r'units-of-measure', UnitOfMeasureViewSet, basename='unit-of-measure')
router.register(r'purchase-units', PurchaseUnitViewSet, basename='purchase-unit')

urlpatterns = router.urls