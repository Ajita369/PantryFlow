from rest_framework.routers import DefaultRouter

from .views import PantryItemViewSet

router = DefaultRouter()
router.register('pantry-items', PantryItemViewSet, basename='pantry-item')

urlpatterns = router.urls
