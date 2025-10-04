from django.db.models import Q, Count, Avg
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
import logging

from ..models import Store, AreaManagerVisit
from ..forms import StoreForm
from .base import BaseViewMixin

logger = logging.getLogger(__name__)


@login_required
def store_list(request):
    """Public-facing store list for the current user with basic stats."""
    stores = Store.objects.filter(is_active=True)
    if hasattr(request.user, 'profile') and request.user.profile.role not in ['admin', 'area_management']:
        stores = request.user.profile.stores.filter(is_active=True)

    data = []
    for s in stores:
        visits = AreaManagerVisit.objects.filter(store=s, manager=request.user, is_draft=False)
        avg = 0
        last = None
        if visits.exists():
            total = sum(v.calculate_score() for v in visits)
            avg = round(total / visits.count(), 1)
            last_v = visits.order_by('-date').first()
            last = last_v.date if last_v else None
        data.append({'store': s, 'avg': avg, 'visits': visits.count(), 'last': last})

    return render(request, 'checklist/stores_list.html', { 'stores': data })


@login_required
def store_detail(request, store_id):
    """Public-facing store detail with visits summary."""
    store = get_object_or_404(Store, id=store_id)
    # Basic authorization: user must have access
    if hasattr(request.user, 'profile') and request.user.profile.role not in ['admin', 'area_management']:
        if store not in request.user.profile.stores.all():
            messages.error(request, 'You do not have access to this store.')
            return redirect('checklist:store_list')

    visits = AreaManagerVisit.objects.filter(store=store, manager=request.user, is_draft=False).order_by('-date')[:20]
    avg = 0
    if visits.exists():
        total = sum(v.calculate_score() for v in visits)
        avg = round(total / visits.count(), 1)

    return render(request, 'checklist/store_detail.html', {
        'store': store,
        'visits': visits,
        'avg': avg,
    })


class StoreManager(BaseViewMixin):
    """Manager class for store operations"""
    
    @staticmethod
    def get_store_analytics():
        """Get comprehensive store analytics"""
        stores = Store.objects.all().annotate(
            visit_count=Count('areamanagervisit', filter=Q(areamanagervisit__is_draft=False)),
            avg_score=Avg('areamanagervisit__calculate_score', filter=Q(areamanagervisit__is_draft=False)),
        ).order_by('-is_active', 'name')
        
        # Calculate store statistics
        total_stores = stores.count()
        active_stores = stores.filter(is_active=True).count()
        inactive_stores = stores.filter(is_active=False).count()
        stores_with_visits = stores.filter(visit_count__gt=0).count()
        
        return {
            'stores': stores,
            'stats': {
                'total': total_stores,
                'active': active_stores,
                'inactive': inactive_stores,
                'with_visits': stores_with_visits,
                'without_visits': total_stores - stores_with_visits,
            }
        }


@user_passes_test(lambda u: u.is_superuser)
def store_management(request):
    """Enhanced store management with comprehensive analytics"""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('checklist:dashboard')
    
    try:
        manager = StoreManager()
        analytics = manager.get_store_analytics()
        
        if request.method == 'POST':
            return handle_store_creation(request)
        
        form = StoreForm()
        
        context = {
            'stores': analytics['stores'],
            'form': form,
            'store_stats': analytics['stats'],
        }
        
        return render(request, 'checklist/store_management.html', context)
        
    except Exception as e:
        logger.error(f"Error in store_management view: {str(e)}")
        messages.error(request, "An error occurred while loading store management.")
        return redirect('checklist:dashboard')


def handle_store_creation(request):
    """Handle store creation with validation and error handling"""
    try:
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save()
            logger.info(f"New store created: {store.name} by {request.user.username}")
            messages.success(request, f'Store "{store.name}" added successfully!')
            return redirect('checklist:store_management')
        else:
            messages.error(request, "Please correct the errors in the form.")
            # Re-render the form with errors
            manager = StoreManager()
            analytics = manager.get_store_analytics()
            context = {
                'stores': analytics['stores'],
                'form': form,
            }
            return render(request, 'checklist/store_management.html', context)
    except ValidationError as e:
        messages.error(request, f"Validation error: {str(e)}")
        return redirect('checklist:store_management')
    except Exception as e:
        logger.error(f"Error creating store: {str(e)}")
        messages.error(request, "Failed to create store. Please try again.")
        return redirect('checklist:store_management')


@user_passes_test(lambda u: u.is_superuser)
def edit_store(request, store_id):
    """Enhanced store editing with better validation and logging"""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('checklist:dashboard')
    
    try:
        store = get_object_or_404(Store, id=store_id)
        original_name = store.name
        
        if request.method == 'POST':
            form = StoreForm(request.POST, instance=store)
            if form.is_valid():
                updated_store = form.save()
                
                # Log the change
                if original_name != updated_store.name:
                    logger.info(f"Store renamed from '{original_name}' to '{updated_store.name}' by {request.user.username}")
                
                messages.success(request, f'Store "{updated_store.name}" updated successfully!')
                return redirect('checklist:store_management')
            else:
                messages.error(request, "Please correct the errors in the form.")
        else:
            form = StoreForm(instance=store)
        
        context = {
            'form': form,
            'store': store,
        }
        
        return render(request, 'checklist/edit_store.html', context)
        
    except Exception as e:
        logger.error(f"Error editing store {store_id}: {str(e)}")
        messages.error(request, "An error occurred while editing the store.")
        return redirect('checklist:store_management')


@user_passes_test(lambda u: u.is_superuser)
def toggle_store_status(request, store_id):
    """Enhanced store status toggle with logging and validation"""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('checklist:dashboard')
    
    try:
        store = get_object_or_404(Store, id=store_id)
        store.is_active = not store.is_active
        store.save()
        
        status = "activated" if store.is_active else "deactivated"
        action = "activated" if store.is_active else "deactivated"
        
        logger.info(f"Store '{store.name}' {action} by {request.user.username}")
        messages.success(request, f'Store "{store.name}" {status} successfully!')
        
        return redirect('checklist:store_management')
        
    except Exception as e:
        logger.error(f"Error toggling store status {store_id}: {str(e)}")
        messages.error(request, "Failed to update store status. Please try again.")
        return redirect('checklist:store_management')