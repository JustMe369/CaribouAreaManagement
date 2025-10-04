from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import json
import logging

from ..models import ActionPlanItem, Store
from ..forms import ActionPlanItemForm
from .base import BaseViewMixin, handle_ajax_response

logger = logging.getLogger(__name__)


class ActionPlanManager(BaseViewMixin):
    """Manager class for action plan operations"""
    
    @staticmethod
    def get_filtered_actions(user, filters):
        """Get filtered action items based on request parameters"""
        action_items = ActionPlanItem.objects.filter(
            visit__manager=user
        ).select_related('visit__store').order_by('-created_at')

        # Apply filters
        status_filter = filters.get('status', '')
        priority_filter = filters.get('priority', '')
        store_filter = filters.get('store', '')
        date_filter = filters.get('date_filter', '')
        search_query = filters.get('search', '')

        if status_filter:
            action_items = action_items.filter(status=status_filter)
        if priority_filter:
            action_items = action_items.filter(priority=priority_filter)
        if store_filter:
            action_items = action_items.filter(visit__store__id=store_filter)
        if date_filter:
            try:
                filter_date = timezone.datetime.strptime(date_filter, '%Y-%m-%d').date()
                action_items = action_items.filter(timeframe=filter_date)
            except (ValueError, TypeError):
                pass
        if search_query:
            action_items = action_items.filter(
                Q(what__icontains=search_query) |
                Q(visit__store__name__icontains=search_query)
            )

        return action_items
    
    @staticmethod
    def calculate_action_stats(action_items, today):
        """Calculate statistics for action items"""
        return {
            'total': action_items.count(),
            'completed': action_items.filter(status='completed').count(),
            'open': action_items.filter(status='open').count(),
            'overdue': action_items.filter(status='open', timeframe__lt=today).count(),
        }


@login_required
def action_plan(request):
    """Display and manage the action plan with advanced filtering"""
    manager = ActionPlanManager()
    
    try:
        today = timezone.now().date()

        # Get filter parameters
        filters = {
            'status': request.GET.get('status', ''),
            'priority': request.GET.get('priority', ''),
            'store': request.GET.get('store', ''),
            'date_filter': request.GET.get('date_filter', ''),
            'search': request.GET.get('search', ''),
        }

        # Get filtered actions
        action_items_list = manager.get_filtered_actions(request.user, filters)

        # Pagination
        paginator = Paginator(action_items_list, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Calculate statistics
        stats = manager.calculate_action_stats(action_items_list, today)

        # Get all stores for the filter dropdown
        stores = Store.objects.filter(is_active=True)

        context = {
            'page_obj': page_obj,
            'stats': stats,
            'stores': stores,
            'filters': filters,
            'today': today,
        }
        
        return render(request, 'checklist/action_plan.html', context)
        
    except Exception as e:
        logger.error(f"Error in action_plan view: {str(e)}")
        messages.error(request, "An error occurred while loading the action plan.")
        
        context = {
            'page_obj': None,
            'stats': {'total': 0, 'completed': 0, 'open': 0, 'overdue': 0},
            'stores': [],
            'filters': {'status': '', 'priority': '', 'store': '', 'date_filter': '', 'search': ''},
            'today': timezone.now().date(),
            'error': True,
        }
        return render(request, 'checklist/action_plan.html', context)


@login_required
def update_action_item(request, item_id):
    """Update an action item with validation and logging"""
    try:
        action_item = get_object_or_404(
            ActionPlanItem.objects.select_related('visit__store'), 
            id=item_id, 
            visit__manager=request.user
        )
        
        if request.method == 'POST':
            form = ActionPlanItemForm(request.POST, instance=action_item)
            if form.is_valid():
                updated_item = form.save(commit=False)
                
                # Log status changes
                if 'status' in form.changed_data:
                    old_status = action_item.status
                    new_status = updated_item.status
                    logger.info(f"Action item {item_id} status changed from {old_status} to {new_status} by {request.user.username}")
                
                updated_item.save()
                
                messages.success(request, f'Action item "{updated_item.what[:50]}..." updated successfully!')
                
                # Redirect back to the page they came from
                next_url = request.GET.get('next', 'checklist:action_plan')
                return redirect(next_url)
            else:
                messages.error(request, "Please correct the errors in the form.")
        else:
            form = ActionPlanItemForm(instance=action_item)
        
        context = {
            'form': form,
            'action_item': action_item,
            'today': timezone.now().date(),
            'next': request.GET.get('next', 'checklist:action_plan')
        }
        
        return render(request, 'checklist/action_plan_item_update.html', context)
        
    except Exception as e:
        logger.error(f"Error in update_action_item view: {str(e)}")
        messages.error(request, "An error occurred while updating the action item.")
        return redirect('checklist:action_plan')


@login_required
@require_POST
@handle_ajax_response
def bulk_update_actions(request):
    """Bulk update multiple action items via AJAX"""
    try:
        data = json.loads(request.body)
        action_ids = data.get('action_ids', [])
        new_status = data.get('status')
        new_priority = data.get('priority')
        
        if not action_ids:
            return JsonResponse({'status': 'error', 'message': 'No action items selected'})
        
        # Validate that all action items belong to the user
        user_actions = ActionPlanItem.objects.filter(
            id__in=action_ids,
            visit__manager=request.user
        )
        
        if user_actions.count() != len(action_ids):
            return JsonResponse({'status': 'error', 'message': 'Some action items not found or unauthorized'})
        
        # Perform bulk update
        updates = {}
        if new_status:
            updates['status'] = new_status
        if new_priority:
            updates['priority'] = new_priority
        
        if updates:
            updated_count = user_actions.update(**updates)
            logger.info(f"Bulk updated {updated_count} action items for user {request.user.username}")
            
            return JsonResponse({
                'status': 'success',
                'message': f'Successfully updated {updated_count} action items',
                'updated_count': updated_count
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'No valid updates specified'})
            
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f"Error in bulk update actions: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Failed to update action items'})


@login_required
@require_POST
def bulk_update_action_items_form(request):
    """Bulk update action items via form submission"""
    item_ids = request.POST.getlist('item_ids')
    bulk_action = request.POST.get('bulk_action')

    if not item_ids:
        messages.warning(request, "You didn't select any items.")
        return redirect('checklist:action_plan')

    if not bulk_action:
        messages.warning(request, "You didn't select a bulk action.")
        return redirect('checklist:action_plan')

    items_to_update = ActionPlanItem.objects.filter(
        id__in=item_ids, 
        visit__manager=request.user
    )

    updated_count = 0
    if bulk_action == 'mark_completed':
        updated_count = items_to_update.update(status='completed', completed_at=timezone.now())
    elif bulk_action == 'set_high':
        updated_count = items_to_update.update(priority='high')
    elif bulk_action == 'set_medium':
        updated_count = items_to_update.update(priority='medium')
    elif bulk_action == 'set_low':
        updated_count = items_to_update.update(priority='low')
    
    if updated_count > 0:
        messages.success(request, f"Successfully updated {updated_count} items.")
    else:
        messages.warning(request, "No items were updated.")

    return redirect('checklist:action_plan')