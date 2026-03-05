import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Load ingredients from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            type=str,
            help="Path to JSON file"
        )

    def handle(self, *args, **options):
        json_path = options["json_path"]

        with open(json_path, encoding="utf-8") as file:
            data = json.load(file)

        ingredients = [
            Ingredient(
                name=item["name"],
                measurement_unit=item["measurement_unit"]
            )
            for item in data
        ]

        Ingredient.objects.bulk_create(
            ingredients,
            ignore_conflicts=True
        )

        self.stdout.write(
            self.style.SUCCESS("Ingredients loaded successfully!")
        )
