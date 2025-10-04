from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from ..models import (
    AreaManagerVisit,
    ChecklistItem,
    ActionPlanItem,
    MaintenanceTicket,
    Store,
)


@login_required
def reports(request):
    """Basic reports dashboard with key counts. Extend as needed."""
    today = timezone.now().date()
    last_30 = today - timedelta(days=30)

    context = {
        'visits_count': AreaManagerVisit.objects.filter(is_draft=False).count(),
        'visits_30': AreaManagerVisit.objects.filter(is_draft=False, date__gte=last_30).count(),
        'open_actions': ActionPlanItem.objects.filter(status='open').count(),
        'pending_tickets': MaintenanceTicket.objects.filter(status='pending').count(),
        'in_progress_tickets': MaintenanceTicket.objects.filter(status='in_progress').count(),
        'stores': Store.objects.filter(is_active=True).count(),
    }
    return render(request, 'checklist/reports.html', context)
