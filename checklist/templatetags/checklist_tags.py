from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def timedelta_days(value, days):
    return value + timedelta(days=days)

@register.filter
def get_action_badge(action_type):
    badge_map = {
        'create': 'success',
        'update': 'warning',
        'delete': 'danger'
    }
    return badge_map.get(action_type, 'secondary')

@register.filter
def get_category_icon(category):
    icons = {
        'Store Operations': 'store',
        'Customer Experience': 'users',
        'Team & Staff': 'user-tie',
        'Sales & Performance': 'chart-line',
        'Health & Safety': 'shield-alt',
        'Maintenance & Assets': 'tools',
        'Administration': 'file-alt',
    }
    return icons.get(category, 'tasks')

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)

@register.simple_tag
def priority_badge(priority):
    if priority == 'high':
        return 'bg-danger'
    elif priority == 'medium':
        return 'bg-warning text-dark'
    else:
        return 'bg-success'

@register.simple_tag
def status_badge(status):
    status_map = {
        'pending': 'bg-warning text-dark',
        'in_progress': 'bg-info text-dark', 
        'completed': 'bg-success',
        'N': 'bg-primary',
        'IP': 'bg-info text-dark'
    }
    return status_map.get(status, 'bg-secondary')