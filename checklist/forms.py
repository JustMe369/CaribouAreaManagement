from django import forms
from .models import ActionPlanItem, AreaManagerVisit, ChecklistItem, Store, ChecklistQuestion
from .models import MaintenanceTicket  # Add this import at the top
from .models import PriorityChoices  # Add this import

class VisitForm(forms.ModelForm):
    class Meta:
        model = AreaManagerVisit
        # Remove 'date' from fields
        fields = ['month', 'day', 'general_notes']
class AreaManagerVisitForm(forms.ModelForm):
    class Meta:
        model = AreaManagerVisit
        fields = ['store', 'time_in', 'time_out', 'month', 'day', 'general_notes']
        widgets = {
            'time_in': forms.TimeInput(attrs={'type': 'time'}),
            'time_out': forms.TimeInput(attrs={'type': 'time'}),
        }

class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ['answer', 'comment']

class ActionPlanItemForm(forms.ModelForm):
    class Meta:
        model = ActionPlanItem
        fields = ['what', 'who', 'timeframe', 'status', 'priority', 'remarks']
        widgets = {
            'timeframe': forms.DateInput(attrs={'type': 'date'}),
        }

class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = AreaManagerVisit  # Placeholder, adjust as needed
        fields = ['maintenance_needed']
        widgets = {
            'maintenance_needed': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = '__all__'

class MaintenanceTicketForm(forms.ModelForm):
    visit = forms.ModelChoiceField(
        queryset=AreaManagerVisit.objects.select_related('store').order_by('-date'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label="Select a visit..."
    )
    
    class Meta:
        model = MaintenanceTicket
        fields = ['visit', 'equipment', 'priority', 'due_date', 'issue_description', 'status', 'attachments']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'issue_description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Describe the maintenance issue in detail...'}),
            'equipment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Espresso Machine, Coffee Grinder, etc.'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always make visit required
        self.fields['visit'].required = True

class MaintenanceTicketEditForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTicket
        fields = ['equipment', 'issue_description', 'priority', 'due_date', 'status']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'issue_description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'equipment': forms.TextInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class ChecklistQuestionForm(forms.ModelForm):
    class Meta:
        model = ChecklistQuestion
        fields = ['category', 'text', 'number', 'is_active']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'number': forms.NumberInput(attrs={'min': 1})
        }

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = AreaManagerVisit
        fields = ['store', 'time_in', 'time_out', 'general_notes']
        widgets = {
            'time_in': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'time_out': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }