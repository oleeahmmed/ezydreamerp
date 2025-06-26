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

class OvertimeReportForm(forms.Form):
    """Form for generating overtime report."""
    
    # Date Selection
    start_date = forms.DateField(
        label=_("Start Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the start date for overtime report.")
    )
    
    end_date = forms.DateField(
        label=_("End Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the end date for overtime report.")
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
    
    # Display Options
    include_weekends = forms.BooleanField(
        label=_("Include Weekends"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include weekend overtime records.")
    )
    
    include_holidays = forms.BooleanField(
        label=_("Include Holidays"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include holiday overtime records.")
    )

class OvertimeReportView(LoginRequiredMixin, View):
    """View for generating overtime reports."""
    template_name = 'report/hrm/overtime_report.html'
    
    def get(self, request, *args, **kwargs):
        form = OvertimeReportForm()
        
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
        
        form = OvertimeReportForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                report_data = self._generate_overtime_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'attendance_data': report_data['attendance_data'],
                    'summary_data': report_data['summary_data'],
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, _("Overtime report generated successfully for {} to {}.").format(
                    form.cleaned_data['start_date'].strftime('%Y-%m-%d'),
                    form.cleaned_data['end_date'].strftime('%Y-%m-%d')))
                
            except Exception as e:
                logger.error(f"Error generating overtime report: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'page_title': _("Overtime Report"),
            'report_generated': False,
        }
    
    def _generate_overtime_report(self, form_data):
        """Generate overtime report using UnifiedAttendanceProcessor."""
        start_date = form_data['start_date']
        end_date = form_data['end_date']
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        
        # Get holidays for the date range
        holidays = Holiday.objects.filter(date__range=[start_date, end_date])
        
        # Initialize processor
        processor = UnifiedAttendanceProcessor(form_data)
        
        attendance_data = []
        summary_data = {
            'total_records': 0,
            'overtime_count': 0,
            'employees_with_overtime': 0,
            'departments_with_overtime': 0,
            'total_overtime_hours': 0.0,
            'total_working_hours': 0.0,
            'avg_overtime_hours': 0.0,
            'avg_daily_overtime': 0.0,
        }
        
        employees_with_overtime = set()
        departments_with_overtime = set()
        
        for employee in employees:
            try:
                # Get ZK logs for this employee
                zk_logs = ZKAttendanceLog.objects.filter(
                    user_id=employee.employee_id,
                    timestamp__date__range=[start_date, end_date]
                ).order_by('timestamp')
                
                # Get leave applications
                leave_applications = LeaveApplication.objects.filter(
                    employee=employee,
                    status='APP',
                    start_date__lte=end_date,
                    end_date__gte=start_date
                )
                
                # Get roster data
                roster_data = self._get_roster_data(employee, start_date, end_date)
                
                # Process attendance for this employee
                attendance_result = processor.process_employee_attendance(
                    employee, start_date, end_date, zk_logs,
                    holidays, leave_applications, roster_data
                )
                
                # Extract overtime records from daily_records
                for daily_record in attendance_result['daily_records']:
                    # Only include records with overtime > 0
                    if daily_record['overtime_hours'] > 0:
                        # Apply weekend/holiday filters
                        if not form_data['include_weekends'] and daily_record['date'].weekday() in [int(d) for d in form_data['weekend_days']]:
                            continue
                        if not form_data['include_holidays'] and daily_record['is_holiday']:
                            continue
                        
                        # Create overtime record for display (same format as daily attendance)
                        overtime_record = {
                            'employee': employee,
                            'employee_id': employee.employee_id,
                            'employee_name': employee.get_full_name(),
                            'designation': employee.designation.name if employee.designation else 'N/A',
                            'department': employee.department.name if employee.department else 'N/A',
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
                            'overtime_minutes': int(daily_record['overtime_hours'] * 60),
                            'overtime_time': f"{int(daily_record['overtime_hours'])}h {int((daily_record['overtime_hours'] % 1) * 60)}m",
                            'shift_name': daily_record['shift_name'],
                            'shift_start_time': daily_record['shift_start_time'],
                            'shift_end_time': daily_record['shift_end_time'],
                            'total_logs': daily_record['total_logs'],
                            'is_roster_day': daily_record['is_roster_day'],
                            'expected_hours': daily_record['expected_hours'],
                            'is_weekend': daily_record['date'].weekday() in [int(d) for d in form_data['weekend_days']],
                            'is_holiday': daily_record['is_holiday'],
                        }
                        
                        attendance_data.append(overtime_record)
                        employees_with_overtime.add(employee.employee_id)
                        if employee.department:
                            departments_with_overtime.add(employee.department.name)
                
                # Update summary statistics
                summary_data['total_records'] += len(attendance_result['daily_records'])
                summary_data['total_working_hours'] += attendance_result['summary_stats']['total_working_hours']
                summary_data['total_overtime_hours'] += attendance_result['summary_stats']['total_overtime_hours']
                
            except Exception as e:
                logger.error(f"Error processing employee {employee.employee_id}: {str(e)}")
                continue
        
        # Finalize summary data
        summary_data['overtime_count'] = len(attendance_data)
        summary_data['employees_with_overtime'] = len(employees_with_overtime)
        summary_data['departments_with_overtime'] = len(departments_with_overtime)
        
        if summary_data['overtime_count'] > 0:
            summary_data['avg_overtime_hours'] = round(summary_data['total_overtime_hours'] / summary_data['overtime_count'], 1)
        
        working_days = (end_date - start_date).days + 1
        if working_days > 0:
            summary_data['avg_daily_overtime'] = round(summary_data['total_overtime_hours'] / working_days, 1)
        
        return {
            'attendance_data': attendance_data,
            'summary_data': summary_data,
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
    
    def _get_roster_data(self, employee, start_date, end_date):
        """Get roster data for employee."""
        roster_data = {'days': {}, 'assignments': {}}
        
        try:
            # Get roster assignments
            roster_assignments = RosterAssignment.objects.filter(
                employee=employee,
                roster__start_date__lte=end_date,
                roster__end_date__gte=start_date
            ).select_related('roster', 'shift', 'employee')
            
            # Get roster days
            roster_days = RosterDay.objects.filter(
                roster_assignment__employee=employee,
                date__gte=start_date,
                date__lte=end_date
            ).select_related('shift', 'roster_assignment__roster')
            
        except Exception as e:
            logger.warning(f"Could not fetch roster data: {str(e)}")
            return roster_data
        
        # Organize data by employee
        roster_data = {'assignments': {}, 'days': {}}
        
        # Organize roster assignments
        for assignment in roster_assignments:
            current_date = max(assignment.roster.start_date, start_date)
            end_assignment_date = min(assignment.roster.end_date, end_date)
            
            while current_date <= end_assignment_date:
                roster_data['assignments'][current_date] = assignment
                current_date += timedelta(days=1)
        
        # Organize roster days
        for roster_day in roster_days:
            roster_data['days'][roster_day.date] = roster_day
        
        return roster_data
    
    def _handle_export(self, request):
        """Handle CSV export of overtime report."""
        form = OvertimeReportForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please fix form errors before exporting."))
            return self.post(request)
        
        try:
            report_data = self._generate_overtime_report(form.cleaned_data)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="overtime_report_{form.cleaned_data["start_date"].strftime("%Y%m%d")}_{form.cleaned_data["end_date"].strftime("%Y%m%d")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Employee ID', 'Employee Name', 'Department', 'Designation',
                'Date', 'Day', 'Status', 'Check In', 'Check Out',
                'Working Hours', 'Overtime Hours', 'Overtime Time', 'Late Minutes',
                'Early Out Minutes', 'Shift', 'Shift Start', 'Shift End', 'Total Logs'
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
                    record['overtime_hours'],
                    record['overtime_time'],
                    record['late_minutes'],
                    record['early_out_minutes'],
                    record['shift_name'],
                    record['shift_start_time'].strftime('%H:%M') if record['shift_start_time'] else '',
                    record['shift_end_time'].strftime('%H:%M') if record['shift_end_time'] else '',
                    record['total_logs'],
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting overtime report: {str(e)}")
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)

# Function-based view wrapper for URL compatibility
overtime_report = OvertimeReportView.as_view()
