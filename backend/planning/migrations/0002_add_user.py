from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


DEFAULT_EMAIL = 'legacy@pantryflow.local'


def backfill_planning_user(apps, schema_editor):
    User = apps.get_model('accounts', 'CustomUser')
    WeeklyBudget = apps.get_model('planning', 'WeeklyBudget')
    ShoppingListItem = apps.get_model('planning', 'ShoppingListItem')

    # Only backfill if there is existing data without a user assigned.
    # On a fresh database this is a no-op and returns immediately.
    has_budget = WeeklyBudget.objects.filter(user__isnull=True).exists()
    has_shopping = ShoppingListItem.objects.filter(user__isnull=True).exists()

    if not has_budget and not has_shopping:
        return

    user, _ = User.objects.get_or_create(
        email=DEFAULT_EMAIL,
        defaults={
            'username': DEFAULT_EMAIL,
            'display_name': 'Legacy User',
            'first_name': 'Legacy',
            'is_active': True,
            # '!' is Django's unusable-password sentinel — avoids calling
            # set_unusable_password() which is not available on historical
            # model proxies used inside RunPython migrations.
            'password': '!',
        },
    )

    WeeklyBudget.objects.filter(user__isnull=True).update(user=user)
    ShoppingListItem.objects.filter(user__isnull=True).update(user=user)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('planning', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='weeklybudget',
            name='user',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='weekly_budgets',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='shoppinglistitem',
            name='user',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='shopping_list_items',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(backfill_planning_user, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='weeklybudget',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='weekly_budgets',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='shoppinglistitem',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='shopping_list_items',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
