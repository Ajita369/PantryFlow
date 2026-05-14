from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BudgetView, ShoppingListViewSet, export_shopping_list

router = DefaultRouter()
router.register('shopping-list', ShoppingListViewSet, basename='shopping-list')

urlpatterns = [
    path('budget/', BudgetView.as_view(), name='budget'),
    path('shopping-list/export/', export_shopping_list, name='shopping-list-export'),
]

urlpatterns += router.urls
