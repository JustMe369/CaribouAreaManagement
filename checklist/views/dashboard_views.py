from django.db.models import Avg, Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import timedelta
import logging

from ..models import (
    AreaManagerVisit, ActionPlanItem, ChecklistItem,
    MaintenanceTicket, Store, ChecklistQuestion, ChecklistCategory
)
from ..forms import ChecklistQuestionForm
from .base import BaseViewMixin

logger = logging.getLogger(__name__)

@login_required
def manage_checklist_questions(request):
    """Enhanced checklist question management with pagination"""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('checklist:dashboard')
    
    try:
        questions = ChecklistQuestion.objects.all()\
            .select_related('category')\
            .order_by('category__name', 'number')
            
        categories = ChecklistCategory.objects.filter(active=True)
        
        if request.method == 'POST':
            form = ChecklistQuestionForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Question added successfully!')
                return redirect('checklist:manage_checklist_questions')
        else:
            form = ChecklistQuestionForm()
        
        context = {
            'questions': questions,
            'categories': categories,
            'form': form,
        }
        return render(request, 'checklist/manage_questions.html', context)
    
    except Exception as e:
        logger.error(f"Error managing checklist questions: {str(e)}")
        messages.error(request, "An error occurred while loading questions.")
        return redirect('checklist:dashboard')

@login_required
def edit_checklist_question(request, question_id):
    """Enhanced question editing with validation"""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('checklist:dashboard')
    
    try:
        question = get_object_or_404(ChecklistQuestion, id=question_id)
        
        if request.method == 'POST':
            form = ChecklistQuestionForm(request.POST, instance=question)
            if form.is_valid():
                form.save()
                messages.success(request, 'Question updated successfully!')
                return redirect('checklist:manage_checklist_questions')
        else:
            form = ChecklistQuestionForm(instance=question)
        
        context = {
            'form': form,
            'question': question,
        }
        return render(request, 'checklist/edit_question.html', context)
    
    except Exception as e:
        logger.error(f"Error editing checklist question: {str(e)}")
        messages.error(request, "An error occurred while editing the question.")
        return redirect('checklist:manage_checklist_questions')

