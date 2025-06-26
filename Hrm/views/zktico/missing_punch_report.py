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

class MissingPunchReportForm(forms.Form):
    """Form for generating missing punch report."""
    
    # Date Range
    start_date = forms.DateField(
        label=_("Start Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the start date for the missing punch report.")
    )
    end_date = forms.DateField(
        label=_("End Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the end date for the missing punch report.")
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
    
    # Missing Punch Options
    missing_punch_type = forms.ChoiceField(
        label=_("Missing Punch Type"),
        choices=[
            ('all', _('All Missing Punches')),
            ('in_only', _('Missing Check-In Only')),
            ('out_only', _('Missing Check-Out Only')),
            ('both', _('Missing Both In & Out')),
        ],
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Filter by type of missing punch.")
    )
    
    # Weekend and Holiday Options
    weekend_days = forms.MultipleChoiceField(
        label=_("Weekend Days"),
        choices=[
            (0, _('Monday')), (1, _('Tuesday')), (2, _('Wednesday')),
            (3, _('Thursday')), (4, _('Friday')), (5, _('Saturday')), (6, _('Sunday'))
        ],
        initial=[4, 5],  # Friday and Saturday
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text=_("Select weekend days to exclude from missing punch analysis.")
    )
    
    exclude_holidays = forms.BooleanField(
        label=_("Exclude Holidays"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Exclude holiday dates from missing punch analysis.")
    )
    
    exclude_leave_days = forms.BooleanField(
        label=_("Exclude Leave Days"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Exclude approved leave days from missing punch analysis.")
    )
    
    # Grace and Threshold Settings
    grace_minutes = forms.IntegerField(
        label=_("Grace Minutes"),
        initial=15,
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Grace period for late arrival in minutes.")
    )
    
    minimum_work_minutes = forms.IntegerField(
        label=_("Minimum Work Duration (Minutes)"),
        initial=30,
        min_value=0,
        max_value=1440,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Minimum work duration to consider as valid attendance.")
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(_("Start date cannot be after end date."))
            
            if (end_date - start_date).days > 90:
                raise forms.ValidationError(_("Date range cannot exceed 90 days for performance reasons."))
        
        return cleaned_data

class MissingPunchReportView(LoginRequiredMixin, View):
    """View for generating missing punch reports."""
    template_name = 'report/hrm/missing_punch_report.html'
    
    def get(self, request, *args, **kwargs):
        form = MissingPunchReportForm()
        
        # Set default dates
        today = timezone.now().date()
        form.fields['start_date'].initial = today - timedelta(days=7)
        form.fields['end_date'].initial = today
        
        context_data = self._get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        # Handle export request
        if 'export' in request.POST:
            return self._handle_export(request)
        
        form = MissingPunchReportForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                report_data = self._generate_missing_punch_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'missing_punch_data': report_data['missing_punch_data'],
                    'summary_data': report_data['summary_data'],
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, _("Missing punch report generated successfully. Found {} missing punch records.").format(
                    len(report_data['missing_punch_data'])))
                
            except Exception as e:
                logger.error(f"Error generating missing punch report: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'page_title': _("Missing Punch Report"),
            'report_generated': False,
        }
    
    def _generate_missing_punch_report(self, form_data):
        """Generate missing punch report using UnifiedAttendanceProcessor."""
        start_date = form_data['start_date']
        end_date = form_data['end_date']
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        
        # Get holidays and leaves
        holidays = Holiday.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ) if form_data['exclude_holidays'] else Holiday.objects.none()
        
        # Get ZK attendance logs
        employee_ids = [emp.employee_id for emp in employees]
        zk_logs = ZKAttendanceLog.objects.filter(
            user_id__in=employee_ids,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        ).order_by('user_id', 'timestamp')
        
        # Get roster data
        roster_data = self._get_roster_data(employees, start_date, end_date)
        
        # Initialize processor
        processor = UnifiedAttendanceProcessor(form_data)
        
        missing_punch_data = []
        summary_data = {
            'total_employees': len(employees),
            'total_days_checked': (end_date - start_date).days + 1,
            'missing_in_only': 0,
            'missing_out_only': 0,
            'missing_both': 0,
            'total_missing_punches': 0,
            'employees_with_missing_punches': 0,
        }
        
        employees_with_missing = set()
        
        for employee in employees:
            employee_logs = zk_logs.filter(user_id=employee.employee_id)
            employee_roster_data = roster_data.get(employee.id, {})
            
            # Get leave applications for this employee
            leave_applications = LeaveApplication.objects.filter(
                employee=employee,
                status='APP',
                start_date__lte=end_date,
                end_date__gte=start_date
            ) if form_data['exclude_leave_days'] else LeaveApplication.objects.none()
            
            # Process attendance for this employee
            attendance_result = processor.process_employee_attendance(
                employee, start_date, end_date, employee_logs,
                holidays, leave_applications, employee_roster_data
            )
            
            # Analyze missing punches from daily records
            for daily_record in attendance_result['daily_records']:
                missing_punch_record = self._analyze_missing_punch(
                    daily_record, employee, form_data
                )
                
                if missing_punch_record:
                    missing_punch_data.append(missing_punch_record)
                    employees_with_missing.add(employee.id)
                    
                    # Update summary
                    if missing_punch_record['missing_type'] == 'in_only':
                        summary_data['missing_in_only'] += 1
                    elif missing_punch_record['missing_type'] == 'out_only':
                        summary_data['missing_out_only'] += 1
                    elif missing_punch_record['missing_type'] == 'both':
                        summary_data['missing_both'] += 1
        
        summary_data['total_missing_punches'] = len(missing_punch_data)
        summary_data['employees_with_missing_punches'] = len(employees_with_missing)
        
        # Filter by missing punch type if specified
        if form_data['missing_punch_type'] != 'all':
            missing_punch_data = [
                record for record in missing_punch_data
                if record['missing_type'] == form_data['missing_punch_type']
            ]
        
        return {
            'missing_punch_data': missing_punch_data,
            'summary_data': summary_data,
        }
    
    def _analyze_missing_punch(self, daily_record, employee, form_data):
        """Analyze daily record for missing punches."""
        # Skip holidays, leaves, and weekends if configured
        if daily_record['status'] in ['HOL', 'LEA']:
            return None
        
        # Skip weekends if configured
        if daily_record['date'].weekday() in form_data['weekend_days']:
            return None
        
        # Check for missing punches
        has_in = daily_record['in_time'] is not None
        has_out = daily_record['out_time'] is not None
        
        missing_type = None
        if not has_in and not has_out:
            missing_type = 'both'
        elif not has_in:
            missing_type = 'in_only'
        elif not has_out:
            missing_type = 'out_only'
        
        if missing_type:
            return {
                'employee': employee,
                'employee_id': employee.employee_id,
                'employee_name': employee.get_full_name(),
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'date': daily_record['date'],
                'day_name': daily_record['day_name'],
                'missing_type': missing_type,
                'shift_name': daily_record['shift_name'],
                'shift_start_time': daily_record['shift_start_time'],
                'shift_end_time': daily_record['shift_end_time'],
                'in_time': daily_record['in_time'],
                'out_time': daily_record['out_time'],
                'total_logs': daily_record['total_logs'],
                'working_hours': daily_record['working_hours'],
                'status': daily_record['status'],
                'roster_info': daily_record['roster_info'],
            }
        
        return None
    
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
        """Handle CSV export of missing punch report."""
        form = MissingPunchReportForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please fix form errors before exporting."))
            return self.post(request)
        
        try:
            report_data = self._generate_missing_punch_report(form.cleaned_data)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="missing_punch_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Employee ID', 'Employee Name', 'Department', 'Designation',
                'Date', 'Day', 'Missing Type', 'Shift', 'Shift Start', 'Shift End',
                'Check In', 'Check Out', 'Total Logs', 'Working Hours', 'Status'
            ])
            
            for record in report_data['missing_punch_data']:
                writer.writerow([
                    record['employee_id'],
                    record['employee_name'],
                    record['department'],
                    record['designation'],
                    record['date'].strftime('%Y-%m-%d'),
                    record['day_name'],
                    record['missing_type'].replace('_', ' ').title(),
                    record['shift_name'],
                    record['shift_start_time'].strftime('%H:%M') if record['shift_start_time'] else '',
                    record['shift_end_time'].strftime('%H:%M') if record['shift_end_time'] else '',
                    record['in_time'].strftime('%Y-%m-%d %H:%M:%S') if record['in_time'] else '',
                    record['out_time'].strftime('%Y-%m-%d %H:%M:%S') if record['out_time'] else '',
                    record['total_logs'],
                    record['working_hours'],
                    record['status'],
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting missing punch report: {str(e)}")
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)
