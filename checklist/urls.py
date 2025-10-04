from django.urls import path
from . import views
from .views.data_export_views import import_questions, export_data, export_visit_excel, export_history_excel
from .views.checklist_views import print_visit_report
from .views.dashboard_views import dashboard, manage_checklist_questions, edit_checklist_question
from .views.checklist_views import (
    new_checklist, checklist_success, checklist_history, 
    checklist_detail, save_draft, load_draft, delete_draft
)
from .views.action_plan_views import (
    action_plan, update_action_item, bulk_update_actions,
    bulk_update_action_items_form
)
from .views.maintenance_views import (
    NewMaintenanceView, edit_maintenance, maintenance_list
)
from .views.store_views import (
    store_management, edit_store, toggle_store_status, store_list, store_detail
)
from .views.area_management_views import area_management, assign_store_to_area, assign_user_to_area
from .views.reports_views import reports
from django.views.generic.base import RedirectView

app_name = 'checklist'

urlpatterns = [
    path('', RedirectView.as_view(url='dashboard/'), name='checklist_root'),
    # Main Dashboard & Checklist Flow
    path('dashboard/', dashboard, name='dashboard'),
    path('manage-questions/', manage_checklist_questions, name='manage_checklist_questions'),
    path('edit-question/<int:question_id>/', edit_checklist_question, name='edit_checklist_question'),
    path('new/', new_checklist, name='new_checklist'),
    path('success/', checklist_success, name='checklist_success'),
    path('history/', checklist_history, name='checklist_history'),
    path('<int:visit_id>/', checklist_detail, name='checklist_detail'),
    path('import-data/', import_questions, name='import_data'),
    path('export-data/', export_data, name='export_data'),
    path('export-visit-excel/<int:visit_id>/', export_visit_excel, name='export_visit_excel'),
    path('export-history-excel/', export_history_excel, name='export_history_excel'),
    path('print-visit-report/<int:visit_id>/', print_visit_report, name='print_visit_report'),
    
    # Draft Handling
    path('draft/save/', save_draft, name='save_draft'),
    path('draft/load/<int:draft_id>/', load_draft, name='load_draft'),
    path('draft/delete/<int:draft_id>/', delete_draft, name='delete_draft'),
    
    # Action Plan Management
    path('action-plan/', action_plan, name='action_plan'),
    path('action-plan/bulk-update/', bulk_update_action_items_form, name='bulk_update_action_items'),
    path('action-plan/bulk-update-ajax/', bulk_update_actions, name='bulk_update_actions_ajax'),
    path('action-plan/<int:item_id>/update/', update_action_item, name='update_action_item'),
    
    # Maintenance Management
    path('maintenance/', maintenance_list, name='maintenance_list'),
    path('maintenance/new/', views.new_maintenance, name='new_maintenance'),
    path('maintenance/new/<int:visit_id>/', NewMaintenanceView.as_view(), name='new_maintenance_with_visit'),
    path('maintenance/<int:ticket_id>/', views.maintenance_detail, name='maintenance_detail'),
    path('maintenance/<int:ticket_id>/edit/', edit_maintenance, name='edit_maintenance'),
    
    # Store Management
    path('stores/', store_management, name='store_management'),
    path('stores/<int:store_id>/edit/', edit_store, name='edit_store'),
    path('stores/<int:store_id>/toggle-status/', toggle_store_status, name='toggle_store_status'),
    
    # User-facing Stores
    path('my-stores/', store_list, name='store_list'),
    path('my-stores/<int:store_id>/', store_detail, name='store_detail'),
    
    path('manage-questions/', manage_checklist_questions, name='manage_checklist_questions'),
    path('edit-question/<int:question_id>/', edit_checklist_question, name='edit_checklist_question'),
    # Area Management
    path('area-management/', area_management, name='area_management'),
    path('area-management/assign-store/<int:area_id>/', assign_store_to_area, name='assign_store_to_area'),
    path('area-management/assign-user/<int:area_id>/', assign_user_to_area, name='assign_user_to_area'),

    # Reports
    path('reports/', reports, name='reports'),

    # API Endpoints
    # Note: get_dashboard_stats was not in your original views - you can add it if needed
    # path('api/stats/', get_dashboard_stats, name='get_dashboard_stats'),
]