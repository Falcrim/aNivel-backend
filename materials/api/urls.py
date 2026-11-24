from rest_framework.routers import DefaultRouter
from materials.api import MaterialCatalogItemViewSet

router = DefaultRouter()
router.register(r'catalog', MaterialCatalogItemViewSet, basename='material-catalog')

urlpatterns = router.urls
