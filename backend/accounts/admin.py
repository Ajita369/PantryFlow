from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'display_name', 'is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email', 'display_name', 'first_name', 'last_name')

    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('display_name',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('display_name',)}),
    )
