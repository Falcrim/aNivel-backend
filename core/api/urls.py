from rest_framework.routers import DefaultRouter

from core.api import ProjectViewSet, CategoryViewSet, SubcategoryViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'subcategories', SubcategoryViewSet, basename='subcategory')

urlpatterns = router.urls