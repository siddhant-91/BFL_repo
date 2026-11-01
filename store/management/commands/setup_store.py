from django.core.management.base import BaseCommand
from store.models import Category

class Command(BaseCommand):
    help = "Create BFL's starter product categories. Safe to run more than once."
    def handle(self, *args, **options):
        names = ["T-shirts", "Shirts", "Sweatshirts", "Jackets", "Jeans", "Accessories"]
        for position, name in enumerate(names, start=1):
            Category.objects.get_or_create(name=name, defaults={"order": position})
        self.stdout.write(self.style.SUCCESS("BFL starter categories are ready."))
