from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import logging

from ..models import MaintenanceTicket, AreaManagerVisit, Store
from ..forms import MaintenanceTicketForm, MaintenanceForm, MaintenanceTicketEditForm
from .base import LoginRequiredMixin

logger = logging.getLogger(__name__)


class MaintenanceManager:
    """Manager class for maintenance operations"""
    
    @staticmethod
    def get_paginated_maintenance(page_number, items_per_page=10):
        """Get paginated maintenance tickets"""
        maintenance_items = MaintenanceTicket.objects.all().select_related(
            'visit__store'
        ).order_by('-created_date')
        
        paginator = Paginator(maintenance_items, items_per_page)
        
        try:
            tickets = paginator.page(page_number)
        except PageNotAnInteger:
            tickets = paginator.page(1)
        except EmptyPage:
            tickets = paginator.page(paginator.num_pages)
            
        return tickets


@method_decorator(login_required, name='dispatch')
class NewMaintenanceView(LoginRequiredMixin, CreateView):
    """View for creating new maintenance tickets"""
    model = MaintenanceTicket
    form_class = MaintenanceTicketForm
    template_name = 'checklist/new_maintenance.html'
    success_url = '/checklist/maintenance/'

    def get_initial(self):
        initial = super().get_initial()
        visit_id = self.kwargs.get('visit_id')
        if visit_id:
            initial['visit'] = visit_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Maintenance ticket created successfully.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, f"Form errors: {form.errors}")
        return super().form_invalid(form)


@login_required
def maintenance_detail(request, ticket_id):
    """View maintenance ticket details"""
    ticket = get_object_or_404(MaintenanceTicket, id=ticket_id)
    return render(request, 'checklist/maintenance_detail.html', {'ticket': ticket})


@login_required
def edit_maintenance(request, ticket_id):
    """Edit an existing maintenance ticket"""
    ticket = get_object_or_404(MaintenanceTicket, id=ticket_id)
    
    if request.method == 'POST':
        form = MaintenanceTicketEditForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, "Maintenance ticket updated successfully!")
            return redirect('checklist:maintenance_detail', ticket_id=ticket.id)
    else:
        form = MaintenanceTicketEditForm(instance=ticket)
    
    return render(request, 'checklist/edit_maintenance.html', {
        'form': form, 
        'ticket': ticket
    })


@login_required
def new_maintenance(request):
    """
    View for creating a new maintenance ticket (standalone version)
    """
    if request.method == 'POST':
        form = MaintenanceTicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save()
            messages.success(request, "Maintenance ticket created successfully!")
            return redirect('checklist:maintenance_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = MaintenanceTicketForm()
    
    return render(request, 'checklist/new_maintenance.html', {'form': form})


@login_required
def maintenance_list(request):
    """Display paginated list of maintenance tickets with filtering"""
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    from ..models import Store
    
    tickets = MaintenanceTicket.objects.all().select_related('visit__store').order_by('-created_date')
    
    # Apply filters
    filters = {
        'status': request.GET.get('status', ''),
        'priority': request.GET.get('priority', ''),
        'store': request.GET.get('store', ''),
        'date_range': request.GET.get('date_range', '')
    }
    
    if filters['status']:
        tickets = tickets.filter(status=filters['status'])
        
    if filters['priority']:
        tickets = tickets.filter(priority=filters['priority'])
        
    if filters['store']:
        tickets = tickets.filter(visit__store__id=filters['store'])
        
    if filters['date_range']:
        today = datetime.now().date()
        if filters['date_range'] == 'today':
            tickets = tickets.filter(created_date__date=today)
        elif filters['date_range'] == 'this_week':
            start_week = today - timedelta(days=today.weekday())
            tickets = tickets.filter(created_date__date__gte=start_week)
        elif filters['date_range'] == 'this_month':
            tickets = tickets.filter(created_date__year=today.year, created_date__month=today.month)
        elif filters['date_range'] == 'last_month':
            last_month = today.replace(day=1) - timedelta(days=1)
            tickets = tickets.filter(created_date__year=last_month.year, created_date__month=last_month.month)
    
    # Calculate statistics
    all_tickets = MaintenanceTicket.objects.all()
    stats = {
        'total': all_tickets.count(),
        'pending': all_tickets.filter(status='pending').count(),
        'in_progress': all_tickets.filter(status='in_progress').count(),
        'completed': all_tickets.filter(status='completed').count(),
        'overdue': all_tickets.filter(due_date__lt=datetime.now().date(), status__in=['pending', 'in_progress']).count(),
        'high_priority': all_tickets.filter(priority='high').count(),
    }
    
    # Pagination
    paginator = Paginator(tickets, 10)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get trend data for last 30 days
    from django.db.models import Count
    from django.db.models.functions import TruncDate
    
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    trend_data = MaintenanceTicket.objects.filter(
        created_date__date__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(created_date)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Get available visits and stores
    visits = AreaManagerVisit.objects.select_related('store').order_by('-date')[:50]
    stores = Store.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'filters': filters,
        'visits': visits,
        'stores': stores,
        'trend_data': list(trend_data),
    }
    return render(request, 'checklist/maintenance_list.html', context)