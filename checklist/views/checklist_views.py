from django.db.models import Q, Count, Avg
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import json
import logging
from datetime import datetime, timedelta
from collections import OrderedDict

# Correct import statement:
from ..models import ChecklistItem, Store, ActionPlanItem, AreaManagerVisit, VisitAttachment, ChecklistCategory, ChecklistQuestion
from ..forms import VisitForm, ActionPlanItemForm
from .base import BaseViewMixin, handle_ajax_response

logger = logging.getLogger(__name__)


class ChecklistManager(BaseViewMixin):
    """Manager class for checklist operations"""
    
    @staticmethod
    def get_questions_by_category():
        """Get questions organized by category"""
        questions_by_category = OrderedDict()
        categories = ChecklistCategory.objects.filter(active=True).order_by('name')
        
        for category in categories:
            questions = ChecklistQuestion.objects.filter(
                category=category, 
                is_active=True
            ).order_by('number')
            if questions.exists():
                questions_by_category[category] = questions
                
        return questions_by_category
    
    @staticmethod
    def process_checklist_items(request, visit):
        """Process checklist items and create action items for failed checks"""
        created_actions = 0
        total_questions = 0
        positive_answers = 0
        questions = ChecklistQuestion.objects.filter(is_active=True)
    
        for question in questions:
            field_name = f"q_{question.id}"
            comment_name = f"comment_{question.id}"
            file_name = f"file_{question.id}"
            
            # Check for checkbox value (will be 'true' if checked, None if unchecked)
            answer_value = request.POST.get(field_name) == 'true'
            comment_value = request.POST.get(comment_name, '').strip()
            
            # Create checklist item
            checklist_item = ChecklistItem.objects.create(
                visit=visit,
                question=question,
                answer=answer_value,
                comment=comment_value
            )

            # Handle file upload
            if file_name in request.FILES:
                file = request.FILES[file_name]
                # Validate file size (5MB max)
                if file.size > 5242880:
                    raise ValidationError(f'File size exceeds 5MB limit: {file.name}')
                # Validate file type
                valid_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
                if file.content_type not in valid_types:
                    raise ValidationError(f'Invalid file type: {file.name}. Only images, PDF, and Word documents allowed.')
                
                try:
                    VisitAttachment.objects.create(
                        visit=visit,
                        checklist_item=checklist_item,
                        file=file
                    )
                except Exception as e:
                    logger.error(f'Error saving file attachment: {str(e)}')
                    raise ValidationError(f'Error uploading file: {file.name}')
            
            # If answer is No and there's a comment, create an action item
            if not answer_value and comment_value:
                ActionPlanItem.objects.create(
                    visit=visit,
                    what=f"{question.category.name} - Q{question.number}: {question.text}",
                    who=request.user.get_full_name() or request.user.username,
                    timeframe=timezone.now().date() + timedelta(days=7),
                    status='open',
                    priority='medium',
                    remarks=comment_value
                )
                checklist_item.requires_follow_up = True
                checklist_item.save()
                created_actions += 1
            total_questions += 1
            if answer_value:
                positive_answers += 1

        visit.overall_score = round((positive_answers / total_questions) * 100) if total_questions > 0 else 0
        visit.save()
        return created_actions


