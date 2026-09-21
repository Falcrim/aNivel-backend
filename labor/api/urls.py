from django.urls import path, include
from rest_framework.routers import DefaultRouter
from labor.api.labor_catalog_viewset import LaborCatalogItemViewSet
from labor.api.labor_budget_viewset import LaborBudgetItemViewSet

router = DefaultRouter()
router.register(r'catalog', LaborCatalogItemViewSet, basename='labor-catalog')
router.register(r'budget', LaborBudgetItemViewSet, basename='labor-budget')

urlpatterns = [
    path('', include(router.urls)),
]
