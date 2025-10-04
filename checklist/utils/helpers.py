"""
Helper utilities for the checklist application
"""
from django.utils import timezone
from django.db.models import Avg, Count
import logging

logger = logging.getLogger(__name__)


def calculate_category_scores(visit):
    """
    Calculate scores for each category in a visit
    """
    from checklist.models import ChecklistItem, ChecklistCategory
    
    category_scores = {}
    items = ChecklistItem.objects.filter(visit=visit)
    
    for category in ChecklistCategory.objects.all():
        category_items = items.filter(question__category=category)
        total_items = category_items.count()
        yes_count = category_items.filter(answer=True).count()
        
        if total_items > 0:
            category_scores[category.name] = round((yes_count / total_items) * 100, 1)
        else:
            category_scores[category.name] = 0
    
    return category_scores


def get_visit_statistics(visit):
    """
    Get comprehensive statistics for a visit
    """
    from checklist.models import ChecklistItem, ActionPlanItem
    
    items = ChecklistItem.objects.filter(visit=visit)
    action_items = ActionPlanItem.objects.filter(visit=visit)
    
    return {
        'total_items': items.count(),
        'passed_items': items.filter(answer=True).count(),
        'failed_items': items.filter(answer=False).count(),
        'follow_up_items': items.filter(requires_follow_up=True).count(),
        'action_items_count': action_items.count(),
        'open_actions': action_items.filter(status='open').count(),
        'completed_actions': action_items.filter(status='completed').count(),
    }


def generate_performance_report(user, days=30):
    """
    Generate a performance report for a user over specified days
    """
    from checklist.models import AreaManagerVisit, ActionPlanItem
    
    start_date = timezone.now().date() - timezone.timedelta(days=days)
    
    visits = AreaManagerVisit.objects.filter(
        manager=user,
        is_draft=False,
        date__gte=start_date
    )
    
    action_items = ActionPlanItem.objects.filter(
        visit__manager=user,
        created_at__gte=start_date
    )
    
    return {
        'period': f"Last {days} days",
        'total_visits': visits.count(),
        'average_score': visits.aggregate(avg=Avg('calculate_score'))['avg'] or 0,
        'actions_created': action_items.count(),
        'actions_completed': action_items.filter(status='completed').count(),
        'completion_rate': round(
            (action_items.filter(status='completed').count() / 
             max(action_items.count(), 1)) * 100, 1
        ),
    }


def format_chart_data(visits):
    """
    Format visit data for chart display
    """
    chart_data = {
        'dates': [],
        'scores': [],
        'stores': [],
    }
    
    for visit in visits:
        chart_data['dates'].append(visit.date.strftime('%b %d'))
        score = visit.calculate_score()
        chart_data['scores'].append(score if score is not None else 0)
        chart_data['stores'].append(visit.store.name)
    
    return chart_data