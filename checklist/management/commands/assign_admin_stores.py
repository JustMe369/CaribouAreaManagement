from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from checklist.models import Store

class Command(BaseCommand):
    help = 'Automatically assigns all stores to admin users'

    def handle(self, *args, **options):
        admins = User.objects.filter(is_superuser=True)
        stores = Store.objects.filter(is_active=True)
        
        for admin in admins:
            if hasattr(admin, 'profile'):
                admin.profile.stores.set(stores)
                self.stdout.write(self.style.SUCCESS(f'Assigned stores to {admin.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'Admin {admin.username} has no profile'))