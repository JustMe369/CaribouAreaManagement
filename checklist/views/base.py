from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
import logging

# Correct import statement:
from ..models import Store

# Set up logging
logger = logging.getLogger(__name__)

class BaseViewMixin:
    """Base mixin for all views with common functionality"""
    
    @classmethod
    def get_user_stores(cls, user):
        """Get stores accessible by user based on role"""
        # Remove the incorrect import from here
        if not hasattr(user, 'profile'):
            return Store.objects.none()
            
        profile = user.profile
        if profile.role in ['admin', 'area_management', 'store_selector']:
            return Store.objects.filter(is_active=True)
        else:
            return profile.stores.filter(is_active=True)


class StaffRequiredMixin(LoginRequiredMixin):
    """Mixin to require staff status"""
    
    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class SuperuserRequiredMixin(LoginRequiredMixin):
    """Mixin to require superuser status"""
    
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


def handle_ajax_response(view_func):
    """Decorator to handle AJAX responses consistently"""
    from functools import wraps
    from django.http import JsonResponse
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"AJAX error in {view_func.__name__}: {str(e)}")
            return JsonResponse({
                'status': 'error', 
                'message': 'An error occurred processing your request'
            })
    return wrapper