class DashboardManager(BaseViewMixin):
    """Enhanced dashboard analytics manager"""
    
    @staticmethod
    def get_category_performance(user):
        """Return list of per-category compliance for the user's visits."""
        qs = ChecklistItem.objects.filter(
            visit__manager=user,
            visit__is_draft=False
        ).values('question__category__name').annotate(
            total=Count('id'),
            compliant=Count('id', filter=Q(answer=True))
        ).order_by('question__category__name')
        data = []
        for row in qs:
            total = row['total'] or 0
            compliant = row['compliant'] or 0
            pct = round((compliant / total) * 100, 1) if total else 0
            data.append({
                'name': row['question__category__name'] or 'Uncategorized',
                'total': total,
                'compliant': compliant,
                'compliance': pct,
            })
        return data
    
    @staticmethod
    def get_basic_stats(user):
        """Get basic dashboard statistics with error handling"""
        try:
            today = timezone.now().date()
            thirty_days_ago = today - timedelta(days=30)
            
            total_visits = AreaManagerVisit.objects.filter(
                manager=user, 
                is_draft=False
            ).count()
            
            recent_visits = AreaManagerVisit.objects.filter(
                manager=user, 
                is_draft=False
            ).select_related('store').order_by('-date')[:10]
            
            return {
                'total_visits': total_visits,
                'recent_visits': recent_visits,
                'today': today,
                'thirty_days_ago': thirty_days_ago
            }
        except Exception as e:
            logger.error(f"Error getting basic stats: {str(e)}")
            return {
                'total_visits': 0,
                'recent_visits': [],
                'today': timezone.now().date(),
                'thirty_days_ago': timezone.now().date() - timedelta(days=30)
            }

    @staticmethod
    def get_action_stats(user, today):
        """Get action item statistics"""
        open_actions_query = ActionPlanItem.objects.filter(
            visit__manager=user, 
            status='open'
        ).select_related('visit__store')
        
        open_actions = open_actions_query.order_by('timeframe')[:10]
        overdue_actions = open_actions_query.filter(timeframe__lt=today)
        
        return {
            'open_actions': open_actions,
            'open_actions_high': open_actions_query.filter(priority='high').count(),
            'open_actions_medium': open_actions_query.filter(priority='medium').count(),
            'open_actions_low': open_actions_query.filter(priority='low').count(),
            'overdue_actions': overdue_actions,
            'overdue_actions_count': overdue_actions.count(),
        }
    
    @staticmethod
    def get_compliance_data(user, thirty_days_ago):
        """Get compliance rate and chart data"""
        # Compliance rate calculation
        all_items = ChecklistItem.objects.filter(
            visit__manager=user, 
            visit__is_draft=False
        )
        
        compliance_rate = 0
        if all_items.exists():
            compliant_items = all_items.filter(answer=True).count()
            total_items_count = all_items.count()
            if total_items_count > 0:
                compliance_rate = round((compliant_items / total_items_count) * 100, 1)
        
        # Chart data for compliance trends
        chart_dates = []
        chart_scores = []
        
        recent_visits_chart = AreaManagerVisit.objects.filter(
            manager=user, 
            is_draft=False,
            date__gte=thirty_days_ago
        ).order_by('date')
        
        for visit in recent_visits_chart:
            chart_dates.append(visit.date.strftime('%b %d'))
            score = visit.calculate_score()
            chart_scores.append(score if score is not None else 0)
        
        return {
            'compliance_rate': compliance_rate,
            'chart_dates': chart_dates,
            'chart_scores': chart_scores,
        }

    @staticmethod
    def get_store_performance(user):
        """Get store performance metrics"""
        stores = Store.objects.filter(is_active=True)
        
        if hasattr(user, 'profile') and user.profile is not None:
            if user.profile.role not in ['admin', 'area_management']:
                stores = user.profile.stores.filter(is_active=True)
        
        store_performance = []
        
        for store in stores:
            store_visits = AreaManagerVisit.objects.filter(
                store=store, 
                manager=user, 
                is_draft=False
            )
            
            if store_visits.exists():
                # Calculate average score by iterating through visits
                total_score = 0
                visit_count = store_visits.count()
                
                for visit in store_visits:
                    total_score += visit.calculate_score()
                
                avg_score = total_score / visit_count if visit_count > 0 else 0
                
                store_performance.append({
                    'store': store,
                    'visit_count': visit_count,
                    'avg_score': round(avg_score, 1),
                    'last_visit': store_visits.order_by('-date').first().date if store_visits.exists() else None,
                })
        
        store_performance.sort(key=lambda x: x['avg_score'], reverse=True)
        return store_performance

    @staticmethod
    def get_monthly_stats(user, today):
        """Get monthly statistics"""
        current_month = today.replace(day=1)
        
        monthly_visits = AreaManagerVisit.objects.filter(
            manager=user,
            is_draft=False,
            date__gte=current_month
        )
        
        # Calculate average score by iterating through visits
        total_score = 0
        visit_count = monthly_visits.count()
        
        for visit in monthly_visits:
            total_score += visit.calculate_score()
        
        avg_score = total_score / visit_count if visit_count > 0 else 0
        
        return {
            'visits_this_month': visit_count,
            'avg_score_this_month': round(avg_score, 1),
        }
    
    @staticmethod
    def get_maintenance_stats(user, today):
        """Get maintenance statistics"""
        maintenance_visits = []
        maintenance_stats = {
            'pending': 0,
            'in_progress': 0,
            'completed': 0,
            'overdue': 0,
        }
        
        try:
            maintenance_query = MaintenanceTicket.objects.filter(
                visit__manager=user
            ).select_related('visit__store')
            
            maintenance_visits = maintenance_query.order_by('-created_date')[:5]
            
            maintenance_stats = {
                'pending': maintenance_query.filter(status='pending').count(),
                'in_progress': maintenance_query.filter(status='in_progress').count(),
                'completed': maintenance_query.filter(status='completed').count(),
                'overdue': maintenance_query.filter(
                    status__in=['pending', 'in_progress'],
                    due_date__lt=today
                ).count(),
            }
        except Exception:
            # Fallback if Maintenance model doesn't exist
            maintenance_visits = AreaManagerVisit.objects.filter(
                manager=user,
                is_draft=False,
                maintenance_needed__isnull=False
            ).exclude(maintenance_needed='').order_by('-date')[:5]
            
            maintenance_stats = {
                'pending': maintenance_visits.count(),
                'in_progress': 0,
                'completed': 0,
                'overdue': 0,
            }
        
        return {
            'maintenance_visits': maintenance_visits,
            'maintenance_stats': maintenance_stats,
        }
    
    @staticmethod
    def get_performance_trend(chart_scores):
        """Calculate performance trend"""
        performance_trend = 'stable'
        if len(chart_scores) >= 2:
            recent_avg = sum(chart_scores[-7:]) / len(chart_scores[-7:]) if len(chart_scores) >= 7 else sum(chart_scores) / len(chart_scores)
            older_avg = sum(chart_scores[:-7]) / len(chart_scores[:-7]) if len(chart_scores) > 7 else recent_avg
            
            if recent_avg > older_avg + 5:
                performance_trend = 'improving'
            elif recent_avg < older_avg - 5:
                performance_trend = 'declining'
                
        return performance_trend


