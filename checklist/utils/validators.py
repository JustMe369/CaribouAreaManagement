"""
Validation utilities for the checklist application
"""
import logging
from django.core.exceptions import ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)


def validate_store_access(user, store_id):
    """
    Validate that user has access to the specified store
    """
    from checklist.models import Store
    
    if not hasattr(user, 'profile'):
        raise ValidationError("User profile not set up")
    
    store = Store.objects.filter(id=store_id, is_active=True).first()
    if not store:
        raise ValidationError("Store not found or inactive")
    
    profile = user.profile
    if profile.role in ['admin', 'area_management', 'store_selector']:
        return store
    
    if store not in profile.stores.all():
        raise ValidationError("You don't have access to this store")
    
    return store


def validate_checklist_data(data):
    """
    Validate checklist submission data
    """
    required_fields = ['store', 'month', 'day']
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate month format
    month = data.get('month', '') # type: ignore
    if not any(char.isdigit() for char in month):
        raise ValidationError("Month must include a year")
    
    return True


def validate_file_upload(file):
    """
    Validate file uploads for attachments
    """
    max_size = 10 * 1024 * 1024  # 10MB
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
    
    if file.size > max_size:
        raise ValidationError(f"File size must be under {max_size // (1024*1024)}MB")
    
    if file.content_type not in allowed_types:
        raise ValidationError("File type not allowed. Please upload images or PDFs")
    
    return True