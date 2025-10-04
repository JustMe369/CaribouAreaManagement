from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django import forms
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile Details'
    filter_horizontal = ('stores', 'areas')  # Add areas to filter_horizontal
    
    fieldsets = (
        ('Role Configuration', {
            'fields': ('role',),
            'classes': ('collapse',)
        }),
        ('Store Access', {
            'fields': ('stores',),
            'description': 'Select stores this user can access',
            'classes': ('collapse',)
        }),
        ('Area Access', {
            'fields': ('areas',),
            'description': 'Select areas this user can manage (Area Managers only)',
            'classes': ('collapse',)
        }),
    )

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj and obj.profile.role != 'area_manager':
            formset.form.base_fields['areas'].disabled = True
        return formset

class CustomUserAdminForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple(
            _('Groups'),
            False,
            attrs={'class': 'group-selector'}
        ),
        required=False,
        help_text=_('Hold down "Control" or "Command" to select multiple groups.')
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions', 'last_login', 'date_joined')

class CustomUserAdmin(UserAdmin):
    form = CustomUserAdminForm
    inlines = (ProfileInline,)
    
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'is_active',
        'is_staff',
        'get_role',
        'get_groups',
        'last_login',
        'user_actions'
    )
    
    list_filter = (
        'is_staff', 
        'is_superuser', 
        'is_active', 
        'groups',
        'profile__role'
    )
    
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__role')
    
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else '—'
    get_role.short_description = _('Role')
    get_role.admin_order_field = 'profile__role'

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = _('Groups')

    def user_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">View Logs</a>&nbsp;'
            '<a class="button" href="{}">Impersonate</a>',
            reverse('admin:auth_user_logs', args=[obj.pk]),
            reverse('admin:impersonate_start', args=[obj.pk]),
        )
    user_actions.short_description = _('Actions')
    user_actions.allow_tags = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')

    def get_inline_instances(self, request, obj=None):
        return super().get_inline_instances(request, obj) if obj else []

    class Media:
        css = {
            'all': ('admin/css/user_admin.css',)
        }
        js = (
            'admin/js/user_admin.js',
        )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_role_display', 'display_stores', 'display_areas')
    filter_horizontal = ('stores', 'areas',)

    def display_stores(self, obj):
        return ", ".join([store.name for store in obj.stores.all()])
    display_stores.short_description = 'Stores'

    def display_areas(self, obj):
        return ", ".join([area.name for area in obj.areas.all()])
    display_areas.short_description = 'Areas'

admin.site.register(Profile, ProfileAdmin)