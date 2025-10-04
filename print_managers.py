import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'caribou_dashboard.settings')
import django
django.setup()
from checklist.models import AreaManagerVisit

visits = AreaManagerVisit.objects.filter(is_draft=False)
for visit in visits[:10]:
    print(f"Manager: {visit.manager.username}, Store: {visit.store.name}, Date: {visit.date}")