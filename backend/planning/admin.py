from django.contrib import admin

from .models import ShoppingListItem, WeeklyBudget


@admin.register(WeeklyBudget)
class WeeklyBudgetAdmin(admin.ModelAdmin):
	list_display = ('weekly_budget_amount', 'currency', 'week_start_date', 'week_end_date')
	list_filter = ('currency',)


@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(admin.ModelAdmin):
	list_display = ('name', 'estimated_price', 'quantity', 'priority', 'is_needed')
	list_filter = ('priority', 'is_needed')
	search_fields = ('name', 'reason')
