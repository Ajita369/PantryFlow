from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BudgetView, ShoppingListViewSet

router = DefaultRouter()
router.register('shopping-list', ShoppingListViewSet, basename='shopping-list')

urlpatterns = [
    path('budget/', BudgetView.as_view(), name='budget'),
]

urlpatterns += router.urls
