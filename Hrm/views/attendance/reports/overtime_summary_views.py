from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django import forms
from decimal import Decimal

from Hrm.models import OvertimeRecord, Employee, Department

class OvertimeSummaryFilterForm(forms.Form):
    """Filter form for overtime summary"""
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white'
        }),
        label='From Date'
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white'
        }),
        label='To Date'
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(OvertimeRecord.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(OvertimeRecord, 'STATUS_CHOICES'):
            raise ValueError("OvertimeRecord model does not have STATUS_CHOICES defined.")

class OvertimeSummaryView(TemplateView):
    """View for overtime summary report"""
    template_name = 'attendance/overtime_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize filter form
        filter_form = OvertimeSummaryFilterForm(self.request.GET or None)
        context['filter_form'] = filter_form
        
        # Get date range
        try:
            date_from = self.request.GET.get('date_from')
            date_to = self.request.GET.get('date_to')
            if not date_from:
                date_from = timezone.now().date().replace(day=1)  # First day of current month
            else:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                
            if not date_to:
                date_to = timezone.now().date()  # Today
            else:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                
            if date_from > date_to:
                date_from, date_to = date_to, date_from
                context['date_warning'] = "Date range was adjusted: 'From Date' was later than 'To Date'."
                
        except ValueError:
            context['date_error'] = "Invalid date format. Using default date range."
            date_from = timezone.now().date().replace(day=1)
            date_to = timezone.now().date()
        
        # Base queryset
        queryset = OvertimeRecord.objects.filter(date__range=[date_from, date_to])
        
        # Apply filters
        employees = Employee.objects.filter(is_active=True)
        if filter_form.is_valid():
            filters = filter_form.cleaned_data
            if filters.get('employee'):
                queryset = queryset.filter(employee=filters['employee'])
                employees = employees.filter(id=filters['employee'].id)
            if filters.get('department'):
                queryset = queryset.filter(employee__department=filters['department'])
                employees = employees.filter(department=filters['department'])
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
        
        # Calculate summary data
        summary_data = []
        for employee in employees:
            emp_overtime = queryset.filter(employee=employee)
            
            total_records = emp_overtime.count()
            approved_records = emp_overtime.filter(status='APP').count()
            pending_records = emp_overtime.filter(status='PEN').count()
            
            # Calculate aggregates
            aggregates = emp_overtime.aggregate(
                total_hours=Sum('hours'),
                approved_hours=Sum('hours', filter=Q(status='APP')),
                pending_hours=Sum('hours', filter=Q(status='PEN'))
            )
            
            total_hours = aggregates['total_hours'] or 0
            approved_hours = aggregates['approved_hours'] or 0
            pending_hours = aggregates['pending_hours'] or 0
            
            # Calculate overtime amount
            hourly_rate = Decimal(employee.basic_salary) / Decimal('30') / Decimal('8')
            overtime_rate = hourly_rate * Decimal('1.5')
            total_overtime_amount = Decimal(total_hours) * overtime_rate
            
            summary_data.append({
                'employee': employee,
                'total_records': total_records,
                'approved_records': approved_records,
                'pending_records': pending_records,
                'total_hours': round(float(total_hours), 2),
                'approved_hours': round(float(approved_hours), 2),
                'pending_hours': round(float(pending_hours), 2),
                'total_overtime_amount': round(float(total_overtime_amount), 2),
                'approval_percentage': round((approved_records / total_records * 100) if total_records > 0 else 0, 2)
            })
        
        context['summary_data'] = summary_data
        context['date_from'] = date_from
        context['date_to'] = date_to
        context['employees'] = employees
        context['departments'] = Department.objects.all()
        
        return context