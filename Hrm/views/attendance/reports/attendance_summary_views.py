from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django import forms
from decimal import Decimal

from Hrm.models import Attendance, Employee, Department, OvertimeRecord

class AttendanceSummaryFilterForm(forms.Form):
    """Filter form for attendance summary"""
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
        choices=[('', 'All Status')] + list(Attendance.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(Attendance, 'STATUS_CHOICES'):
            raise ValueError("Attendance model does not have STATUS_CHOICES defined.")

class AttendanceSummaryView(TemplateView):
    """View for attendance summary report"""
    template_name = 'attendance/reports/attendance_summary.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize filter form
        filter_form = AttendanceSummaryFilterForm(self.request.GET or None)
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
        queryset = Attendance.objects.filter(date__range=[date_from, date_to]).select_related('employee', 'employee__department')
        
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
            emp_attendance = queryset.filter(employee=employee)
            
            total_days = emp_attendance.count()
            present_days = emp_attendance.filter(status='PRE').count()
            absent_days = emp_attendance.filter(status='ABS').count()
            late_days = emp_attendance.filter(status='LAT').count()
            leave_days = emp_attendance.filter(status='LEA').count()
            half_days = emp_attendance.filter(status='HAL').count()
            
            # Calculate aggregates
            aggregates = emp_attendance.aggregate(
                total_overtime_minutes=Sum('overtime_minutes'),
                total_late_minutes=Sum('late_minutes')
            )
            
            total_overtime_hours = (aggregates['total_overtime_minutes'] or 0) / 60
            total_late_minutes = aggregates['total_late_minutes'] or 0
            
            # Calculate working hours from check_in and check_out
            total_working_hours = 0
            for att in emp_attendance:
                if att.check_in and att.check_out:
                    duration = att.check_out - att.check_in
                    hours = duration.total_seconds() / 3600  # Convert to hours
                    total_working_hours += hours
            
            summary_data.append({
                'employee': employee,
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'leave_days': leave_days,
                'half_days': half_days,
                'total_working_hours': round(float(total_working_hours), 2),
                'total_overtime_hours': round(float(total_overtime_hours), 2),
                'total_late_minutes': total_late_minutes,
                'attendance_percentage': round((present_days / total_days * 100) if total_days > 0 else 0, 2)
            })
        
        context['summary_data'] = summary_data
        context['date_from'] = date_from
        context['date_to'] = date_to
        context['employees'] = employees
        context['departments'] = Department.objects.all()
        
        return context

class EmployeeAttendanceDetailFilterForm(forms.Form):
    """Filter form for employee attendance detail"""
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
        required=True,
        empty_label="Select Employee",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white'
        })
    )

class EmployeeAttendanceDetailView(TemplateView):
    """View for detailed attendance report for a specific employee"""
    template_name = 'attendance/reports/employee_attendance_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize filter form
        filter_form = EmployeeAttendanceDetailFilterForm(self.request.GET or None)
        context['filter_form'] = filter_form
        
        # Initialize defaults
        employee = None
        date_from = timezone.now().date().replace(day=1)  # First day of current month
        date_to = timezone.now().date()  # Today
        attendance_records = []
        error_message = None
        
        if filter_form.is_valid():
            filters = filter_form.cleaned_data
            employee = filters.get('employee')
            
            # Get date range
            try:
                if filters.get('date_from'):
                    date_from = datetime.strptime(str(filters['date_from']), '%Y-%m-%d').date()
                if filters.get('date_to'):
                    date_to = datetime.strptime(str(filters['date_to']), '%Y-%m-%d').date()
                
                if date_from > date_to:
                    date_from, date_to = date_to, date_from
                    context['date_warning'] = "Date range was adjusted: 'From Date' was later than 'To Date'."
                    
            except ValueError:
                context['date_error'] = "Invalid date format. Using default date range."
                date_from = timezone.now().date().replace(day=1)
                date_to = timezone.now().date()
        
        else:
            context['form_error'] = "Please select an employee."
        
        # Fetch attendance records if employee is selected
        if employee:
            queryset = Attendance.objects.filter(
                employee=employee,
                date__range=[date_from, date_to]
            ).select_related('employee', 'employee__department').order_by('date')
            
            for record in queryset:
                working_hours = 0
                if record.check_in and record.check_out:
                    duration = record.check_out - record.check_in
                    working_hours = duration.total_seconds() / 3600  # Convert to hours
                
                attendance_records.append({
                    'date': record.date,
                    'check_in': record.check_in,
                    'check_out': record.check_out,
                    'status': record.get_status_display(),
                    'working_hours': round(float(working_hours), 2),
                    'overtime_minutes': record.overtime_minutes or 0,
                    'late_minutes': record.late_minutes or 0,
                    'early_out_minutes': record.early_out_minutes or 0,
                })
        else:
            context['form_error'] = context.get('form_error', "No employee selected.")
        
        context['employee'] = employee
        context['attendance_records'] = attendance_records
        context['date_from'] = date_from
        context['date_to'] = date_to
        context['employees'] = Employee.objects.filter(is_active=True)
        
        return context