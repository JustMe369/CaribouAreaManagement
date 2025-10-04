from django.urls import path
from .views import manage_users, profile_view, settings_view, help_view

urlpatterns = [
    path('manage/', manage_users, name='manage_users'),
    path('profile/', profile_view, name='profile'),
    path('settings/', settings_view, name='settings'),
    path('help/', help_view, name='help'),
]