from django.conf import settings  # Add this at the top
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.utils import timezone

# Checklist Category
class ChecklistCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True, help_text='Mark category as active/inactive')

    def __str__(self):
        return f'{self.name} {"(Inactive)" if not self.active else ""}'

# Checklist Question
class ChecklistQuestion(models.Model):
    category = models.ForeignKey(ChecklistCategory, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    number = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'number']

    def __str__(self):
        return f"{self.category.name} - Q{self.number}"

# Store locations
class Area(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    users = models.ManyToManyField(User, blank=True, related_name='assigned_areas', 
                                  help_text='Users who can access this area')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    def get_user_count(self):
        """Return count of users assigned to this area"""
        return self.users.count()

    def get_store_count(self):
        """Return count of stores in this area"""
        return self.stores.count()
class Store(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    manager_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True, validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter valid phone number (e.g. +1234567890)')], help_text='Store contact number with country code')
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='stores')
    equipment_categories = models.ManyToManyField('EquipmentCategory', blank=True)

    def __str__(self):
        return self.name

class EquipmentCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(EquipmentCategory, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    model_number = models.CharField(max_length=50, blank=True)
    installation_date = models.DateField(null=True, blank=True)
    maintenance_interval = models.PositiveIntegerField(help_text="Days between maintenance", default=90)

    def __str__(self):
        return f"{self.name} ({self.model_number})"



# The main checklist visit
class AreaManagerVisit(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='visits')

    manager = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    month = models.CharField(max_length=20)
    day = models.IntegerField(default=1)
    time = models.TimeField(auto_now_add=True)
    overall_score = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True)
    run_out_items = models.TextField(blank=True)
    maintenance_needed = models.TextField(blank=True)
    general_notes = models.TextField(blank=True)
    is_draft = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    time_in = models.TimeField('Time In', default=timezone.now)
    time_out = models.TimeField('Time Out', blank=True, null=True)

    def __str__(self):
        return f"Visit to {self.store.name} on {self.date}"

    def calculate_score(self):
        """Calculates score based on completed items"""
        total_items = self.checklist_items.count()
        if total_items == 0:
            return 0
        completed = self.checklist_items.filter(answer=True).count()
        return round((completed / total_items) * 100)

    @property
    def score_letter_grade(self):
        """Return letter grade (A-F) based on score"""
        return 'A' if self.calculate_score() >= 95 else 'B' if self.calculate_score() >= 85 else 'C' if self.calculate_score() >= 75 else 'D' if self.calculate_score() >= 65 else 'F'

# This model stores the answer to each individual question
class ChecklistItem(models.Model):
    visit = models.ForeignKey(
        AreaManagerVisit,
        on_delete=models.CASCADE,
        related_name='checklist_items',  # Changed from 'items' for clarity
        db_index=True
    )
    question = models.ForeignKey(ChecklistQuestion, on_delete=models.CASCADE, null=True, blank=True)
    answer = models.BooleanField()
    comment = models.TextField(blank=True)
    requires_follow_up = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question.category.name} - Q{self.question.number}"

# The action plan items
class ActionPlanItem(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    visit = models.ForeignKey(AreaManagerVisit, on_delete=models.CASCADE, related_name='action_items')
    what = models.TextField()
    who = models.CharField(max_length=100)
    timeframe = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Action: {self.what}"

    class Meta:
        ordering = ['-priority', 'timeframe']


class PriorityChoices(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'

class MaintenanceTicket(models.Model):
    visit = models.ForeignKey(
        'AreaManagerVisit',
        on_delete=models.CASCADE,
        related_name='maintenance_tickets'
    )
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ]
    equipment = models.CharField(max_length=100)
    issue_description = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM
    )
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    closed_date = models.DateTimeField(null=True, blank=True)
    attachments = models.FileField(upload_to='maintenance_attachments/', null=True, blank=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"Maintenance Ticket #{self.id} for {self.visit.store.name}"

    @property
    def is_overdue(self):
        if self.due_date and self.status != 'C':
            return self.due_date < timezone.now().date()
        return False

class VisitAttachment(models.Model):
    visit = models.ForeignKey(AreaManagerVisit, on_delete=models.CASCADE, related_name='attachments')
    checklist_item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name='attachments', null=True, blank=True)
    file = models.FileField(upload_to='visit_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for visit {self.visit.id}"