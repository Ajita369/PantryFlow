from django.urls import path

from .views import dashboard, health

urlpatterns = [
    path('health/', health, name='health'),
    path('dashboard/', dashboard, name='dashboard'),
]
