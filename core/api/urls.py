from rest_framework.routers import DefaultRouter
from core.api import (
    ProjectViewSet,
    CategoryViewSet,
    SubcategoryViewSet,
    UnitOfMeasureViewSet,
    PurchaseUnitViewSet,
    SupplierViewSet,
    ConstructionStageViewSet,
    BudgetItemViewSet,
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'subcategories', SubcategoryViewSet, basename='subcategory')
router.register(r'units-of-measure', UnitOfMeasureViewSet, basename='unit-of-measure')
router.register(r'purchase-units', PurchaseUnitViewSet, basename='purchase-unit')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'stages', ConstructionStageViewSet, basename='stage')
router.register(r'budget-items', BudgetItemViewSet, basename='budget-item')

urlpatterns = router.urls
