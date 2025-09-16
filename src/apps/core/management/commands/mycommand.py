from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "My custom command"

    def handle(self, *args, **options):
        print("Hello, this is my custom command!")
