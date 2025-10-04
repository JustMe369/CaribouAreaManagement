from django.db import models
from django.contrib.auth.models import User
from checklist.models import Area  # Import Area model

class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'System Admin'),
        ('area_manager', 'Area Manager'),
        ('store_manager', 'Store Manager'),
        ('area_management', 'Area Management'),
        ('store_selector', 'Store Selector'),
        ('visit_creator', 'Visit Creator')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    stores = models.ManyToManyField('checklist.Store', blank=True)
    areas = models.ManyToManyField('checklist.Area', blank=True)  # New field for area access

    def has_store_access(self, store):
        if self.role in ['admin', 'area_manager']:
            return True
        return store in self.stores.all() or store.area in self.areas.all()

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

# Create your models here.