import logging
from datetime import timedelta, datetime
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
import json
import csv

from Hrm.models import *
from .unified_attendance_processor import UnifiedAttendanceProcessor

logger = logging.getLogger(__name__)

class DailyAttendanceReportForm(forms.Form):
    """Form for generating daily attendance report."""
    
    # Date Selection
    report_date = forms.DateField(
        label=_("Report Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the date for daily attendance report.")
    )
    
    # Employee Filtering
    employee_filter = forms.ChoiceField(
        label=_("Employee Filter"),
        choices=[
            ('all', _('All Active Employees')),
            ('department', _('Filter by Department')),
            ('designation', _('Filter by Designation')),
            ('specific', _('Specific Employee IDs')),
        ],
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
    )
    
    designations = forms.ModelMultipleChoiceField(
        queryset=Designation.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
    )
    
    employee_ids = forms.CharField(
        label=_("Specific Employee IDs"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'EMP001, EMP002, EMP003'
        }),
    )
    
    # Display Options
    show_absent_employees = forms.BooleanField(
        label=_("Show Absent Employees"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include employees who were absent on the selected date.")
    )
    
    show_leave_employees = forms.BooleanField(
        label=_("Show Employees on Leave"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include employees who were on approved leave.")
    )
    
    show_holiday_status = forms.BooleanField(
        label=_("Show Holiday Status"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Show if the selected date is a holiday.")
    )
    
    include_roster_info = forms.BooleanField(
        label=_("Include Roster Information"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Show roster and shift information for each employee.")
    )
    
    # Weekend and Grace Settings
    weekend_days = forms.MultipleChoiceField(
        label=_("Weekend Days"),
        choices=[
            (0, _('Monday')), (1, _('Tuesday')), (2, _('Wednesday')),
            (3, _('Thursday')), (4, _('Friday')), (5, _('Saturday')), (6, _('Sunday'))
        ],
        initial=[4, 5],  # Friday and Saturday
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )
    
    grace_minutes = forms.IntegerField(
        label=_("Grace Minutes"),
        initial=15,
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    early_out_threshold_minutes = forms.IntegerField(
        label=_("Early Out Threshold (Minutes)"),
        initial=30,
        min_value=0,
        max_value=240,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    overtime_start_after_minutes = forms.IntegerField(
        label=_("Overtime Start After (Minutes)"),
        initial=15,
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    minimum_overtime_minutes = forms.IntegerField(
        label=_("Minimum Overtime (Minutes)"),
        initial=60,
        min_value=0,
        max_value=480,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

class DailyAttendanceReportView(LoginRequiredMixin, View):
    """View for generating daily attendance reports."""
    template_name = 'report/hrm/daily_attendance_report.html'
    
    def get(self, request, *args, **kwargs):
        form = DailyAttendanceReportForm()
        
        # Set default date to today
        today = timezone.now().date()
        form.fields['report_date'].initial = today
        
        context_data = self._get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        # Handle export request
        if 'export' in request.POST:
            return self._handle_export(request)
        
        form = DailyAttendanceReportForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                report_data = self._generate_daily_attendance_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'attendance_data': report_data['attendance_data'],
                    'summary_data': report_data['summary_data'],
                    'holiday_info': report_data['holiday_info'],
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, _("Daily attendance report generated successfully for {}.").format(
                    form.cleaned_data['report_date'].strftime('%Y-%m-%d')))
                
            except Exception as e:
                logger.error(f"Error generating daily attendance report: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'page_title': _("Daily Attendance Report"),
            'report_generated': False,
        }
    
    def _generate_daily_attendance_report(self, form_data):
        """Generate daily attendance report using UnifiedAttendanceProcessor."""
        report_date = form_data['report_date']
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        
        # Get holidays for the date
        holidays = Holiday.objects.filter(date=report_date)
        holiday_info = {
            'is_holiday': holidays.exists(),
            'holiday_name': holidays.first().name if holidays.exists() else None,
            'is_weekend': report_date.weekday() in form_data['weekend_days'],
            'day_name': report_date.strftime('%A'),
        }
        
        # Get ZK attendance logs for the date
        employee_ids = [emp.employee_id for emp in employees]
        zk_logs = ZKAttendanceLog.objects.filter(
            user_id__in=employee_ids,
            timestamp__date=report_date
        ).order_by('user_id', 'timestamp')
        
        # Get roster data
        roster_data = self._get_roster_data(employees, report_date, report_date)
        
        # Initialize processor
        processor = UnifiedAttendanceProcessor(form_data)
        
        attendance_data = []
        summary_data = {
            'total_employees': len(employees),
            'present_count': 0,
            'absent_count': 0,
            'late_count': 0,
            'leave_count': 0,
            'holiday_count': 0,
            'half_day_count': 0,
            'overtime_count': 0,
            'early_out_count': 0,
            'total_working_hours': 0.0,
            'total_overtime_hours': 0.0,
            'average_working_hours': 0.0,
            'attendance_percentage': 0.0,
        }
        
        for employee in employees:
            employee_logs = zk_logs.filter(user_id=employee.employee_id)
            employee_roster_data = roster_data.get(employee.id, {})
            
            # Get leave applications for this employee and date
            leave_applications = LeaveApplication.objects.filter(
                employee=employee,
                status='APP',
                start_date__lte=report_date,
                end_date__gte=report_date
            )
            
            # Process attendance for this employee for the single date
            attendance_result = processor.process_employee_attendance(
                employee, report_date, report_date, employee_logs,
                holidays, leave_applications, employee_roster_data
            )
            
            # Get the daily record for this date
            daily_record = attendance_result['daily_records'][0] if attendance_result['daily_records'] else None
            
            if daily_record:
                # Create attendance record for display
                attendance_record = {
                    'employee': employee,
                    'employee_id': employee.employee_id,
                    'employee_name': employee.get_full_name(),
                    'department': employee.department.name if employee.department else 'N/A',
                    'designation': employee.designation.name if employee.designation else 'N/A',
                    'date': daily_record['date'],
                    'day_name': daily_record['day_name'],
                    'status': daily_record['status'],
                    'status_display': self._get_status_display(daily_record['status']),
                    'in_time': daily_record['in_time'],
                    'out_time': daily_record['out_time'],
                    'working_hours': daily_record['working_hours'],
                    'late_minutes': daily_record['late_minutes'],
                    'early_out_minutes': daily_record['early_out_minutes'],
                    'overtime_hours': daily_record['overtime_hours'],
                    'shift_name': daily_record['shift_name'],
                    'shift_start_time': daily_record['shift_start_time'],
                    'shift_end_time': daily_record['shift_end_time'],
                    'roster_info': daily_record['roster_info'] if form_data['include_roster_info'] else '',
                    'total_logs': daily_record['total_logs'],
                    'is_roster_day': daily_record['is_roster_day'],
                    'expected_hours': daily_record['expected_hours'],
                }
                
                # Apply display filters
                should_include = True
                
                if not form_data['show_absent_employees'] and daily_record['status'] == 'ABS':
                    should_include = False
                elif not form_data['show_leave_employees'] and daily_record['status'] == 'LEA':
                    should_include = False
                
                if should_include:
                    attendance_data.append(attendance_record)
                
                # Update summary statistics
                status = daily_record['status']
                if status == 'PRE':
                    summary_data['present_count'] += 1
                elif status == 'ABS':
                    summary_data['absent_count'] += 1
                elif status == 'LAT':
                    summary_data['late_count'] += 1
                    summary_data['present_count'] += 1  # Late is still present
                elif status == 'LEA':
                    summary_data['leave_count'] += 1
                elif status == 'HOL':
                    summary_data['holiday_count'] += 1
                elif status == 'HAL':
                    summary_data['half_day_count'] += 1
                
                summary_data['total_working_hours'] += daily_record['working_hours']
                summary_data['total_overtime_hours'] += daily_record['overtime_hours']
                
                if daily_record['overtime_hours'] > 0:
                    summary_data['overtime_count'] += 1
                if daily_record['early_out_minutes'] > 0:
                    summary_data['early_out_count'] += 1
        
        # Calculate averages and percentages
        total_working_employees = summary_data['present_count'] + summary_data['late_count'] + summary_data['half_day_count']
        if total_working_employees > 0:
            summary_data['average_working_hours'] = round(
                summary_data['total_working_hours'] / total_working_employees, 2
            )
        
        total_expected_employees = len(employees) - summary_data['holiday_count'] - summary_data['leave_count']
        if total_expected_employees > 0:
            summary_data['attendance_percentage'] = round(
                (total_working_employees / total_expected_employees) * 100, 2
            )
        
        return {
            'attendance_data': attendance_data,
            'summary_data': summary_data,
            'holiday_info': holiday_info,
        }
    
    def _get_status_display(self, status):
        """Get human-readable status display."""
        status_map = {
            'PRE': _('Present'),
            'ABS': _('Absent'),
            'LAT': _('Late'),
            'LEA': _('Leave'),
            'HOL': _('Holiday'),
            'HAL': _('Half Day'),
        }
        return status_map.get(status, status)
    
    def _get_filtered_employees(self, form_data):
        """Get employees based on filter criteria."""
        employee_filter = form_data['employee_filter']
        
        queryset = Employee.objects.filter(is_active=True).select_related(
            'department', 'designation', 'default_shift'
        )
        
        if employee_filter == 'department':
            departments = form_data['departments']
            return queryset.filter(department__in=departments)
        elif employee_filter == 'designation':
            designations = form_data['designations']
            return queryset.filter(designation__in=designations)
        elif employee_filter == 'specific':
            employee_ids = [id.strip() for id in form_data['employee_ids'].split(',') if id.strip()]
            return queryset.filter(employee_id__in=employee_ids)
        
        return queryset
    
    def _get_roster_data(self, employees, start_date, end_date):
        """Get roster data for employees."""
        roster_data = {}
        
        try:
            # Get roster assignments
            roster_assignments = RosterAssignment.objects.filter(
                employee__in=employees,
                roster__start_date__lte=end_date,
                roster__end_date__gte=start_date
            ).select_related('roster', 'shift', 'employee')
            
            # Get roster days
            roster_days = RosterDay.objects.filter(
                roster_assignment__employee__in=employees,
                date__gte=start_date,
                date__lte=end_date
            ).select_related('shift', 'roster_assignment__roster')
            
        except Exception as e:
            logger.warning(f"Could not fetch roster data: {str(e)}")
            return {}
        
        # Organize data by employee
        for employee in employees:
            roster_data[employee.id] = {
                'assignments': {},
                'days': {}
            }
        
        # Organize roster assignments
        for assignment in roster_assignments:
            employee_id = assignment.employee.id
            current_date = max(assignment.roster.start_date, start_date)
            end_assignment_date = min(assignment.roster.end_date, end_date)
            
            while current_date <= end_assignment_date:
                roster_data[employee_id]['assignments'][current_date] = assignment
                current_date += timedelta(days=1)
        
        # Organize roster days
        for roster_day in roster_days:
            employee_id = roster_day.roster_assignment.employee.id
            roster_data[employee_id]['days'][roster_day.date] = roster_day
        
        return roster_data
    
    def _handle_export(self, request):
        """Handle CSV export of daily attendance report."""
        form = DailyAttendanceReportForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please fix form errors before exporting."))
            return self.post(request)
        
        try:
            report_data = self._generate_daily_attendance_report(form.cleaned_data)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="daily_attendance_report_{form.cleaned_data["report_date"].strftime("%Y%m%d")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Employee ID', 'Employee Name', 'Department', 'Designation',
                'Date', 'Day', 'Status', 'Check In', 'Check Out',
                'Working Hours', 'Late Minutes', 'Early Out Minutes', 'Overtime Hours',
                'Shift', 'Shift Start', 'Shift End', 'Total Logs', 'Expected Hours'
            ])
            
            for record in report_data['attendance_data']:
                writer.writerow([
                    record['employee_id'],
                    record['employee_name'],
                    record['department'],
                    record['designation'],
                    record['date'].strftime('%Y-%m-%d'),
                    record['day_name'],
                    record['status_display'],
                    record['in_time'].strftime('%Y-%m-%d %H:%M:%S') if record['in_time'] else '',
                    record['out_time'].strftime('%Y-%m-%d %H:%M:%S') if record['out_time'] else '',
                    record['working_hours'],
                    record['late_minutes'],
                    record['early_out_minutes'],
                    record['overtime_hours'],
                    record['shift_name'],
                    record['shift_start_time'].strftime('%H:%M') if record['shift_start_time'] else '',
                    record['shift_end_time'].strftime('%H:%M') if record['shift_end_time'] else '',
                    record['total_logs'],
                    record['expected_hours'],
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting daily attendance report: {str(e)}")
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)
