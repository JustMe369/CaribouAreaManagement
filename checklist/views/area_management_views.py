from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from ..models import Area, Store

def area_management(request):
    """Main area management view"""
    areas = Area.objects.all().prefetch_related('stores')
    return render(request, 'checklist/area_management.html', {
        'areas': areas
    })

def assign_store_to_area(request, area_id):
    """Assign a store to an area"""
    area = Area.objects.get(id=area_id)
    
    if request.method == 'POST':
        store_id = request.POST.get('store_id')
        if store_id:
            store = Store.objects.get(id=store_id)
            store.area = area
            store.save()
            messages.success(request, f'Successfully assigned {store.name} to {area.name}')
        return redirect('checklist:area_management')
    
    # Get stores that are not assigned to this area
    available_stores = Store.objects.filter(area__isnull=True) | Store.objects.exclude(area=area)
    return render(request, 'checklist/assign_store_to_area.html', {
        'area': area,
        'available_stores': available_stores
    })

def assign_user_to_area(request, area_id):
    """Assign a user to an area"""
    area = Area.objects.get(id=area_id)
    User = get_user_model()
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            user = User.objects.get(id=user_id)
            if hasattr(user, 'profile'):
                user.profile.areas.add(area)
                messages.success(request, f'Successfully assigned {user.get_full_name() or user.username} to {area.name}')
        return redirect('checklist:area_management')
    
    # Get users that are not assigned to this area
    available_users = User.objects.filter(profile__role__in=['area_manager', 'store_manager']).exclude(profile__areas=area)
    return render(request, 'checklist/assign_user_to_area.html', {
        'area': area,
        'available_users': available_users
    })

def assign_users_to_area(request, area_id):
    """Legacy function - assign multiple users to an area (for admin)"""
    area = Area.objects.get(id=area_id)
    User = get_user_model()
    
    if request.method == 'POST':
        user_ids = request.POST.getlist('users')
        for user in User.objects.filter(id__in=user_ids):
            if hasattr(user, 'profile'):
                user.profile.areas.add(area)
                messages.success(request, f'Successfully added users to {area.name}')
        return redirect('admin:checklist_area_changelist')
    
    users = User.objects.filter(profile__role__in=['area_manager', 'store_manager'])
    return render(request, 'admin/checklist/assign_users_to_area.html', {
        'area': area,
        'users': users
    })