from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django import forms
from decimal import Decimal
import calendar
from Hrm.models import Attendance, Employee, Department, OvertimeRecord,Holiday,LeaveApplication
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
    
    
class MonthlySalaryReportForm(forms.Form):
    YEAR_CHOICES = [(y, y) for y in range(2020, datetime.today().year + 2)]
    MONTH_CHOICES = [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]

    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        initial=datetime.now().year,
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white'})
    )
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        initial=datetime.now().month,
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:focus:border-blue-500 dark:bg-gray-700 dark:text-white'})
    )
    



class MonthlySalarySummaryView(TemplateView):
    template_name = 'attendance/reports/monthly_salary_summary.html' 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use the MonthlySalaryReportForm for year and month selection
        form = MonthlySalaryReportForm(self.request.GET or None)
        context['form'] = form # Use 'form' as context key as in previous answer

        employees_data = []
        year = None
        month = None

        if form.is_valid():
            year = int(form.cleaned_data['year'])
            month = int(form.cleaned_data['month'])
            
            num_days_in_month = calendar.monthrange(year, month)[1]
            start_date = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.get_current_timezone())
            end_date = datetime(year, month, num_days_in_month, 23, 59, 59, tzinfo=timezone.get_current_timezone())

            employees_queryset = Employee.objects.filter(is_active=True).order_by('first_name')

            holidays_in_month_dates = set(Holiday.objects.filter(
                date__year=year, 
                date__month=month
            ).values_list('date', flat=True))
            
            for employee in employees_queryset:
                # --- ADD THESE DEBUG PRINTS ---
                print(f"--- Employee: {employee.get_full_name()} (ID: {employee.id}) ---")
                print(f"Gross Salary: {employee.gross_salary}, Type: {type(employee.gross_salary)}")
                print(f"Expected Work Hours: {employee.expected_work_hours}, Type: {type(employee.expected_work_hours)}")
                print(f"Number of days in month: {num_days_in_month}")
                
                # Initialize for this employee
                distinct_payable_dates_for_employee = set()
                present_days_display = 0
                late_days_display = 0
                total_overtime_minutes = 0
                
                attendance_records = Attendance.objects.filter(
                    employee=employee,
                    date__year=year,
                    date__month=month
                )
                
                for record in attendance_records:
                    if record.status == 'PRE':
                        present_days_display += 1
                        distinct_payable_dates_for_employee.add(record.date)
                    elif record.status == 'LAT':
                        late_days_display += 1
                        distinct_payable_dates_for_employee.add(record.date)
                    
                    total_overtime_minutes += record.overtime_minutes or 0
                
                approved_leave_applications = LeaveApplication.objects.filter(
                    employee=employee,
                    status='APP',
                    start_date__lte=end_date.date(),
                    end_date__gte=start_date.date()
                ).order_by('start_date')

                leave_days_for_display = 0
                for leave_app in approved_leave_applications:
                    current_leave_date = leave_app.start_date
                    while current_leave_date <= leave_app.end_date:
                        if start_date.date() <= current_leave_date <= end_date.date():
                            if current_leave_date not in distinct_payable_dates_for_employee:
                                leave_days_for_display += 1
                            distinct_payable_dates_for_employee.add(current_leave_date)
                        current_leave_date += timedelta(days=1)
                
                holiday_days_for_display = 0
                for holiday_date in holidays_in_month_dates:
                    if holiday_date not in distinct_payable_dates_for_employee:
                        holiday_days_for_display += 1
                    distinct_payable_dates_for_employee.add(holiday_date)
                
                payable_days = len(distinct_payable_dates_for_employee)
                
                # Calculate 1 day salary
                one_day_salary = Decimal('0.00')
                if employee.gross_salary and num_days_in_month > 0:
                    one_day_salary = employee.gross_salary / Decimal(str(num_days_in_month))
                print(f"Calculated One Day Salary: {one_day_salary}") # Debug print
                
                # Calculate Attendance Amount
                attendance_amount = one_day_salary * Decimal(str(payable_days))
                
                # Calculate Overtime Amount
                per_hour_ot_rate = Decimal('0.00')
                total_overtime_hours = Decimal(str(total_overtime_minutes / 60))
                
                # Debug print for expected_work_hours before division
                print(f"Employee Expected Work Hours for OT calculation: {employee.expected_work_hours}")

                if employee.expected_work_hours and employee.expected_work_hours > 0:
                    if one_day_salary > 0:
                        per_hour_ot_rate = one_day_salary / Decimal(str(employee.expected_work_hours))
                print(f"Calculated Per Hour OT Rate: {per_hour_ot_rate}") # Debug print
                
                overtime_amount = per_hour_ot_rate * total_overtime_hours
                
                # Calculate Total Salary Amount
                total_salary_amount = attendance_amount + overtime_amount

                employees_data.append({
                    'employee_id': employee.employee_id,
                    'employee_name': employee.get_full_name(),
                    'gross_salary': employee.gross_salary,
                    'expected_work_hours': employee.expected_work_hours, # This field is passed directly
                    'payable_days': payable_days,
                    'present_days': present_days_display,
                    'late_days': late_days_display,
                    'holiday_days': holiday_days_for_display,
                    'leave_days': leave_days_for_display,
                    'total_overtime_minutes': total_overtime_minutes,
                    'total_overtime_hours': round(total_overtime_hours, 2),
                    'one_day_salary': round(one_day_salary, 2),
                    'per_hour_ot_rate': round(per_hour_ot_rate, 2),
                    'attendance_amount': round(attendance_amount, 2),
                    'overtime_amount': round(overtime_amount, 2),
                    'total_salary_amount': round(total_salary_amount, 2),
                })
            
            context['employees_data'] = employees_data
            context['selected_year'] = year
            context['selected_month'] = month
            context['month_name'] = datetime(year, month, 1).strftime('%B') if year and month else ''

        return context    