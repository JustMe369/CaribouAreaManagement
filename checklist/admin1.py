from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.models import User, Group
from .models import (
    Store, AreaManagerVisit, ChecklistItem, ActionPlanItem, 
    ChecklistCategory, ChecklistQuestion, MaintenanceTicket,
    EquipmentCategory, Product, Area
)

class CaribouAdminSite(AdminSite):
    """Custom admin site for Caribou Coffee Area Manager"""
    site_header = "Caribou Coffee Area Manager Admin"
    site_title = "Caribou Coffee Admin"
    index_title = "Welcome to Caribou Coffee Management System"
    enable_nav_sidebar = True
    
    def each_context(self, request):
        context = super().each_context(request)
        context['available_apps'] = self.get_app_list(request)
        return context
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='admin_dashboard'),
            path('history/', self.admin_view(self.checklist_history), name='history'),  # Changed from admin_history to history
            path('api/stats/', self.admin_view(self.api_stats), name='admin_api_stats'),
            path('api/chart-data/', self.admin_view(self.api_chart_data), name='admin_api_chart_data'),
        ]
        return custom_urls + urls

    def checklist_history(self, request):
        """Admin history view that redirects to the checklist history"""
        from django.shortcuts import redirect
        return redirect('checklist:checklist_history')

    def dashboard_view(self, request):
        """Custom dashboard view with comprehensive analytics"""
        context = {
            'title': 'Admin Dashboard',
            'total_stores': Store.objects.filter(is_active=True).count(),
            'total_visits': AreaManagerVisit.objects.filter(is_draft=False).count(),
            'open_actions': ActionPlanItem.objects.filter(status='open').count(),
            'recent_visits': AreaManagerVisit.objects.filter(is_draft=False).order_by('-date')[:5],
            'pending_actions': ActionPlanItem.objects.filter(status='open').order_by('-created_at')[:10],
            'stores_with_recent_visits': Store.objects.filter(
                visits__date__gte=timezone.now() - timedelta(days=30)
            ).distinct().count(),
            'open_maintenance_tickets': MaintenanceTicket.objects.exclude(status='C').count(),
            'avg_compliance': self.get_average_compliance(),
            'category_performance': self.get_category_performance(),
        }
        return render(request, 'admin/dashboard.html', context)
    
    def api_stats(self, request):
        """API endpoint for real-time statistics"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        stats = {
            'total_stores': Store.objects.filter(is_active=True).count(),
            'total_visits': AreaManagerVisit.objects.filter(is_draft=False).count(),
            'visits_this_month': AreaManagerVisit.objects.filter(
                date__gte=thirty_days_ago, is_draft=False
            ).count(),
            'open_actions': ActionPlanItem.objects.filter(status='open').count(),
            'avg_compliance': self.get_average_compliance(),
            'stores_visited_this_month': Store.objects.filter(
                visits__date__gte=thirty_days_ago,
                visits__is_draft=False
            ).distinct().count(),
        }
        return JsonResponse(stats)
    
    def api_chart_data(self, request):
        """API endpoint for chart data"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Daily visits for the last 30 days
        daily_visits = []
        current_date = thirty_days_ago
        while current_date <= timezone.now():
            visits_count = AreaManagerVisit.objects.filter(
                date=current_date.date(), is_draft=False
            ).count()
            daily_visits.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'visits': visits_count
            })
            current_date += timedelta(days=1)
        
        # Category performance data
        category_data = ChecklistItem.objects.filter(
            visit__is_draft=False
        ).values('question__category__name').annotate(
            total=Count('id'),
            compliant=Count('id', filter=Q(answer=True))
        ).order_by('question__category__name')
        
        chart_data = {
            'daily_visits': daily_visits,
            'category_performance': list(category_data)
        }
        return JsonResponse(chart_data)
    
    def get_category_performance(self):
        """Calculate performance for each checklist category."""
        category_data = ChecklistItem.objects.filter(
            visit__is_draft=False
        ).values('question__category__name').annotate(
            total=Count('id'),
            compliant=Count('id', filter=Q(answer=True))
        ).order_by('question__category__name')

        for item in category_data:
            item['compliance'] = round((item['compliant'] / item['total']) * 100) if item['total'] > 0 else 0

        return category_data

    def get_average_compliance(self):
        """Calculate average compliance rate across all visits"""
        visits = list(AreaManagerVisit.objects.filter(is_draft=False))
        if not visits:
            return 0
        
        total_score = sum(visit.calculate_score() for visit in visits)
        return round(total_score / len(visits), 1)


