from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


DEFAULT_EMAIL = 'legacy@pantryflow.local'


def backfill_pantry_user(apps, schema_editor):
    User = apps.get_model('accounts', 'CustomUser')
    PantryItem = apps.get_model('pantry', 'PantryItem')

    # Only backfill if there is existing data without a user assigned.
    # On a fresh database this is a no-op and returns immediately.
    if not PantryItem.objects.filter(user__isnull=True).exists():
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

    PantryItem.objects.filter(user__isnull=True).update(user=user)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('pantry', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pantryitem',
            name='user',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pantry_items',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(backfill_pantry_user, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='pantryitem',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pantry_items',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
