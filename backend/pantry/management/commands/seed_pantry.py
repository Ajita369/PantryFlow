from datetime import date, timedelta

from django.core.management.base import BaseCommand

from pantry.models import PantryItem


class Command(BaseCommand):
    help = 'Seed the pantry with sample items for development.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Insert sample data even if items already exist.',
        )

    def handle(self, *args, **options):
        if PantryItem.objects.exists() and not options['force']:
            self.stdout.write('Pantry already has data. Use --force to reseed.')
            return

        PantryItem.objects.all().delete()

        today = date.today()
        samples = [
            PantryItem(
                name='Brown rice',
                category='Grains',
                quantity=2.5,
                unit='kg',
                expiry_date=today + timedelta(days=120),
                purchase_date=today - timedelta(days=7),
                notes='Open bag, store airtight.',
                location='Pantry',
            ),
            PantryItem(
                name='Spinach',
                category='Produce',
                quantity=1,
                unit='bunch',
                expiry_date=today + timedelta(days=2),
                purchase_date=today - timedelta(days=2),
                notes='Use for salads or saute.',
                location='Fridge',
            ),
            PantryItem(
                name='Greek yogurt',
                category='Dairy',
                quantity=2,
                unit='cups',
                expiry_date=today + timedelta(days=6),
                purchase_date=today - timedelta(days=1),
                notes='',
                location='Fridge',
            ),
            PantryItem(
                name='Canned chickpeas',
                category='Canned',
                quantity=3,
                unit='cans',
                expiry_date=None,
                purchase_date=today - timedelta(days=30),
                notes='Great for quick lunches.',
                location='Pantry',
            ),
        ]

        PantryItem.objects.bulk_create(samples)
        self.stdout.write('Seeded pantry with sample items.')