# Create custom admin site instance
caribou_admin_site = CaribouAdminSite(name='caribou_admin')


class StoreAdmin(admin.ModelAdmin):
    """Enhanced Store Admin with comprehensive features"""
    list_display = [
        'name', 'area', 'manager_name', 'phone', 'email', 'is_active',
        'last_visit_date', 'compliance_score', 'action_items_count',
        'display_equipment_categories', 'visit_frequency', 'maintenance_status'
    ]
    list_per_page = 25
    save_on_top = True
    show_full_result_count = False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(visits__user=request.user).distinct()
    
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        return obj.visits.filter(user=request.user).exists()
    
    actions = ['export_as_csv', 'activate_stores', 'deactivate_stores']
    
    def export_as_csv(self, request, queryset):
        """Export selected stores to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="stores_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Manager', 'Phone', 'Email', 'Active', 'Last Visit', 'Compliance Score'])
        
        for store in queryset:
            writer.writerow([
                store.name,
                store.manager_name,
                store.phone,
                store.email,
                store.is_active,
                store.last_visit_date(),
                store.compliance_score()
            ])
        return response
    export_as_csv.short_description = 'Export selected stores to CSV'
    
    def activate_stores(self, request, queryset):
        """Activate selected stores"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} store(s) activated.')
    activate_stores.short_description = 'Activate selected stores'
    
    def deactivate_stores(self, request, queryset):
        """Deactivate selected stores"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} store(s) deactivated.')
    deactivate_stores.short_description = 'Deactivate selected stores'
    filter_horizontal = ('equipment_categories',)
    change_list_template = 'admin/store_management.html'
    
    def visit_frequency(self, obj):
        """Calculate average visits per month"""
        visits = obj.visits.filter(is_draft=False).count()
        if visits > 0:
            first_visit = obj.visits.earliest('date').date
            months = (timezone.now().date() - first_visit).days // 30
            return f"{visits/max(months,1):.1f}/month"
        return "No visits"
    visit_frequency.short_description = 'Visit Frequency'
    
    def maintenance_status(self, obj):
        """Show maintenance ticket status summary"""
        try:
            tickets = MaintenanceTicket.objects.filter(visit__store=obj)
            pending = tickets.filter(status='N').count()
            in_progress = tickets.filter(status='IP').count()
            overdue = tickets.filter(status__in=['N','IP'], due_date__lt=timezone.now().date()).count()
            return format_html(
                '<span class="badge bg-danger">{}</span> '
                '<span class="badge bg-warning">{}</span> '
                '<span class="badge bg-secondary">{}</span>',
                pending, in_progress, overdue
            )
        except Exception:
            return "-"
    maintenance_status.short_description = 'Maintenance'

    def display_equipment_categories(self, obj):
        return ", ".join([c.name for c in obj.equipment_categories.all()])
    display_equipment_categories.short_description = 'Equipment Categories'
    list_filter = ['is_active', 'area']
    search_fields = ['name', 'manager_name', 'email', 'phone', 'area__name']
    list_editable = ['is_active', 'area']
    ordering = ['name']
    
    fieldsets = (
        ('Store Information', {
            'fields': ('name', 'manager_name', 'phone', 'email')
        }),
        ('Address Details', {
            'fields': ('address',)
        }),
        ('Status & Settings', {
            'fields': ('is_active',)
        })
    )
    
    def last_visit_date(self, obj):
        """Display last visit date"""
        last_visit = obj.visits.filter(is_draft=False).first()
        if last_visit:
            return format_html(
                '<span style="color: #28a745;">{}</span>',
                last_visit.date.strftime('%b %d, %Y')
            )
        return format_html('<span style="color: #6c757d;">No visits</span>')
    last_visit_date.short_description = 'Last Visit'
    
    def compliance_score(self, obj):
        """Display average compliance score"""
        visits = obj.visits.filter(is_draft=False)
        if not visits.exists():
            return format_html('<span style="color: #6c757d;">N/A</span>')
        
        avg_score = sum(visit.calculate_score() for visit in visits) / visits.count()
        color = '#28a745' if avg_score >= 80 else '#ffc107' if avg_score >= 60 else '#dc3545'
        return format_html('<span style="color: {};">{}</span>', color, f'{avg_score:.1f}%')
    compliance_score.short_description = 'Avg Compliance'
    
    def action_items_count(self, obj):
        """Display count of open action items"""
        count = ActionPlanItem.objects.filter(
            visit__store=obj, status='open'
        ).count()
        if count > 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">{}</span>',
                count
            )
        return format_html('<span style="color: #28a745;">0</span>')
    action_items_count.short_description = 'Open Actions'


class AreaManagerVisitAdmin(admin.ModelAdmin):
    """Enhanced Visit Admin with advanced filtering and actions"""
    list_display = [
        'store', 'manager', 'date', 'month', 'calculate_score_display', 
        'is_draft', 'total_items', 'compliant_items', 'created_at'
    ]
    list_per_page = 25
    save_on_top = True
    show_full_result_count = False
    list_filter = ['date', 'is_draft', 'month', 'store']
    search_fields = ['store__name', 'manager__username', 'month']
    list_editable = ['is_draft']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    actions = ['mark_as_complete', 'export_visit_summary']
    
    fieldsets = (
        ('Visit Information', {
            'fields': ('store', 'manager', 'month')
        }),
        ('Visit Details', {
            'fields': ('general_notes', 'is_draft')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['date', 'created_at', 'updated_at']
    
    def calculate_score_display(self, obj):
        """Display compliance score with color coding"""
        score = obj.calculate_score()
        if score >= 90:
            color = '#28a745'
            badge = '🟢'
        elif score >= 75:
            color = '#ffc107'
            badge = '��'
        elif score >= 60:
            color = '#fd7e14'
            badge = '🟠'
        else:
            color = '#dc3545'
            badge = '🔴'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}%</span>',
            color, badge, score
        )
    calculate_score_display.short_description = 'Compliance Score'
    
    def total_items(self, obj):
        """Display total checklist items"""
        return obj.checklist_items.count()
    total_items.short_description = 'Total Items'
    
    def compliant_items(self, obj):
        """Display compliant items count"""
        compliant = obj.checklist_items.filter(answer=True).count()
        total = obj.checklist_items.count()
        if total > 0:
            percentage = (compliant / total) * 100
            return format_html('{} / {} ({})', compliant, total, f'{percentage:.0f}%')
        return '0 / 0'
    compliant_items.short_description = 'Compliant Items'
    
    def mark_as_complete(self, request, queryset):
        """Mark selected visits as complete"""
        updated = queryset.update(is_draft=False)
        self.message_user(request, f'{updated} visit(s) marked as complete.')
    mark_as_complete.short_description = 'Mark selected visits as complete'
    
    def export_visit_summary(self, request, queryset):
        """Export visit summary"""
        self.message_user(request, 'Export functionality to be implemented.')
    export_visit_summary.short_description = 'Export visit summary'


class ChecklistItemAdmin(admin.ModelAdmin):
    """Enhanced Checklist Item Admin"""
    list_display = [
        'visit', 'get_category', 'get_question_number', 'get_question_text_preview', 
        'answer_display', 'answer', 'requires_follow_up', 'comment_preview'
    ]
    list_filter = ['question__category', 'answer', 'requires_follow_up', 'visit__date']
    search_fields = ['visit__store__name', 'question__category__name', 'question__text']
    list_editable = ['answer', 'requires_follow_up']
    ordering = ['-visit__date', 'question__category', 'question__number']

    def get_category(self, obj):
        return obj.question.category.name
    get_category.short_description = 'Category'
    get_category.admin_order_field = 'question__category'

    def get_question_number(self, obj):
        return obj.question.number
    get_question_number.short_description = 'Q#'
    get_question_number.admin_order_field = 'question__number'

    def get_question_text_preview(self, obj):
        """Display preview of question text"""
        return obj.question.text[:50] + '...' if len(obj.question.text) > 50 else obj.question.text
    get_question_text_preview.short_description = 'Question'
    
    def comment_preview(self, obj):
        """Display preview of comment"""
        if obj.comment:
            return obj.comment[:30] + '...' if len(obj.comment) > 30 else obj.comment
        return '-'
    comment_preview.short_description = 'Comment'
    
    def answer_display(self, obj):
        """Display answer with visual indicator"""
        if obj.answer:
            return format_html('<span style="color: #28a745;">✅ Yes</span>')
        return format_html('<span style="color: #dc3545;">❌ No</span>')
    answer_display.short_description = 'Answer'


class ActionPlanItemAdmin(admin.ModelAdmin):
    """Enhanced Action Plan Item Admin"""
    list_display = [
        'visit', 'issue_description_preview', 'who', 
        'timeframe', 'status_display', 'status', 'priority_display', 'priority', 'created_at'
    ]
    list_filter = ['status', 'priority', 'timeframe', 'created_at']
    search_fields = ['what', 'who', 'visit__store__name']
    list_editable = ['status', 'priority']
    date_hierarchy = 'timeframe'
    ordering = ['-created_at']
    
    actions = ['mark_as_completed', 'mark_as_in_progress']
    
    fieldsets = (
        ('Action Item Details', {
            'fields': ('visit', 'what', 'remarks')
        }),
        ('Assignment', {
            'fields': ('who', 'timeframe')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def issue_description_preview(self, obj):
        """Display preview of issue description"""
        return obj.what[:60] + '...' if len(obj.what) > 60 else obj.what
    issue_description_preview.short_description = 'Issue Description'
    
    def status_display(self, obj):
        """Display status with color coding"""
        status_map = {'N': 'New', 'IP': 'In Progress', 'C': 'Closed'}
        colors = {'N': '#dc3545', 'IP': '#ffc107', 'C': '#28a745'}
        status_text = status_map.get(obj.status, obj.status)
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#6c757d'), status_text
        )
    status_display.short_description = 'Status'
    
    def priority_display(self, obj):
        """Display priority with visual indicator"""
        indicators = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        return format_html(
            '<span style="font-weight: bold;">{} {}</span>',
            indicators.get(obj.priority, '⚪'), obj.priority
        )
    priority_display.short_description = 'Priority'
    
    def mark_as_completed(self, request, queryset):
        """Mark selected action items as completed"""
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} action item(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected items as completed'
    
    def mark_as_in_progress(self, request, queryset):
        """Mark selected action items as in progress"""
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} action item(s) marked as in progress.')
    mark_as_in_progress.short_description = 'Mark selected items as in progress'


class ChecklistCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'description')
    list_editable = ('active',)
    list_filter = ('active',)
    search_fields = ('name',)
    list_per_page = 25
    save_on_top = True
    show_full_result_count = False


class ChecklistQuestionAdmin(admin.ModelAdmin):
    list_display = ('number', 'text', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('text', 'category__name')
    list_editable = ('is_active',)
    list_per_page = 25
    save_on_top = True
    show_full_result_count = False
    actions = ['export_questions', 'import_questions']
    
    def export_questions(self, request, queryset):
        """Export selected questions to CSV with improved error handling"""
        try:
            from django.http import HttpResponse
            import csv
            from io import StringIO
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="checklist_questions_export.csv"'
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Question Number', 'Category', 'Question Text', 'Is Active'])
            
            # Write data
            for question in queryset:
                writer.writerow([
                    question.number,
                    question.category.name if question.category else '',
                    question.text,
                    'Yes' if question.is_active else 'No'
                ])
                
            # Get CSV data from memory buffer
            csv_data = output.getvalue()
            output.close()
            
            response.write(csv_data)
            return response
            
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Error exporting questions: {str(e)}')
            return HttpResponseRedirect(request.path_info)
    
    def import_questions(self, request, queryset=None):
        """Import questions from CSV with improved error handling"""
        from django.shortcuts import render
        from django import forms
        from django.contrib import messages
        
        class ImportForm(forms.Form):
            file = forms.FileField(
                label='CSV File',
                help_text='File must contain columns: Question Number, Category, Question Text, Is Active'
            )
            
        if request.method == 'POST':
            form = ImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    import csv
                    from io import TextIOWrapper
                    from django.db import transaction
                    from ..models import ChecklistQuestion, ChecklistCategory
                    
                    with transaction.atomic():
                        file = TextIOWrapper(request.FILES['file'].file, encoding=request.encoding)
                        reader = csv.DictReader(file)
                        
                        for row in reader:
                            # Validate required fields
                            if not all(key in row for key in ['Question Number', 'Category', 'Question Text', 'Is Active']):
                                raise ValueError('Invalid CSV format - missing required columns')
                                
                            # Get or create category
                            category, _ = ChecklistCategory.objects.get_or_create(name=row['Category'].strip())
                            
                            # Create question
                            ChecklistQuestion.objects.create(
                                number=row['Question Number'],
                                category=category,
                                text=row['Question Text'],
                                is_active=row['Is Active'].lower() in ('true', 'yes', '1')
                            )
                        
                    messages.success(request, 'Questions imported successfully!')
                    
                except Exception as e:
                    messages.error(request, f'Error importing questions: {str(e)}')
        else:
            form = ImportForm()
            
        return render(request, 'admin/checklist/import_questions.html', {
            'form': form,
            'title': 'Import Questions'
        })
    
    import_questions.short_description = 'Import questions from CSV'


class MaintenanceTicketAdmin(admin.ModelAdmin):
    list_display = [
        'visit', 'equipment', 'priority_display', 'status_display', 
        'due_date', 'is_overdue'
    ]
    list_per_page = 25
    save_on_top = True
    show_full_result_count = False
    list_filter = ['priority', 'status', ('due_date', admin.DateFieldListFilter)]
    search_fields = ['equipment', 'visit__store__name']
    raw_id_fields = ['visit']
    
    actions = ['mark_as_completed', 'mark_as_in_progress']
    def priority_display(self, obj):
        """Display priority with visual indicator"""
        indicators = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        return format_html(
            '<span style="font-weight: bold;">{} {}</span>',
            indicators.get(obj.priority, '⚪'), obj.get_priority_display()
        )
    priority_display.short_description = 'Priority'

    def status_display(self, obj):
        """Display status with color coding"""
        if obj.status == 'completed':
            color = '#28a745'
        elif obj.status == 'in_progress':
            color = '#ffc107'
        else:  # pending
            color = '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def is_overdue_display(self, obj):
        if obj.due_date and obj.status != 'completed' and obj.due_date < timezone.now().date():
            return format_html('<span style="color: #dc3545;">Yes</span>')
        return 'No'
    is_overdue_display.short_description = 'Overdue'
    is_overdue_display.admin_order_field = 'due_date'

    def mark_as_completed(self, request, queryset):
        """Mark selected maintenance tickets as completed"""
        updated = queryset.update(status='completed', closed_date=timezone.now())
        self.message_user(request, f'{updated} maintenance ticket(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected tickets as completed'

    def mark_as_in_progress(self, request, queryset):
        """Mark selected maintenance tickets as in progress"""
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} maintenance ticket(s) marked as in progress.')
    mark_as_in_progress.short_description = 'Mark selected tickets as in progress'


class StoreInline(admin.TabularInline):
    model = Store
    extra = 0
    fields = ('name', 'manager_name', 'is_active')
    readonly_fields = ('name', 'manager_name')
    can_delete = False
    show_change_link = True

class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'store_count']
    search_fields = ['name']
    inlines = [StoreInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(store_count=Count('stores'))

    def store_count(self, obj):
        return obj.store_count
    store_count.short_description = 'Stores'
    store_count.admin_order_field = 'store_count'

# Register models with both admin sites
admin.site.register(Area, AreaAdmin)  
caribou_admin_site.register(Area, AreaAdmin)

# Register models with both admin sites
admin.site.register(Store, StoreAdmin)
admin.site.register(EquipmentCategory)
admin.site.register(ChecklistQuestion, ChecklistQuestionAdmin)
admin.site.register(MaintenanceTicket, MaintenanceTicketAdmin)
if not admin.site.is_registered(User):
    admin.site.register(User)
caribou_admin_site.register(ChecklistQuestion, ChecklistQuestionAdmin)
caribou_admin_site.register(MaintenanceTicket, MaintenanceTicketAdmin)
if not caribou_admin_site.is_registered(User):
    caribou_admin_site.register(User)
if not caribou_admin_site.is_registered(Group):
    caribou_admin_site.register(Group)
    
    def store_count(self, obj):
        return obj.stores.count()
    store_count.short_description = 'Stores'
    
    def user_count(self, obj):
        return obj.profile_set.count()
    user_count.short_description = 'Users'

# Register models with both admin sites
admin.site.register(Area, AreaAdmin)
caribou_admin_site.register(Area, AreaAdmin)  # Remove this duplicate registration:
# admin.site.register(Area, AreaAdmin)
# caribou_admin_site.register(Area, AreaAdmin)  # Keep this if you need custom admin site registration

def priority_display(self, obj):
    return obj.get_priority_display()
priority_display.short_description = 'Priority'

def is_overdue(self, obj):
    if obj.status != 'C' and obj.due_date and obj.due_date < timezone.now().date():
        return format_html('<span style="color: #dc3545;">Overdue</span>')
    return format_html('<span style="color: #28a745;">On Time</span>')
is_overdue.short_description = 'Overdue Status'

def status_display(self, obj):
    """Display status with color coding"""
    status_map = {'N': 'New', 'IP': 'In Progress', 'C': 'Closed'}
    colors = {'N': '#dc3545', 'IP': '#ffc107', 'C': '#28a745'}
    status_text = status_map.get(obj.status, obj.status)
    return format_html(
        '<span style="color: {}; font-weight: bold;">{}</span>',
        colors.get(obj.status, '#6c757d'), status_text
    )
status_display.short_description = 'Status'

def mark_as_completed(self, request, queryset):
    """Mark selected maintenance tickets as completed"""
    updated = queryset.update(status='C', closed_date=timezone.now())
    self.message_user(request, f'{updated} maintenance ticket(s) marked as completed.')
mark_as_completed.short_description = 'Mark selected tickets as completed'

def mark_as_in_progress(self, request, queryset):
    """Mark selected maintenance tickets as in progress"""
    updated = queryset.update(status='IP')
    self.message_user(request, f'{updated} maintenance ticket(s) marked as in progress.')
mark_as_in_progress.short_description = 'Mark selected tickets as in progress'


# Register models with both admin sites
admin.site.register(Store, StoreAdmin)
admin.site.register(EquipmentCategory)
admin.site.register(Product)
admin.site.register(AreaManagerVisit, AreaManagerVisitAdmin)
admin.site.register(ChecklistItem, ChecklistItemAdmin)
admin.site.register(ActionPlanItem, ActionPlanItemAdmin)
admin.site.register(ChecklistCategory, ChecklistCategoryAdmin)
admin.site.register(ChecklistQuestion, ChecklistQuestionAdmin)
admin.site.register(MaintenanceTicket, MaintenanceTicketAdmin)
if not admin.site.is_registered(User):
    admin.site.register(User)
if not admin.site.is_registered(Group):
    admin.site.register(Group)

# Also register with custom admin site
caribou_admin_site.register(Store, StoreAdmin)
caribou_admin_site.register(EquipmentCategory)
caribou_admin_site.register(Product)
caribou_admin_site.register(AreaManagerVisit, AreaManagerVisitAdmin)
caribou_admin_site.register(ChecklistItem, ChecklistItemAdmin)
caribou_admin_site.register(ActionPlanItem, ActionPlanItemAdmin)
caribou_admin_site.register(ChecklistCategory, ChecklistCategoryAdmin)
caribou_admin_site.register(ChecklistQuestion, ChecklistQuestionAdmin)
caribou_admin_site.register(MaintenanceTicket, MaintenanceTicketAdmin)
if not caribou_admin_site.is_registered(User):
    caribou_admin_site.register(User)
if not caribou_admin_site.is_registered(Group):
    caribou_admin_site.register(Group)


class StoreAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'area_link', 'manager_name', 'phone', 'email', 'is_active',
        'last_visit_date', 'compliance_score', 'action_items_count'
    ]
    list_filter = ['area', 'is_active']
    
    def area_link(self, obj):
        if obj.area:
            return format_html('<a href="{}">{}</a>', 
                f'/admin/checklist/area/{obj.area.id}/change/', 
                obj.area.name)
        return "-"
    area_link.short_description = 'Area'
    area_link.admin_order_field = 'area'