from django.views.generic import TemplateView
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from datetime import timedelta

from ..models import ProductionOrder, ProductionReceipt, ProductionIssue, BillOfMaterials

class ProductionDashboardView(TemplateView):
    template_name = 'production/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        period = kwargs.get('period', 'monthly')
        
        # Set date range based on period
        today = timezone.now().date()
        if period == 'daily':
            start_date = today
            end_date = today
            context['period_label'] = f"Today ({today.strftime('%b %d, %Y')})"
        elif period == 'weekly':
            start_date = today - timedelta(days=today.weekday())  # Monday
            end_date = start_date + timedelta(days=6)  # Sunday
            context['period_label'] = f"This Week ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')})"
        else:  # monthly
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            context['period_label'] = f"This Month ({start_date.strftime('%b %Y')})"
        
        # Production Orders statistics
        production_orders = ProductionOrder.objects.filter(document_date__range=[start_date, end_date])
        context['total_production_orders'] = production_orders.count()
        context['completed_production_orders'] = production_orders.filter(status='Completed').count()
        context['in_process_production_orders'] = production_orders.filter(status='In Process').count()
        
        # Production completion rate
        if context['total_production_orders'] > 0:
            context['production_completion_rate'] = (context['completed_production_orders'] / context['total_production_orders']) * 100
        else:
            context['production_completion_rate'] = 0
        
        # Production Receipts statistics
        production_receipts = ProductionReceipt.objects.filter(document_date__range=[start_date, end_date])
        context['total_production_receipts'] = production_receipts.count()
        context['posted_production_receipts'] = production_receipts.filter(status='Posted').count()
        
        # Production Issues statistics
        production_issues = ProductionIssue.objects.filter(document_date__range=[start_date, end_date])
        context['total_production_issues'] = production_issues.count()
        context['posted_production_issues'] = production_issues.filter(status='Posted').count()
        
        # BOM statistics
        context['total_boms'] = BillOfMaterials.objects.count()
        context['active_boms'] = BillOfMaterials.objects.filter(status='Active').count()
        
        # Recent Production Orders
        context['recent_production_orders'] = ProductionOrder.objects.order_by('-document_date')[:5]
        
        # Recent Production Receipts
        context['recent_production_receipts'] = ProductionReceipt.objects.order_by('-document_date')[:5]
        
        # Recent Production Issues
        context['recent_production_issues'] = ProductionIssue.objects.order_by('-document_date')[:5]
        
        return context
