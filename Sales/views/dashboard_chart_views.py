import json
from datetime import datetime, timedelta
from django.views.generic import TemplateView
from django.db.models import Sum, Count, F, Q, Value, FloatField, DecimalField, ExpressionWrapper, Avg
from django.db.models.functions import TruncDay, TruncMonth, Coalesce, ExtractDay, ExtractMonth
from django.utils import timezone
from django.shortcuts import redirect
from django.http import JsonResponse

from Sales.models import (
    ARInvoice, ARInvoiceLine, SalesOrder, SalesOrderLine, 
    SalesQuotation, SalesEmployee, Delivery, Return
)
from Inventory.models import Item, Warehouse
from BusinessPartnerMasterData.models import BusinessPartner


class SalesDashboardChartView(TemplateView):
    template_name = 'sales/dashboard/sales-dashboard-chart.html'

    def get(self, request, *args, **kwargs):
        # Get period from kwargs (URL) or request parameters or default to daily
        period = kwargs.get('period') or request.GET.get('period', 'daily')
        
        # If accessing the default dashboard URL, redirect to the specific view
        if 'period' not in kwargs and 'period' not in request.GET:
            return redirect('Sales:dashboard_chart_daily')
        
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get period from kwargs or request parameters
        period = kwargs.get('period') or self.request.GET.get('period', 'daily')
        context['period'] = period
        
        # Get date ranges
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        
        try:
            # Daily metrics
            context['today_sales'] = self.get_today_sales()
            context['today_deliveries'] = self.get_today_deliveries()
            context['today_invoices'] = self.get_today_invoices()
            context['today_returns'] = self.get_today_returns()
            context['today_quotations'] = self.get_today_quotations()
            context['new_orders'] = self.get_new_orders()
            
            # Monthly metrics
            context['monthly_sales'] = self.get_monthly_sales()
            context['monthly_deliveries'] = self.get_monthly_deliveries()
            context['monthly_invoices'] = self.get_monthly_invoices()
            context['monthly_returns'] = self.get_monthly_returns()
            context['monthly_quotations'] = self.get_monthly_quotations()
            context['monthly_orders'] = self.get_monthly_orders()
            
            # Top products
            context['top_products_daily'] = self.get_top_products(today, today)
            context['top_products_monthly'] = self.get_top_products(first_day_of_month, today)
            
            # Top customers
            context['top_customers_daily'] = self.get_top_customers(today, today)
            context['top_customers_monthly'] = self.get_top_customers(first_day_of_month, today)
            
            # Sales employee orders
            context['sales_employee_orders'] = self.get_sales_employee_orders(today, today)
            context['sales_employee_orders_monthly'] = self.get_sales_employee_orders(first_day_of_month, today)
            
            # Delivery employee deliveries
            context['delivery_employee_deliveries'] = self.get_delivery_employee_deliveries(today, today)
            context['delivery_employee_deliveries_monthly'] = self.get_delivery_employee_deliveries(first_day_of_month, today)
            
            # Today's orders
            context['todays_orders'] = self.get_todays_orders()
            
            # Today's deliveries, returns, and invoices
            context['todays_deliveries'] = self.get_todays_deliveries()
            context['todays_returns'] = self.get_todays_returns()
            context['todays_invoices'] = self.get_todays_invoices()
            
            # Top monthly orders
            context['top_monthly_orders'] = self.get_top_monthly_orders()
            
            # Monthly lists for detailed views
            context['monthly_deliveries_list'] = self.get_monthly_deliveries_list()
            context['monthly_returns_list'] = self.get_monthly_returns_list()
            context['monthly_invoices_list'] = self.get_monthly_invoices_list()
            
            # Chart data
            context['daily_sales_chart_data'] = self.get_daily_sales_chart_data()
            context['monthly_sales_chart_data'] = self.get_monthly_sales_chart_data()
            context['top_products_chart_data'] = self.get_top_products_chart_data(period)
            context['top_customers_chart_data'] = self.get_top_customers_chart_data(period)
            context['sales_vs_returns_chart_data'] = self.get_sales_vs_returns_chart_data(period)
            context['employee_performance_chart_data'] = self.get_employee_performance_chart_data(period)
            
        except Exception as e:
            # Log the error and provide empty data to prevent template rendering issues
            print(f"Error fetching dashboard data: {str(e)}")
            # Set default empty values for all context variables
            context.update({
                'today_sales': {'total': 0, 'count': 0},
                'today_deliveries': {'total': 0, 'count': 0},
                'today_invoices': {'total': 0, 'count': 0},
                'today_returns': {'total': 0, 'count': 0},
                'today_quotations': {'total': 0, 'count': 0},
                'new_orders': {'total': 0, 'count': 0},
                'monthly_sales': {'total': 0, 'count': 0},
                'monthly_deliveries': {'total': 0, 'count': 0},
                'monthly_invoices': {'total': 0, 'count': 0},
                'monthly_returns': {'total': 0, 'count': 0},
                'monthly_quotations': {'total': 0, 'count': 0},
                'monthly_orders': {'total': 0, 'count': 0},
                'top_products_daily': [],
                'top_products_monthly': [],
                'top_customers_daily': [],
                'top_customers_monthly': [],
                'sales_employee_orders': [],
                'sales_employee_orders_monthly': [],
                'delivery_employee_deliveries': [],
                'delivery_employee_deliveries_monthly': [],
                'todays_orders': [],
                'todays_deliveries': [],
                'todays_returns': [],
                'todays_invoices': [],
                'top_monthly_orders': [],
                'monthly_deliveries_list': [],
                'monthly_returns_list': [],
                'monthly_invoices_list': [],
                'daily_sales_chart_data': {'labels': [], 'datasets': []},
                'monthly_sales_chart_data': {'labels': [], 'datasets': []},
                'top_products_chart_data': {'labels': [], 'datasets': []},
                'top_customers_chart_data': {'labels': [], 'datasets': []},
                'sales_vs_returns_chart_data': {'labels': [], 'datasets': []},
                'employee_performance_chart_data': {'labels': [], 'datasets': []},
            })
        
        return context

    def get_daily_sales_chart_data(self):
        """Get sales data for the last 7 days for chart visualization"""
        today = timezone.now().date()
        start_date = today - timedelta(days=6)  # Last 7 days including today
        
        # Get daily sales data
        daily_sales = SalesOrder.objects.filter(
            document_date__gte=start_date,
            document_date__lte=today
        ).annotate(
            day=TruncDay('document_date')
        ).values('day').annotate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        ).order_by('day')
        
        # Create a dictionary to store sales by day
        sales_by_day = {day.strftime('%Y-%m-%d'): 0 for day in [start_date + timedelta(days=i) for i in range(7)]}
        
        # Fill in the actual sales data
        for entry in daily_sales:
            day_str = entry['day'].strftime('%Y-%m-%d')
            sales_by_day[day_str] = float(entry['total'])
        
        # Format for Chart.js
        labels = [day for day in sales_by_day.keys()]
        data = [sales_by_day[day] for day in labels]
        
        # Format dates for display
        display_labels = [(datetime.strptime(day, '%Y-%m-%d')).strftime('%b %d') for day in labels]
        
        return {
            'labels': display_labels,
            'datasets': [{
                'label': 'Daily Sales',
                'data': data,
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1,
                'tension': 0.4
            }]
        }

    def get_monthly_sales_chart_data(self):
        """Get sales data for the last 6 months for chart visualization"""
        today = timezone.now().date()
        start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)  # First day of 6 months ago
        start_date = start_date - timedelta(days=5*30)  # Approximate 5 months back
        
        # Get monthly sales data
        monthly_sales = SalesOrder.objects.filter(
            document_date__gte=start_date,
            document_date__lte=today
        ).annotate(
            month=TruncMonth('document_date')
        ).values('month').annotate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        ).order_by('month')
        
        # Create a list of the last 6 months
        months = []
        for i in range(5, -1, -1):
            month = today.replace(day=1) - timedelta(days=i*30)  # Approximate
            months.append(month.replace(day=1))
        
        # Create a dictionary to store sales by month
        sales_by_month = {month.strftime('%Y-%m'): 0 for month in months}
        
        # Fill in the actual sales data
        for entry in monthly_sales:
            month_str = entry['month'].strftime('%Y-%m')
            if month_str in sales_by_month:
                sales_by_month[month_str] = float(entry['total'])
        
        # Format for Chart.js
        labels = [month for month in sales_by_month.keys()]
        data = [sales_by_month[month] for month in labels]
        
        # Format dates for display
        display_labels = [(datetime.strptime(month, '%Y-%m')).strftime('%b %Y') for month in labels]
        
        return {
            'labels': display_labels,
            'datasets': [{
                'label': 'Monthly Sales',
                'data': data,
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1,
                'tension': 0.4
            }]
        }

    def get_top_products_chart_data(self, period):
        """Get top products data for chart visualization"""
        today = timezone.now().date()
        
        if period == 'daily':
            start_date = today
            top_products = self.get_top_products(start_date, today)
            chart_title = 'Top Products (Today)'
        else:
            start_date = today.replace(day=1)
            top_products = self.get_top_products(start_date, today)
            chart_title = 'Top Products (This Month)'
        
        # Extract data for chart
        labels = [product['item_name'] for product in top_products]
        sales_data = [float(product['total_sales']) for product in top_products]
        quantity_data = [float(product['total_quantity']) for product in top_products]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Sales Amount',
                    'data': sales_data,
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 1
                },
                {
                    'label': 'Quantity Sold',
                    'data': quantity_data,
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                }
            ],
            'title': chart_title
        }

    def get_top_customers_chart_data(self, period):
        """Get top customers data for chart visualization"""
        today = timezone.now().date()
        
        if period == 'daily':
            start_date = today
            top_customers = self.get_top_customers(start_date, today)
            chart_title = 'Top Customers (Today)'
        else:
            start_date = today.replace(day=1)
            top_customers = self.get_top_customers(start_date, today)
            chart_title = 'Top Customers (This Month)'
        
        # Extract data for chart
        labels = [customer['customer_name'] for customer in top_customers]
        sales_data = [float(customer['total_sales']) for customer in top_customers]
        order_data = [customer['order_count'] for customer in top_customers]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Sales Amount',
                    'data': sales_data,
                    'backgroundColor': 'rgba(153, 102, 255, 0.2)',
                    'borderColor': 'rgba(153, 102, 255, 1)',
                    'borderWidth': 1
                },
                {
                    'label': 'Order Count',
                    'data': order_data,
                    'backgroundColor': 'rgba(255, 159, 64, 0.2)',
                    'borderColor': 'rgba(255, 159, 64, 1)',
                    'borderWidth': 1
                }
            ],
            'title': chart_title
        }

    def get_sales_vs_returns_chart_data(self, period):
        """Get sales vs returns data for chart visualization"""
        today = timezone.now().date()
        
        if period == 'daily':
            # Get data for the last 7 days
            start_date = today - timedelta(days=6)
            date_range = [start_date + timedelta(days=i) for i in range(7)]
            
            # Get daily sales data
            daily_sales = SalesOrder.objects.filter(
                document_date__gte=start_date,
                document_date__lte=today
            ).annotate(
                day=TruncDay('document_date')
            ).values('day').annotate(
                total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField()))
            ).order_by('day')
            
            # Get daily returns data
            daily_returns = Return.objects.filter(
                document_date__gte=start_date,
                document_date__lte=today
            ).annotate(
                day=TruncDay('document_date')
            ).values('day').annotate(
                total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField()))
            ).order_by('day')
            
            # Create dictionaries to store data by day
            sales_by_day = {day.strftime('%Y-%m-%d'): 0 for day in date_range}
            returns_by_day = {day.strftime('%Y-%m-%d'): 0 for day in date_range}
            
            # Fill in the actual data
            for entry in daily_sales:
                day_str = entry['day'].strftime('%Y-%m-%d')
                if day_str in sales_by_day:
                    sales_by_day[day_str] = float(entry['total'])
            
            for entry in daily_returns:
                day_str = entry['day'].strftime('%Y-%m-%d')
                if day_str in returns_by_day:
                    returns_by_day[day_str] = float(entry['total'])
            
            # Format for Chart.js
            labels = [day for day in sales_by_day.keys()]
            sales_data = [sales_by_day[day] for day in labels]
            returns_data = [returns_by_day[day] for day in labels]
            
            # Format dates for display
            display_labels = [(datetime.strptime(day, '%Y-%m-%d')).strftime('%b %d') for day in labels]
            chart_title = 'Sales vs Returns (Last 7 Days)'
            
        else:
            # Get data for the last 6 months
            today = timezone.now().date()
            start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)  # First day of 6 months ago
            start_date = start_date - timedelta(days=5*30)  # Approximate 5 months back
            
            # Create a list of the last 6 months
            months = []
            for i in range(5, -1, -1):
                month = today.replace(day=1) - timedelta(days=i*30)  # Approximate
                months.append(month.replace(day=1))
            
            # Get monthly sales data
            monthly_sales = SalesOrder.objects.filter(
                document_date__gte=start_date,
                document_date__lte=today
            ).annotate(
                month=TruncMonth('document_date')
            ).values('month').annotate(
                total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField()))
            ).order_by('month')
            
            # Get monthly returns data
            monthly_returns = Return.objects.filter(
                document_date__gte=start_date,
                document_date__lte=today
            ).annotate(
                month=TruncMonth('document_date')
            ).values('month').annotate(
                total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField()))
            ).order_by('month')
            
            # Create dictionaries to store data by month
            sales_by_month = {month.strftime('%Y-%m'): 0 for month in months}
            returns_by_month = {month.strftime('%Y-%m'): 0 for month in months}
            
            # Fill in the actual data
            for entry in monthly_sales:
                month_str = entry['month'].strftime('%Y-%m')
                if month_str in sales_by_month:
                    sales_by_month[month_str] = float(entry['total'])
            
            for entry in monthly_returns:
                month_str = entry['month'].strftime('%Y-%m')
                if month_str in returns_by_month:
                    returns_by_month[month_str] = float(entry['total'])
            
            # Format for Chart.js
            labels = [month for month in sales_by_month.keys()]
            sales_data = [sales_by_month[month] for month in labels]
            returns_data = [returns_by_month[month] for month in labels]
            
            # Format dates for display
            display_labels = [(datetime.strptime(month, '%Y-%m')).strftime('%b %Y') for month in labels]
            chart_title = 'Sales vs Returns (Last 6 Months)'
        
        return {
            'labels': display_labels,
            'datasets': [
                {
                    'label': 'Sales',
                    'data': sales_data,
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'borderWidth': 1,
                    'tension': 0.4
                },
                {
                    'label': 'Returns',
                    'data': returns_data,
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 1,
                    'tension': 0.4
                }
            ],
            'title': chart_title
        }

    def get_employee_performance_chart_data(self, period):
        """Get employee performance data for chart visualization"""
        today = timezone.now().date()
        
        if period == 'daily':
            start_date = today
            employee_data = self.get_sales_employee_orders(start_date, today)
            chart_title = 'Sales Employee Performance (Today)'
        else:
            start_date = today.replace(day=1)
            employee_data = self.get_sales_employee_orders_monthly(start_date, today)
            chart_title = 'Sales Employee Performance (This Month)'
        
        # Extract data for chart
        labels = [employee['employee_name'] for employee in employee_data]
        amount_data = [float(employee['total_amount']) for employee in employee_data]
        order_data = [employee['order_count'] for employee in employee_data]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Sales Amount',
                    'data': amount_data,
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                },
                {
                    'label': 'Order Count',
                    'data': order_data,
                    'backgroundColor': 'rgba(255, 206, 86, 0.2)',
                    'borderColor': 'rgba(255, 206, 86, 1)',
                    'borderWidth': 1
                }
            ],
            'title': chart_title
        }

    # Reuse methods from SalesDashboardView
    def get_todays_deliveries(self):
        """Get today's deliveries"""
        today = timezone.now().date()
        try:
            deliveries = Delivery.objects.filter(
                document_date=today
            ).select_related('customer', 'sales_employee').order_by('-document_date')[:10]
            
            return deliveries
        except Exception as e:
            print(f"Error in get_todays_deliveries: {str(e)}")
            return []

    def get_todays_returns(self):
        """Get today's returns"""
        today = timezone.now().date()
        try:
            returns = Return.objects.filter(
                document_date=today
            ).select_related('customer', 'sales_employee').order_by('-document_date')[:10]
            
            return returns
        except Exception as e:
            print(f"Error in get_todays_returns: {str(e)}")
            return []

    def get_todays_invoices(self):
        """Get today's invoices"""
        today = timezone.now().date()
        try:
            invoices = ARInvoice.objects.filter(
                document_date=today
            ).select_related('customer', 'sales_employee').order_by('-document_date')[:10]
            
            return invoices
        except Exception as e:
            print(f"Error in get_todays_invoices: {str(e)}")
            return []

    def get_today_sales(self):
        """Get today's sales data"""
        today = timezone.now().date()
        sales_data = SalesOrder.objects.filter(
            document_date=today
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return sales_data

    def get_today_deliveries(self):
        """Get today's deliveries data"""
        today = timezone.now().date()
        delivery_data = Delivery.objects.filter(
            document_date=today
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return delivery_data

    def get_today_invoices(self):
        """Get today's invoices data"""
        today = timezone.now().date()
        invoice_data = ARInvoice.objects.filter(
            document_date=today
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return invoice_data

    def get_today_returns(self):
        """Get today's returns data"""
        today = timezone.now().date()
        return_data = Return.objects.filter(
            document_date=today
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return return_data

    def get_today_quotations(self):
        """Get today's quotations data"""
        today = timezone.now().date()
        quotation_data = SalesQuotation.objects.filter(
            document_date=today
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return quotation_data

    def get_new_orders(self):
        """Get new orders data"""
        today = timezone.now().date()
        new_orders_data = SalesOrder.objects.filter(
            document_date=today,
            status='Draft'  # Assuming 'New' status is 'Draft' in your model
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return new_orders_data

    def get_monthly_sales(self):
        """Get monthly sales data"""
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        sales_data = SalesOrder.objects.filter(
            document_date__gte=first_day_of_month,
            document_date__lte=today
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return sales_data

    def get_monthly_deliveries(self):
        """Get monthly deliveries data"""
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        delivery_data = Delivery.objects.filter(
            document_date__gte=first_day_of_month,
            document_date__lte=today
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return delivery_data

    def get_monthly_invoices(self):
        """Get monthly invoices data"""
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        invoice_data = ARInvoice.objects.filter(
            document_date__gte=first_day_of_month,
            document_date__lte=today
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return invoice_data

    def get_monthly_returns(self):
        """Get monthly returns data"""
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        return_data = Return.objects.filter(
            document_date__gte=first_day_of_month,
            document_date__lte=today
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return return_data

    def get_monthly_quotations(self):
        """Get monthly quotations data"""
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        quotation_data = SalesQuotation.objects.filter(
            document_date__gte=first_day_of_month,
            document_date__lte=today
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return quotation_data

    def get_monthly_orders(self):
        """Get monthly orders data"""
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        orders_data = SalesOrder.objects.filter(
            document_date__gte=first_day_of_month,
            document_date__lte=today
        ).aggregate(
            total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField())),
            count=Count('id')
        )
        return orders_data

    def get_top_products(self, start_date, end_date):
        """Get top products by sales for a date range"""
        try:
            # Create a proper expression with output_field for the multiplication
            total_sales_expr = ExpressionWrapper(
                F('quantity') * F('unit_price'), 
                output_field=DecimalField(max_digits=18, decimal_places=6)
            )
            
            # Get all order lines for orders in the date range
            top_products = SalesOrderLine.objects.filter(
                order__document_date__gte=start_date,
                order__document_date__lte=end_date
            ).values('item_name').annotate(
                total_quantity=Sum('quantity'),
                total_sales=Sum(total_sales_expr),
                avg_price=ExpressionWrapper(
                    Sum(total_sales_expr) / Sum('quantity'),
                    output_field=DecimalField(max_digits=18, decimal_places=6)
                )
            ).order_by('-total_sales')[:5]
            
            return top_products
        except Exception as e:
            print(f"Error in get_top_products: {str(e)}")
            return []

    def get_top_customers(self):
        try:
            # Your code logic to get top customers goes here
            pass
        except Exception as e:
            print(f"Error in get_top_customers: {str(e)}")
            return []

    def get_top_customers(self, start_date, end_date):
        """Get top customers by sales for a date range"""
        try:
            top_customers = SalesOrder.objects.filter(
                document_date__gte=start_date,
                document_date__lte=end_date,
                customer__isnull=False  # Ensure customer exists
            ).values('customer__id', 'customer__name').annotate(
                customer_name=F('customer__name'),  # Explicit annotation
                order_count=Count('id'),
                invoice_count=Count('invoices', distinct=True),  # Use distinct to avoid duplicates
                total_sales=Sum('total_amount')
            ).order_by('-total_sales')[:5]
            
            return top_customers
        except Exception as e:
            print(f"Error in get_top_customers: {str(e)}")
            return []

    def get_sales_employee_orders(self, start_date, end_date):
        """Get sales employee performance for a date range - all orders without status filtering"""
        try:
            # Get all sales employees
            all_employees = SalesEmployee.objects.all()
            employee_data = []
            
            for employee in all_employees:
                # Get all orders for this employee in the date range
                orders = SalesOrder.objects.filter(
                    document_date__gte=start_date,
                    document_date__lte=end_date,
                    sales_employee=employee
                )
                
                # Calculate metrics
                order_count = orders.count()
                total_amount = orders.aggregate(
                    total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField()))
                )['total']
                
                # Calculate average order value
                avg_order = 0
                if order_count > 0:
                    avg_order = total_amount / order_count
                
                # Add to results if they have any orders in this period
                if order_count > 0:
                    employee_data.append({
                        'employee_id': employee.id,
                        'employee_name': employee.name,
                        'order_count': order_count,
                        'total_amount': total_amount,
                        'avg_order': avg_order
                    })
            
            # Sort by total amount descending
            employee_data = sorted(employee_data, key=lambda x: x['total_amount'], reverse=True)
            return employee_data
        except Exception as e:
            print(f"Error in get_sales_employee_orders: {str(e)}")
            return []

    def get_sales_employee_orders_monthly(self, start_date, end_date):
        """Alias for get_sales_employee_orders to be explicit about monthly data"""
        return self.get_sales_employee_orders(start_date, end_date)

    def get_delivery_employee_deliveries(self, start_date, end_date):
        """Get delivery employee performance for a date range - all deliveries without status filtering"""
        try:
            # Get all unique delivery employees
            all_delivery_employees = Delivery.objects.filter(
                document_date__gte=start_date,
                document_date__lte=end_date,
                deliveryemployee__isnull=False
            ).values_list('deliveryemployee', flat=True).distinct()
            
            employee_data = []
            
            for employee_name in all_delivery_employees:
                # Get all deliveries for this employee in the date range
                deliveries = Delivery.objects.filter(
                    document_date__gte=start_date,
                    document_date__lte=end_date,
                    deliveryemployee=employee_name
                )
                
                # Calculate metrics
                delivery_count = deliveries.count()
                total_amount = deliveries.aggregate(
                    total=Coalesce(Sum('total_amount'), Value(0, output_field=DecimalField()))
                )['total']
                
                # Calculate average delivery value
                avg_delivery = 0
                if delivery_count > 0:
                    avg_delivery = total_amount / delivery_count
                
                # Add to results
                employee_data.append({
                    'delivery_employee_name': employee_name,
                    'delivery_count': delivery_count,
                    'total_amount': total_amount,
                    'avg_delivery': avg_delivery
                })
            
            # Sort by total amount descending
            employee_data = sorted(employee_data, key=lambda x: x['total_amount'], reverse=True)
            return employee_data
        except Exception as e:
            print(f"Error in get_delivery_employee_deliveries: {str(e)}")
            return []

    def get_todays_orders(self):
        """Get today's orders"""
        today = timezone.now().date()
        try:
            orders = SalesOrder.objects.filter(
                document_date=today
            ).select_related('customer', 'sales_employee').order_by('-document_date')[:10]
            
            return orders
        except Exception as e:
            print(f"Error in get_todays_orders: {str(e)}")
            return []

    def get_top_monthly_orders(self):
        """Get top monthly orders by amount"""
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        try:
            orders = SalesOrder.objects.filter(
                document_date__gte=first_day_of_month,
                document_date__lte=today
            ).select_related('customer', 'sales_employee').order_by('-total_amount')[:10]
            
            return orders
        except Exception as e:
            print(f"Error in get_top_monthly_orders: {str(e)}")
            return []
            
    def get_monthly_deliveries_list(self):
        """Get list of deliveries for the current month"""
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        try:
            deliveries = Delivery.objects.filter(
                document_date__gte=first_day_of_month,
                document_date__lte=today
            ).select_related('customer', 'sales_employee').order_by('-total_amount')[:15]
            
            return deliveries
        except Exception as e:
            print(f"Error in get_monthly_deliveries_list: {str(e)}")
            return []
    
    def get_monthly_returns_list(self):
        """Get list of returns for the current month"""
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        try:
            returns = Return.objects.filter(
                document_date__gte=first_day_of_month,
                document_date__lte=today
            ).select_related('customer', 'sales_employee').order_by('-total_amount')[:15]
            
            return returns
        except Exception as e:
            print(f"Error in get_monthly_returns_list: {str(e)}")
            return []
    
    def get_monthly_invoices_list(self):
        """Get list of invoices for the current month"""
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        try:
            invoices = ARInvoice.objects.filter(
                document_date__gte=first_day_of_month,
                document_date__lte=today
            ).select_related('customer', 'sales_employee').order_by('-total_amount')[:15]
            
            return invoices
        except Exception as e:
            print(f"Error in get_monthly_invoices_list: {str(e)}")
            return []