@login_required
def new_checklist(request):
    """Create a new checklist"""
    manager = ChecklistManager()
    
    # Check user profile
    if not hasattr(request.user, 'profile'):
        messages.error(request, "Your user profile is not set up. Please contact an administrator.")
        return redirect('checklist:dashboard')

    # Get user stores
    stores = manager.get_user_stores(request.user)
    single_store = None
    
    if request.user.profile.role == 'visit_creator' and stores.count() == 1:
        single_store = stores.first()

    if not stores.exists():
        if request.user.profile.role not in ['admin', 'area_management', 'store_selector']:
            messages.error(request, "You are not assigned to any active stores. Please contact an administrator.")
        else:
            messages.error(request, "No active stores available in the system. Please add a store first.")
        return redirect('checklist:dashboard')

    if request.method == 'POST':
        return handle_checklist_submission(request, stores)

    # GET request - prepare form
    questions_by_category = manager.get_questions_by_category()
    now = timezone.now()
    visit_form = VisitForm(initial={'month': now.month, 'day': now.day})

    # Calculate date limits
    min_date = now - timedelta(days=30)  # Allow 30 days back
    max_date = now + timedelta(days=7)   # Allow 7 days forward
    
    return render(request, 'checklist/new_checklist.html', {
        'stores': stores,
        'single_store': single_store,
        'questions_by_category': questions_by_category,
        'current_date': now.strftime('%Y-%m-%d'),
        'current_time': now.strftime('%H:%M'),
        'min_date': min_date,
        'max_date': max_date,
        'form_data': {},
    })


def handle_checklist_submission(request, stores):
    """Handle POST request for checklist submission"""
    manager = ChecklistManager()
    form_data = request.POST

    try:
        with transaction.atomic():
            store_id = form_data.get('store')
            visit_date_str = form_data.get('visit_date')
            time_in_str = form_data.get('time_in')
            time_out_str = form_data.get('time_out')

            if not all([store_id, visit_date_str, time_in_str]):
                messages.error(request, "Store, Visit Date, and Time In are required.")
                return render_checklist_form(request, stores, form_data)

            user_store = get_object_or_404(Store, id=store_id)
            
            try:
                visit_date = datetime.strptime(visit_date_str, '%Y-%m-%d').date()
                time_in = datetime.strptime(time_in_str, '%H:%M').time()
                time_out = datetime.strptime(time_out_str, '%H:%M').time() if time_out_str and time_out_str.strip() else None
            except (ValueError, TypeError) as e:
                logger.error(f"Date/time parsing error: {str(e)}")
                messages.error(request, "Invalid date or time format. Please check your inputs.")
                return render_checklist_form(request, stores, form_data)

            action = form_data.get('action')
            is_draft = (action == 'draft')
            
            # Get additional form fields
            general_notes = form_data.get('general_notes', '')
            run_out_items = form_data.get('run_out_items', '')
            maintenance_needed = form_data.get('maintenance_needed', '')

            new_visit = AreaManagerVisit.objects.create(
                manager=request.user,
                store=user_store,
                date=visit_date,
                time_in=time_in,
                time_out=time_out,
                is_draft=is_draft,
                general_notes=general_notes,
                run_out_items=run_out_items,
                maintenance_needed=maintenance_needed
            )

            try:
                created_actions = manager.process_checklist_items(request, new_visit)
            except ValidationError as e:
                messages.error(request, str(e))
                new_visit.delete()  # Rollback the visit creation
                return render_checklist_form(request, stores, form_data)

            if is_draft:
                messages.info(request, "Checklist saved as draft.")
                return redirect('checklist:checklist_history')
            else:
                messages.success(request, f'Checklist submitted successfully! {created_actions} action items created.')
                return redirect('checklist:checklist_history')

    except ValidationError as e:
        messages.error(request, f"Validation error: {str(e)}")
        return render_checklist_form(request, stores, form_data)
    except Exception as e:
        logger.error(f"Error in checklist submission: {str(e)}")
        messages.error(request, "An error occurred while submitting the checklist. Please try again.")
        return render_checklist_form(request, stores, form_data)


def render_checklist_form(request, stores, form_data=None):
    """Render the checklist form with proper context"""
    manager = ChecklistManager()
    
    if form_data is None:
        form_data = {}

    questions_by_category = manager.get_questions_by_category()
    now = timezone.now()

    # Calculate date limits
    min_date = now - timedelta(days=30)
    max_date = now + timedelta(days=7)
    
    context = {
        'form_data': form_data,
        'questions_by_category': questions_by_category,
        'stores': stores,
        'single_store': stores.first() if stores.count() == 1 and request.user.profile.role == 'visit_creator' else None,
        'current_date': now.strftime('%Y-%m-%d'),
        'current_time': now.strftime('%H:%M'),
        'min_date': min_date,
        'max_date': max_date,
    }
    return render(request, 'checklist/new_checklist.html', context)


