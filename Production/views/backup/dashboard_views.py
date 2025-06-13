from django.views.generic import TemplateView
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import timedelta

from ..models import ProductionOrder, ProductionReceipt, ProductionIssue

class ProductionDashboardView(TemplateView):
    template_name = 'production/dashboard.html'
    permission_required = 'Production.view_productionorder'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Dashboard'
        context['subtitle'] = 'Production overview and statistics'
        
        # Get date range
        today = timezone.now().date()
        period = self.kwargs.get('period', 'monthly')
        
        if period == 'daily':
            start_date = today - timedelta(days=7)
            date_format = '%Y-%m-%d'
            date_label = 'Last 7 days'
        elif period == 'weekly':
            start_date = today - timedelta(days=30)
            date_format = '%Y-%W'
            date_label = 'Last 4 weeks'
        else:  # monthly
            start_date = today - timedelta(days=180)
            date_format = '%Y-%m'
            date_label = 'Last 6 months'
            
        context['period'] = period
        context['date_label'] = date_label
        
        # Get production orders
        production_orders = ProductionOrder.objects.filter(
            document_date__gte=start_date
        )
        
        # Get production receipts
        production_receipts = ProductionReceipt.objects.filter(
            document_date__gte=start_date,
            status='Posted'
        )
        
        # Get production issues
        production_issues = ProductionIssue.objects.filter(
            document_date__gte=start_date,
            status='Posted'
        )
        
        # Calculate statistics
        context['total_orders'] = production_orders.count()
        context['orders_in_process'] = production_orders.filter(status='In Process').count()
        context['orders_completed'] = production_orders.filter(status='Completed').count()
        
        context['total_planned_quantity'] = production_orders.aggregate(
            total=Sum('planned_quantity')
        )['total'] or 0
        
        context['total_produced_quantity'] = production_orders.aggregate(
            total=Sum('produced_quantity')
        )['total'] or 0
        
        context['total_receipts'] = production_receipts.count()
        context['total_receipt_quantity'] = production_receipts.aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        context['total_issues'] = production_issues.count()
        
        # Get recent production orders
        context['recent_orders'] = production_orders.order_by('-document_date')[:5]
        
        # Get recent production receipts
        context['recent_receipts'] = production_receipts.order_by('-document_date')[:5]
        
        # Get recent production issues
        context['recent_issues'] = production_issues.order_by('-document_date')[:5]
        
        # Calculate completion rate
        if context['total_planned_quantity'] > 0:
            context['completion_rate'] = (context['total_produced_quantity'] / context['total_planned_quantity']) * 100
        else:
            context['completion_rate'] = 0
            
        return context