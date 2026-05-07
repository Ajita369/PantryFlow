from django.contrib import admin

from .models import PantryItem


@admin.register(PantryItem)
class PantryItemAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'quantity', 'unit', 'expiry_date', 'location')
	search_fields = ('name', 'category', 'location')
	list_filter = ('category', 'location')