@login_required
def dashboard(request):
    """Comprehensive dashboard view with full error handling"""
    try:
        manager = DashboardManager()
        user = request.user
        
        # Get all statistics with fallback handling
        basic_stats = manager.get_basic_stats(user)
        action_stats = manager.get_action_stats(user, basic_stats['today'])
        compliance_data = manager.get_compliance_data(user, basic_stats['thirty_days_ago'])
        maintenance_data = manager.get_maintenance_stats(user, basic_stats['today'])
        store_performance = manager.get_store_performance(user)
        monthly_stats = manager.get_monthly_stats(user, basic_stats['today'])
        performance_trend = manager.get_performance_trend(compliance_data['chart_scores'])

        # Category performance (labels + scores)
        category_perf = manager.get_category_performance(user)
        category_labels = [c['name'] for c in category_perf]
        category_scores = [c['compliance'] for c in category_perf]

        # Stores performance arrays (top 10)
        top_stores = store_performance[:10]
        store_labels = [sp['store'].name for sp in top_stores]
        store_scores = [sp['avg_score'] for sp in top_stores]
        
        context = {
            # Basic statistics
            'total_visits': basic_stats['total_visits'],
            'recent_visits': basic_stats['recent_visits'],
            'today': basic_stats['today'],
            
            # Enhanced analytics
            **action_stats,
            **compliance_data,
            **maintenance_data,
            'store_performance': store_performance[:5],
            'monthly_stats': monthly_stats,
            'performance_trend': performance_trend,

            # Category and Store datasets for charts
            'category_performance': category_perf,
            'category_labels': category_labels,
            'category_scores': category_scores,
            'store_labels': store_labels,
            'store_scores': store_scores,
            
            # Additional features
            'import_url': 'checklist:checklist_checklistquestion_import',
            'export_url': 'checklist:checklist_question_export',
            'error': False
        }
        
        return render(request, 'checklist/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Critical dashboard error: {str(e)}")
        messages.error(request, "A system error occurred. Please try again later.")
        
        # Comprehensive fallback context
        return render(request, 'checklist/dashboard.html', {
            'error': True,
            'total_visits': 0,
            'recent_visits': [],
            'today': timezone.now().date(),
            'open_actions': [],
            'overdue_actions': [],
            'compliance_rate': 0,
            'maintenance_visits': [],
            'store_performance': [],
            'monthly_stats': {'visits_this_month': 0, 'avg_score_this_month': 0}
        })