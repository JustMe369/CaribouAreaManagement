from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Profile
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.contrib.auth import get_user_model

# Create your views here.
def home_page(request):
    return HttpResponse("""
        <h1>Welcome to Caribou Coffee Dashboard</h1>
        <p>Your project is set up successfully!</p>
        <ul>
            <li><a href="/admin/">Admin Panel</a></li>
            <li><a href="/checklist/new/">New Checklist Form</a></li>
            <li><a href="/profile/">My Profile</a></li>
        </ul>
    """)
@user_passes_test(lambda u: u.is_superuser)
def manage_users(request):
    users = get_user_model().objects.all().select_related('profile')
    return render(request, 'users/manage_users.html', {'users': users})
from .models import Profile

@login_required
def profile_view(request):
    profile = request.user.profile
    roles = Profile.ROLE_CHOICES
    return render(request, 'users/profile_enhanced.html', {
        'profile': profile,
        'roles': roles
    })
    context = {
        'profile': profile,
        'stores': profile.stores.all(),
        'role_display': profile.get_role_display()
    }
    return render(request, 'users/profile.html', context)

@login_required
def settings_view(request):
    """User settings page stub (extend with forms for password, preferences, etc.)."""
    profile = request.user.profile if hasattr(request.user, 'profile') else None
    return render(request, 'users/settings.html', {
        'profile': profile,
        'user': request.user,
    })

@login_required
def help_view(request):
    """Basic help/FAQ page."""
    return render(request, 'users/help.html')