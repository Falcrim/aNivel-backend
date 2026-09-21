"""
================================================================================
RUTAS API - MÓDULO INVENTARIO (Herramientas, Maquinaria, Locaciones y Traslados)
================================================================================

1. LOCACIONES (Almacenes, Depósitos y Frentes de Obra):
   - LIST / CREATE:            GET / POST   http://127.0.0.1:8000/api/inventory/locations/
   - DETAIL / EDIT / DELETE:   GET / PUT / PATCH / DELETE http://127.0.0.1:8000/api/inventory/locations/{id}/
   - Filtrar por Tipo:         GET          http://127.0.0.1:8000/api/inventory/locations/?location_type=WAREHOUSE
   - Filtrar por Obra:         GET          http://127.0.0.1:8000/api/inventory/locations/?project=1
   - Búsqueda por Nombre/Cód:  GET          http://127.0.0.1:8000/api/inventory/locations/?search=central

2. CATEGORÍAS DE HERRAMIENTAS:
   - LIST / CREATE:            GET / POST   http://127.0.0.1:8000/api/inventory/categories/
   - DETAIL / EDIT / DELETE:   GET / PUT / PATCH / DELETE http://127.0.0.1:8000/api/inventory/categories/{id}/

3. INVENTARIO DE HERRAMIENTAS Y MAQUINARIA:
   - LIST / CREATE:            GET / POST   http://127.0.0.1:8000/api/inventory/tools/
   - DETAIL / EDIT / DELETE:   GET / PUT / PATCH / DELETE http://127.0.0.1:8000/api/inventory/tools/{id}/
   - Filtrar por Locación:     GET          http://127.0.0.1:8000/api/inventory/tools/?location=1
   - Filtrar por Obra:         GET          http://127.0.0.1:8000/api/inventory/tools/?project=1
   - Filtrar por Estado:       GET          http://127.0.0.1:8000/api/inventory/tools/?status=AVAILABLE
   - Filtrar por Categoría:    GET          http://127.0.0.1:8000/api/inventory/tools/?category=1
   - Historial de Traslados:   GET          http://127.0.0.1:8000/api/inventory/tools/{id}/history/

4. TRASLADOS Y MOVIMIENTOS:
   - LIST (Historial Global):  GET          http://127.0.0.1:8000/api/inventory/transfers/
   - REGISTRAR TRASLADO:       POST         http://127.0.0.1:8000/api/inventory/transfers/
     Body (JSON):
     {
       "tool_id": 1,
       "destination_location_id": 2,
       "responsible_person": "Ing. Marcelo Rios",
       "notes": "Asignada a fase de excavación"
     }
================================================================================
"""

from rest_framework.routers import DefaultRouter
from inventory.api.location_viewset import LocationViewSet
from inventory.api.tool_category_viewset import ToolCategoryViewSet
from inventory.api.tool_viewset import ToolViewSet
from inventory.api.tool_transfer_viewset import ToolTransferViewSet

router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='inventory-locations')
router.register(r'categories', ToolCategoryViewSet, basename='inventory-categories')
router.register(r'tools', ToolViewSet, basename='inventory-tools')
router.register(r'transfers', ToolTransferViewSet, basename='inventory-transfers')

urlpatterns = router.urls
