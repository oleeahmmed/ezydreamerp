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

class EarlyLeavingReportForm(forms.Form):
    """Form for generating early leaving report."""
    
    # Date Selection
    start_date = forms.DateField(
        label=_("Start Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the start date for early leaving report.")
    )
    
    end_date = forms.DateField(
        label=_("End Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the end date for early leaving report.")
    )
    
    # Employee Filtering
    employee_filter = forms.ChoiceField(
        label=_("Employee Filter"),
        choices=[
            ('all', _('All Employees')),
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
    
    # Early Leaving Settings
    early_leaving_threshold = forms.IntegerField(
        label=_("Early Leaving Threshold (Minutes)"),
        initial=30,
        min_value=1,
        max_value=480,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Minimum minutes to consider as early leaving.")
    )
    
    # Display Options
    include_weekends = forms.BooleanField(
        label=_("Include Weekends"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include weekend days in the report.")
    )
    
    include_holidays = forms.BooleanField(
        label=_("Include Holidays"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include holiday days in the report.")
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

class EarlyLeavingReportView(LoginRequiredMixin, View):
    """View for generating early leaving reports."""
    template_name = 'report/hrm/early_leaving_report.html'
    
    def get(self, request, *args, **kwargs):
        form = EarlyLeavingReportForm()
        
        # Set default dates
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        form.fields['start_date'].initial = start_of_month
        form.fields['end_date'].initial = today
        
        context_data = self._get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        # Handle export request
        if 'export' in request.POST:
            return self._handle_export(request)
        
        form = EarlyLeavingReportForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                report_data = self._generate_early_leaving_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'attendance_data': report_data['attendance_data'],
                    'summary_data': report_data['summary_data'],
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, _("Early leaving report generated successfully for {} to {}.").format(
                    form.cleaned_data['start_date'].strftime('%Y-%m-%d'),
                    form.cleaned_data['end_date'].strftime('%Y-%m-%d')))
                
            except Exception as e:
                logger.error(f"Error generating early leaving report: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'page_title': _("Early Leaving Report"),
            'report_generated': False,
        }
    
    def _generate_early_leaving_report(self, form_data):
        """Generate early leaving report using UnifiedAttendanceProcessor."""
        start_date = form_data['start_date']
        end_date = form_data['end_date']
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        
        # Get holidays for the date range
        holidays = Holiday.objects.filter(date__range=[start_date, end_date])
        
        # Get ZK attendance logs for the date range
        employee_ids = [emp.employee_id for emp in employees]
        zk_logs = ZKAttendanceLog.objects.filter(
            user_id__in=employee_ids,
            timestamp__date__range=[start_date, end_date]
        ).order_by('user_id', 'timestamp')
        
        # Get roster data
        roster_data = self._get_roster_data(employees, start_date, end_date)
        
        # Initialize processor
        processor = UnifiedAttendanceProcessor(form_data)
        
        attendance_data = []
        summary_data = {
            'total_records': 0,
            'early_leaving_count': 0,
            'total_early_minutes': 0,
            'avg_early_minutes': 0,
            'employees_with_early_leaving': 0,
            'departments_affected': 0,
            'total_working_hours': 0.0,
            'total_overtime_hours': 0.0,
        }
        
        employees_with_early = set()
        departments_affected = set()
        
        for employee in employees:
            employee_logs = zk_logs.filter(user_id=employee.employee_id)
            employee_roster_data = roster_data.get(employee.id, {})
            
            # Get leave applications for this employee and date range
            leave_applications = LeaveApplication.objects.filter(
                employee=employee,
                status='APP',
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            # Process attendance for this employee for the date range
            attendance_result = processor.process_employee_attendance(
                employee, start_date, end_date, employee_logs,
                holidays, leave_applications, employee_roster_data
            )
            
            # Filter for early leaving records
            for daily_record in attendance_result['daily_records']:
                if self._is_early_leaving_record(daily_record, form_data):
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
                        'shift_name': daily_record['shift_name'],
                        'scheduled_out': daily_record['shift_end_time'],
                        'actual_out': daily_record['out_time'],
                        'early_minutes': daily_record['early_out_minutes'],
                        'early_hours': round(daily_record['early_out_minutes'] / 60, 2),
                        'working_hours': daily_record['working_hours'],
                        'overtime_hours': daily_record['overtime_hours'],
                        'is_weekend': daily_record.get('is_holiday', False) and 'Weekend' in daily_record.get('holiday_name', ''),
                        'is_holiday': daily_record.get('is_holiday', False) and 'Weekend' not in daily_record.get('holiday_name', ''),
                        'reason': '',  # Can be extended later
                        'approved': False,  # Can be extended later
                        'approved_by': '',  # Can be extended later
                    }
                    
                    attendance_data.append(attendance_record)
                    employees_with_early.add(employee.id)
                    departments_affected.add(employee.department.name if employee.department else 'No Department')
                    summary_data['total_working_hours'] += daily_record['working_hours']
                    summary_data['total_overtime_hours'] += daily_record['overtime_hours']
        
        # Calculate summary statistics
        summary_data['total_records'] = len(attendance_data)
        summary_data['early_leaving_count'] = len([r for r in attendance_data if r['early_minutes'] > 0])
        summary_data['total_early_minutes'] = sum(r['early_minutes'] for r in attendance_data)
        summary_data['avg_early_minutes'] = (
            summary_data['total_early_minutes'] / max(summary_data['early_leaving_count'], 1)
        )
        summary_data['employees_with_early_leaving'] = len(employees_with_early)
        summary_data['departments_affected'] = len(departments_affected)
        
        return {
            'attendance_data': attendance_data,
            'summary_data': summary_data,
        }
    
    def _is_early_leaving_record(self, daily_record, form_data):
        """Check if a daily record qualifies as early leaving."""
        # Must have checkout time and be present/late
        if not daily_record.get('out_time') or daily_record.get('status') not in ['PRE', 'LAT']:
            return False
        
        # Must have early out minutes above threshold
        early_minutes = daily_record.get('early_out_minutes', 0)
        if early_minutes < form_data['early_leaving_threshold']:
            return False
        
        # Check weekend inclusion
        is_weekend = daily_record.get('is_holiday', False) and 'Weekend' in daily_record.get('holiday_name', '')
        if is_weekend and not form_data['include_weekends']:
            return False
        
        # Check holiday inclusion
        is_holiday = daily_record.get('is_holiday', False) and 'Weekend' not in daily_record.get('holiday_name', '')
        if is_holiday and not form_data['include_holidays']:
            return False
        
        return True
    
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
        
        queryset = Employee.objects.select_related(
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
        """Handle CSV export of early leaving report."""
        form = EarlyLeavingReportForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please fix form errors before exporting."))
            return self.post(request)
        
        try:
            report_data = self._generate_early_leaving_report(form.cleaned_data)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="early_leaving_report_{form.cleaned_data["start_date"].strftime("%Y%m%d")}_{form.cleaned_data["end_date"].strftime("%Y%m%d")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Employee ID', 'Employee Name', 'Department', 'Designation',
                'Date', 'Day', 'Shift', 'Scheduled Out', 'Actual Out',
                'Early Minutes', 'Early Hours', 'Working Hours', 'Overtime Hours',
                'Status', 'Weekend', 'Holiday'
            ])
            
            for record in report_data['attendance_data']:
                writer.writerow([
                    record['employee_id'],
                    record['employee_name'],
                    record['department'],
                    record['designation'],
                    record['date'].strftime('%Y-%m-%d'),
                    record['day_name'],
                    record['shift_name'],
                    record['scheduled_out'].strftime('%H:%M') if record['scheduled_out'] else '',
                    record['actual_out'].strftime('%H:%M:%S') if record['actual_out'] else '',
                    record['early_minutes'],
                    record['early_hours'],
                    record['working_hours'],
                    record['overtime_hours'],
                    record['status_display'],
                    'Yes' if record['is_weekend'] else 'No',
                    'Yes' if record['is_holiday'] else 'No',
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting early leaving report: {str(e)}")
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)