@login_required
@require_POST
@handle_ajax_response
def save_draft(request):
    """Save checklist as draft with enhanced error handling"""
    try:
        data = json.loads(request.body)
        
        with transaction.atomic():
            # Extract data with defaults
            visit_data = data.get('visit_data', {})
            store_id = data.get('store_id')
            run_out_items = data.get('run_out_items', '')
            maintenance_needed = data.get('maintenance_needed', '')
            general_notes = data.get('general_notes', '')
            answers = data.get('answers', {})
            
            # Get or create store
            if store_id:
                store = get_object_or_404(Store, id=store_id)
            else:
                store = Store.objects.first()
            
            # Create draft visit
            draft_visit = AreaManagerVisit.objects.create(
                store=store,
                manager=request.user,
                month=visit_data.get('month', ''),
                day=visit_data.get('day', 1),
                run_out_items=run_out_items,
                maintenance_needed=maintenance_needed,
                general_notes=general_notes,
                is_draft=True
            )
            
            # Save answers with validation
            saved_answers = 0
            for question_key, answer_data in answers.items():
                try:
                    parts = question_key.split('_')
                    if len(parts) < 3:
                        logger.warning(f"Invalid question key format: {question_key}")
                        continue
                    
                    category_name = parts[1]
                    question_number = int(parts[2])

                    question_obj = ChecklistQuestion.objects.get(
                        category__name=category_name,
                        number=question_number
                    )

                    ChecklistItem.objects.create(
                        visit=draft_visit,
                        question=question_obj,
                        answer=answer_data.get('answer', False),
                        comment=answer_data.get('comment', '')
                    )
                    saved_answers += 1
                except ChecklistQuestion.DoesNotExist:
                    logger.warning(f"ChecklistQuestion not found for key: {question_key}")
                except Exception as e:
                    logger.warning(f"Error processing draft answer {question_key}: {str(e)}")
            
            logger.info(f"Draft saved successfully with {saved_answers} answers")
            return JsonResponse({
                'status': 'success', 
                'message': f'Draft saved successfully! {saved_answers} items saved.',
                'draft_id': draft_visit.id
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
    except Exception as e:
        logger.error(f"Error saving draft: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Failed to save draft. Please try again.'})


@login_required
@handle_ajax_response
def load_draft(request, draft_id):
    """Load draft checklist data"""
    try:
        draft_visit = get_object_or_404(AreaManagerVisit, id=draft_id, manager=request.user, is_draft=True)
        items = ChecklistItem.objects.filter(visit=draft_visit)
        
        answers = {}
        for item in items:
            key = f"answer_{item.question.category.name}_{item.question.number}"
            answers[key] = {
                'answer': item.answer,
                'comment': item.comment
            }
        
        draft_data = {
            'status': 'success',
            'data': {
                'visit_data': {
                    'month': draft_visit.month,
                    'day': draft_visit.day,
                    'time': draft_visit.time.strftime('%H:%M') if draft_visit.time else '',
                },
                'store_id': draft_visit.store.id,
                'run_out_items': draft_visit.run_out_items,
                'maintenance_needed': draft_visit.maintenance_needed,
                'general_notes': draft_visit.general_notes,
                'answers': answers
            }
        }
        
        return JsonResponse(draft_data)
        
    except Exception as e:
        logger.error(f"Error loading draft {draft_id}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Failed to load draft'})


@login_required
def delete_draft(request, draft_id):
    """Delete a draft checklist"""
    try:
        draft_visit = get_object_or_404(AreaManagerVisit, id=draft_id, manager=request.user, is_draft=True)
        draft_name = f"{draft_visit.store.name} - {draft_visit.month}"
        draft_visit.delete()
        
        logger.info(f"Draft deleted: {draft_name} by user {request.user.username}")
        messages.success(request, f'Draft "{draft_name}" deleted successfully!')
        return redirect('checklist:checklist_drafts')
        
    except Exception as e:
        logger.error(f"Error deleting draft {draft_id}: {str(e)}")
        messages.error(request, 'Failed to delete draft. Please try again.')
        return redirect('checklist:checklist_drafts')


@login_required
def checklist_success(request):
    """Show success page after checklist submission"""
    recent_visits = AreaManagerVisit.objects.filter(
        manager=request.user, 
        is_draft=False
    ).order_by('-created_at')[:5]
    
    return render(request, 'checklist/success.html', {
        'recent_visits': recent_visits,
        'total_visits': AreaManagerVisit.objects.filter(manager=request.user, is_draft=False).count()
    })


@login_required
def checklist_history(request):
    """Display checklist history with sorting and pagination"""
    sort_by = request.GET.get('sort', '-date')
    valid_sorts = ['store__name', '-store__name', 'date', '-date', 'overall_score', '-overall_score']
    
    visits = AreaManagerVisit.objects.filter(
        manager=request.user,
        is_draft=False
    ).select_related('store')
    
    if sort_by in valid_sorts:
        visits = visits.order_by(sort_by)
    
    paginator = Paginator(visits, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Build history list for template
    history = []
    for visit in page_obj:
        history.append({
            'timestamp': visit.created_at,
            'user': visit.manager.get_full_name() or str(visit.manager),
            'action': 'Visit',
            'details': f"Store: {visit.store.name}, Score: {getattr(visit, 'overall_score', 'N/A')}"
        })
    
    return render(request, 'checklist/history.html', {
        'history': history,
        'sort_by': sort_by,
        'page_obj': page_obj
    })


@login_required
def checklist_drafts(request):
    """Display draft checklists with statistics"""
    try:
        drafts = AreaManagerVisit.objects.filter(
            manager=request.user, 
            is_draft=True
        ).select_related('store').order_by('-created_at')
        
        draft_stats = {
            'total': drafts.count(),
            'this_week': drafts.filter(created_at__gte=timezone.now() - timedelta(days=7)).count(),
            'this_month': drafts.filter(created_at__gte=timezone.now() - timedelta(days=30)).count(),
        }
        
        context = {
            'drafts': drafts,
            'draft_stats': draft_stats,
        }
        
        return render(request, 'checklist/drafts.html', context)
        
    except Exception as e:
        logger.error(f"Error in checklist_drafts view: {str(e)}")
        messages.error(request, "An error occurred while loading drafts.")
        return render(request, 'checklist/drafts.html', {})


@login_required
def checklist_detail(request, visit_id):
    """Display detailed view of a checklist"""
    visit = get_object_or_404(AreaManagerVisit, id=visit_id, manager=request.user)
    items = visit.checklist_items.select_related('question__category').order_by('question__category__name', 'question__number')

    items_by_category = OrderedDict()
    for item in items:
        if item.question.category not in items_by_category:
            items_by_category[item.question.category] = []
        items_by_category[item.question.category].append(item)

    passed_items = items.filter(answer=True).count()
    failed_items = items.filter(answer=False).count()

    context = {
        'visit': visit,
        'items': items,
        'items_by_category': items_by_category,
        'passed_items': passed_items,
        'failed_items': failed_items,
        'overall_score': visit.calculate_score(),
    }
    return render(request, 'checklist/checklist_detail.html', context)


def print_visit_report(request, visit_id):
    """
    Generate a PDF report for a specific visit
    """
    visit = get_object_or_404(AreaManagerVisit, id=visit_id)
    checklist_items = ChecklistItem.objects.filter(visit=visit)
    action_items = ActionPlanItem.objects.filter(visit=visit)
    
    return render(request, 'checklist/visit_report.html', {
        'visit': visit,
        'checklist_items': checklist_items,
        'action_items': action_items,
    })