from django.urls import path, include
from rest_framework.routers import DefaultRouter
from labor.api.labor_catalog_viewset import LaborCatalogItemViewSet

router = DefaultRouter()
router.register(r'catalog', LaborCatalogItemViewSet, basename='labor-catalog')

urlpatterns = [
    path('', include(router.urls)),
]
