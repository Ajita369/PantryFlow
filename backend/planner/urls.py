from django.urls import path

from .views import plan_week

urlpatterns = [
    path('plan-week/', plan_week, name='plan-week'),
]
