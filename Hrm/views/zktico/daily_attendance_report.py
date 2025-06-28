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
    """Enhanced form for generating daily attendance report with dynamic shift options and 🔥 NEW RULES."""
    
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
    
    # 🔥 NEW RULE 1: Minimum Working Hours Rule
    enable_minimum_working_hours_rule = forms.BooleanField(
        label=_("🔥 Enable Minimum Working Hours Rule"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("If working hours are less than specified, mark as Absent")
    )
    
    minimum_working_hours_for_present = forms.FloatField(
        label=_("Minimum Hours for Present"),
        initial=4.0,
        min_value=1.0,
        max_value=12.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        help_text=_("Minimum working hours required to be marked as Present")
    )
    
    # 🔥 NEW RULE 2: Half Day Rule Based on Working Hours
    enable_working_hours_half_day_rule = forms.BooleanField(
        label=_("🔥 Enable Working Hours Half Day Rule"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Mark as Half Day if working hours are between specified range")
    )
    
    half_day_minimum_hours = forms.FloatField(
        label=_("Half Day Minimum Hours"),
        initial=4.0,
        min_value=1.0,
        max_value=8.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        help_text=_("Minimum hours for half day")
    )
    
    half_day_maximum_hours = forms.FloatField(
        label=_("Half Day Maximum Hours"),
        initial=6.0,
        min_value=2.0,
        max_value=10.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        help_text=_("Maximum hours for half day")
    )
    
    # 🔥 NEW RULE 3: In-time and Out-time Both Must Rule
    require_both_in_and_out = forms.BooleanField(
        label=_("🔥 Require Both In-time and Out-time"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Mark as Absent if either check-in or check-out is missing")
    )
    
    # 🔥 NEW RULE 4: Maximum Allowable Working Hours Rule
    enable_maximum_working_hours_rule = forms.BooleanField(
        label=_("🔥 Enable Maximum Working Hours Rule"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Flag potentially erroneous entries with excessive working hours")
    )
    
    maximum_allowable_working_hours = forms.FloatField(
        label=_("Maximum Allowable Working Hours"),
        initial=16.0,
        min_value=8.0,
        max_value=24.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        help_text=_("Maximum working hours before flagging as potentially erroneous")
    )
    
    # 🔥 NEW RULE 5: Dynamic Shift Detection Override Rule
    dynamic_shift_fallback_to_default = forms.BooleanField(
        label=_("🔥 Dynamic Shift Fallback to Default"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Use employee default shift when dynamic detection fails")
    )
    
    dynamic_shift_fallback_shift_id = forms.ModelChoiceField(
        label=_("Fallback Shift"),
        queryset=Shift.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Fixed shift to use when dynamic detection fails and no default shift")
    )
    
    # 🔥 NEW RULE 6: Grace Time per Shift Instead of Global
    use_shift_grace_time = forms.BooleanField(
        label=_("🔥 Use Shift-Specific Grace Time"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Use grace time defined in shift settings instead of global grace time")
    )
    
    # 🔥 NEW RULE 7: Consecutive Absence to Flag as Termination Risk
    enable_consecutive_absence_flagging = forms.BooleanField(
        label=_("🔥 Enable Consecutive Absence Flagging"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Flag employees with consecutive absences as termination risk")
    )
    
    consecutive_absence_termination_risk_days = forms.IntegerField(
        label=_("Consecutive Absence Days for Termination Risk"),
        initial=5,
        min_value=2,
        max_value=15,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Number of consecutive absence days to flag as termination risk")
    )
    
    # 🔥 NEW RULE 8: Max Early Out Threshold
    enable_max_early_out_flagging = forms.BooleanField(
        label=_("🔥 Enable Max Early Out Flagging"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Flag employees with excessive early out occurrences")
    )
    
    max_early_out_threshold_minutes = forms.IntegerField(
        label=_("Max Early Out Threshold (Minutes)"),
        initial=120,
        min_value=30,
        max_value=300,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Early out minutes threshold for flagging")
    )
    
    max_early_out_occurrences = forms.IntegerField(
        label=_("Max Early Out Occurrences"),
        initial=3,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Number of early out occurrences before flagging")
    )
    
    # 🔥 ENHANCED SHIFT DETECTION OPTIONS
    enable_dynamic_shift_detection = forms.BooleanField(
        label=_("Enable Dynamic Shift Detection"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Automatically detect shifts based on actual check-in/out times instead of roster assignments.")
    )
    
    dynamic_shift_tolerance_minutes = forms.IntegerField(
        label=_("Dynamic Shift Tolerance (Minutes)"),
        initial=30,
        min_value=5,
        max_value=120,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Time tolerance for matching attendance times to shift schedules.")
    )
    
    multiple_shift_priority = forms.ChoiceField(
        label=_("Multiple Shift Match Priority"),
        choices=[
            ('least_break', _('Least Break Time')),
            ('shortest_duration', _('Shortest Duration')),
            ('alphabetical', _('Alphabetical Order')),
        ],
        initial='least_break',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("How to choose when multiple shifts match the attendance pattern.")
    )
    
    # 🔥 ADVANCED OVERTIME CONFIGURATION
    overtime_calculation_method = forms.ChoiceField(
        label=_("Overtime Calculation Method"),
        choices=[
            ('shift_based', _('Shift-Based (After shift end time)')),
            ('expected_hours', _('Expected Hours-Based (After expected work hours)')),
        ],
        initial='shift_based',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Method for calculating when overtime starts.")
    )
    
    holiday_overtime_full_day = forms.BooleanField(
        label=_("Holiday Overtime - Full Day"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Consider entire working time as overtime on holidays.")
    )
    
    weekend_overtime_full_day = forms.BooleanField(
        label=_("Weekend Overtime - Full Day"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Consider entire working time as overtime on weekends.")
    )
    
    late_affects_overtime = forms.BooleanField(
        label=_("Late Arrival Affects Overtime"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Adjust overtime calculation if employee arrives late.")
    )
    
    separate_ot_break_time = forms.IntegerField(
        label=_("Separate Overtime Break Time (Minutes)"),
        initial=0,
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Additional break time to deduct from overtime hours.")
    )
    
    # 🔥 ENHANCED BREAK TIME CONFIGURATION
    use_shift_break_time = forms.BooleanField(
        label=_("Use Shift-Specific Break Time"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Use break time defined in shift settings, otherwise use default.")
    )
    
    default_break_minutes = forms.IntegerField(
        label=_("Default Break Time (Minutes)"),
        initial=60,
        min_value=0,
        max_value=240,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Default break time when shift break time is not available.")
    )
    
    break_deduction_method = forms.ChoiceField(
        label=_("Break Deduction Method"),
        choices=[
            ('fixed', _('Fixed Break Time')),
            ('proportional', _('Proportional to Working Hours')),
        ],
        initial='fixed',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("How to calculate break time deduction.")
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
    
    show_shift_analysis = forms.BooleanField(
        label=_("Show Shift Analysis"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Display detailed shift detection and analysis information.")
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
    
    # 🔥 ADVANCED RULES
    late_to_absent_days = forms.IntegerField(
        label=_("Late to Absent Conversion (Days)"),
        initial=3,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Convert to absent after this many consecutive late days.")
    )
    
    holiday_before_after_absent = forms.BooleanField(
        label=_("Holiday Before/After Absent Rule"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Mark holiday as absent if employee is absent before and after.")
    )
    
    weekend_before_after_absent = forms.BooleanField(
        label=_("Weekend Before/After Absent Rule"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Mark weekend as absent if employee is absent before and after.")
    )
    
    # 🔥 EMPLOYEE OVERRIDE SETTINGS
    use_employee_specific_grace = forms.BooleanField(
        label=_("Use Employee-Specific Grace Time"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Use individual employee grace time settings when available.")
    )
    
    use_employee_specific_overtime = forms.BooleanField(
        label=_("Use Employee-Specific Overtime Rules"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Use individual employee overtime settings when available.")
    )
    
    use_employee_expected_hours = forms.BooleanField(
        label=_("Use Employee Expected Hours"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Use individual employee expected work hours when available.")
    )

class DailyAttendanceReportView(LoginRequiredMixin, View):
    """Enhanced view for generating daily attendance reports with dynamic shift options and 🔥 NEW RULES."""
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
                    'shift_analysis': report_data.get('shift_analysis', {}),
                    'config_applied': report_data.get('config_applied', {}),
                    'flagged_records': report_data.get('flagged_records', []),
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, _("🔥 Enhanced daily attendance report generated successfully for {} with new rules applied.").format(
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
            'shifts': Shift.objects.all().order_by('name'),
            'page_title': _("🔥 Enhanced Daily Attendance Report with New Rules"),
            'report_generated': False,
        }
    
    def _generate_daily_attendance_report(self, form_data):
        """Generate daily attendance report using enhanced UnifiedAttendanceProcessor with 🔥 NEW RULES."""
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
        
        # 🔥 Initialize enhanced processor with all form options including NEW RULES
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
            'total_break_hours': 0.0,
            'average_working_hours': 0.0,
            'attendance_percentage': 0.0,
            'dynamic_detection_count': 0,
            'multiple_shift_matches': 0,
            # 🔥 NEW RULE SUMMARY STATS
            'flagged_employees': 0,
            'new_rule_conversions': {
                'minimum_hours': 0,
                'half_day': 0,
                'incomplete_punch': 0,
                'excessive_hours': 0,
                'termination_risk': 0,
                'excessive_early_out': 0,
            },
        }
        
        # 🔥 Enhanced shift analysis tracking
        shift_analysis = {
            'roster_day_usage': 0,
            'roster_assignment_usage': 0,
            'default_shift_usage': 0,
            'dynamic_detection_usage': 0,
            'no_shift_days': 0,
            'multiple_shift_matches': 0,
            'fallback_usage': 0,
        }
        
        all_flagged_records = []
        
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
            
            # 🔥 Process attendance with enhanced processor including NEW RULES
            attendance_result = processor.process_employee_attendance(
                employee, report_date, report_date, employee_logs,
                holidays, leave_applications, employee_roster_data
            )
            
            # Get the daily record for this date
            daily_record = attendance_result['daily_records'][0] if attendance_result['daily_records'] else None
            
            if daily_record:
                # 🔥 Create enhanced attendance record for display with NEW RULE fields
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
                    'original_status': daily_record.get('original_status', daily_record['status']),
                    'in_time': daily_record['in_time'],
                    'out_time': daily_record['out_time'],
                    'working_hours': daily_record['working_hours'],
                    'net_working_hours': daily_record.get('net_working_hours', daily_record['working_hours']),
                    'late_minutes': daily_record['late_minutes'],
                    'early_out_minutes': daily_record['early_out_minutes'],
                    'overtime_hours': daily_record['overtime_hours'],
                    'break_time_minutes': daily_record.get('break_time_minutes', 0),
                    'overtime_break_minutes': daily_record.get('overtime_break_minutes', 0),
                    'shift_name': daily_record['shift_name'],
                    'shift_start_time': daily_record['shift_start_time'],
                    'shift_end_time': daily_record['shift_end_time'],
                    'shift_source': daily_record.get('shift_source', 'Unknown'),
                    'roster_info': daily_record['roster_info'] if form_data['include_roster_info'] else '',
                    'total_logs': daily_record['total_logs'],
                    'is_roster_day': daily_record['is_roster_day'],
                    'expected_hours': daily_record['expected_hours'],
                    
                    # 🔥 Enhanced shift detection info
                    'dynamic_shift_used': daily_record.get('dynamic_shift_used', False),
                    'shift_match_confidence': daily_record.get('shift_match_confidence', 0.0),
                    'multiple_shifts_found': daily_record.get('multiple_shifts_found', []),
                    'converted_from_late': daily_record.get('converted_from_late', False),
                    'conversion_reason': daily_record.get('conversion_reason', ''),
                    
                    # 🔥 NEW RULE FIELDS
                    'converted_from_minimum_hours': daily_record.get('converted_from_minimum_hours', False),
                    'converted_to_half_day': daily_record.get('converted_to_half_day', False),
                    'converted_from_incomplete_punch': daily_record.get('converted_from_incomplete_punch', False),
                    'excessive_working_hours_flag': daily_record.get('excessive_working_hours_flag', False),
                    'termination_risk_flag': daily_record.get('termination_risk_flag', False),
                    'excessive_early_out_flag': daily_record.get('excessive_early_out_flag', False),
                    'excessive_early_out': daily_record.get('excessive_early_out', False),
                    'flag_reason': daily_record.get('flag_reason'),
                    
                    # 🔥 Enhanced overtime info
                    'overtime_calculation_method': daily_record.get('overtime_calculation_method', 'shift_based'),
                    'holiday_overtime': daily_record.get('holiday_overtime', False),
                    'weekend_overtime': daily_record.get('weekend_overtime', False),
                }
                
                # Apply display filters
                should_include = True
                
                if not form_data['show_absent_employees'] and daily_record['status'] == 'ABS':
                    should_include = False
                elif not form_data['show_leave_employees'] and daily_record['status'] == 'LEA':
                    should_include = False
                
                if should_include:
                    attendance_data.append(attendance_record)
                
                # 🔥 Update enhanced summary statistics including NEW RULE conversions
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
                summary_data['total_break_hours'] += daily_record.get('break_time_minutes', 0) / 60
                
                if daily_record['overtime_hours'] > 0:
                    summary_data['overtime_count'] += 1
                if daily_record['early_out_minutes'] > 0:
                    summary_data['early_out_count'] += 1
                if daily_record.get('dynamic_shift_used', False):
                    summary_data['dynamic_detection_count'] += 1
                if len(daily_record.get('multiple_shifts_found', [])) > 1:
                    summary_data['multiple_shift_matches'] += 1
                
                # 🔥 Track NEW RULE conversions
                if daily_record.get('converted_from_minimum_hours', False):
                    summary_data['new_rule_conversions']['minimum_hours'] += 1
                if daily_record.get('converted_to_half_day', False):
                    summary_data['new_rule_conversions']['half_day'] += 1
                if daily_record.get('converted_from_incomplete_punch', False):
                    summary_data['new_rule_conversions']['incomplete_punch'] += 1
                if daily_record.get('excessive_working_hours_flag', False):
                    summary_data['new_rule_conversions']['excessive_hours'] += 1
                if daily_record.get('termination_risk_flag', False):
                    summary_data['new_rule_conversions']['termination_risk'] += 1
                if daily_record.get('excessive_early_out_flag', False):
                    summary_data['new_rule_conversions']['excessive_early_out'] += 1
                
                # Track flagged employees
                if (daily_record.get('termination_risk_flag', False) or 
                    daily_record.get('excessive_early_out_flag', False) or
                    daily_record.get('excessive_working_hours_flag', False)):
                    summary_data['flagged_employees'] += 1
            
            # 🔥 Update shift analysis from attendance result
            if 'shift_analysis' in attendance_result:
                result_analysis = attendance_result['shift_analysis']
                for key in shift_analysis:
                    shift_analysis[key] += result_analysis.get(key, 0)
            
            # 🔥 Collect flagged records
            if attendance_result.get('flagged_records'):
                for flag in attendance_result['flagged_records']:
                    flag['employee'] = employee
                    all_flagged_records.append(flag)
        
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
            'shift_analysis': shift_analysis,
            'config_applied': processor.get_config_summary() if hasattr(processor, 'get_config_summary') else {},
            'flagged_records': all_flagged_records,
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
        """Handle CSV export of daily attendance report with 🔥 NEW RULE fields."""
        form = DailyAttendanceReportForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please fix form errors before exporting."))
            return self.post(request)
        
        try:
            report_data = self._generate_daily_attendance_report(form.cleaned_data)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="🔥_enhanced_daily_attendance_report_with_new_rules_{form.cleaned_data["report_date"].strftime("%Y%m%d")}.csv"'
            
            writer = csv.writer(response)
            
            # 🔥 Enhanced CSV headers with NEW RULE fields
            writer.writerow([
                'Employee ID', 'Employee Name', 'Department', 'Designation',
                'Date', 'Day', 'Status', 'Original Status', 'Check In', 'Check Out',
                'Working Hours', 'Net Working Hours', 'Late Minutes', 'Early Out Minutes', 
                'Overtime Hours', 'Break Minutes', 'OT Break Minutes',
                'Shift', 'Shift Source', 'Shift Start', 'Shift End', 'Total Logs', 
                'Expected Hours', 'Dynamic Shift Used', 'Shift Confidence', 
                'Multiple Shifts Found', 'Converted From Late', 'Holiday OT', 'Weekend OT',
                # 🔥 NEW RULE COLUMNS
                'Converted From Min Hours', 'Converted To Half Day', 'Converted From Incomplete Punch',
                'Excessive Working Hours Flag', 'Termination Risk Flag', 'Excessive Early Out Flag',
                'Flag Reason', 'Conversion Reason'
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
                    record['original_status'],
                    record['in_time'].strftime('%Y-%m-%d %H:%M:%S') if record['in_time'] else '',
                    record['out_time'].strftime('%Y-%m-%d %H:%M:%S') if record['out_time'] else '',
                    record['working_hours'],
                    record['net_working_hours'],
                    record['late_minutes'],
                    record['early_out_minutes'],
                    record['overtime_hours'],
                    record['break_time_minutes'],
                    record['overtime_break_minutes'],
                    record['shift_name'],
                    record['shift_source'],
                    record['shift_start_time'].strftime('%H:%M') if record['shift_start_time'] else '',
                    record['shift_end_time'].strftime('%H:%M') if record['shift_end_time'] else '',
                    record['total_logs'],
                    record['expected_hours'],
                    'Yes' if record['dynamic_shift_used'] else 'No',
                    f"{record['shift_match_confidence']:.1%}" if record['shift_match_confidence'] else '',
                    ', '.join(record['multiple_shifts_found']) if record['multiple_shifts_found'] else '',
                    'Yes' if record['converted_from_late'] else 'No',
                    'Yes' if record['holiday_overtime'] else 'No',
                    'Yes' if record['weekend_overtime'] else 'No',
                    # 🔥 NEW RULE DATA
                    'Yes' if record['converted_from_minimum_hours'] else 'No',
                    'Yes' if record['converted_to_half_day'] else 'No',
                    'Yes' if record['converted_from_incomplete_punch'] else 'No',
                    'Yes' if record['excessive_working_hours_flag'] else 'No',
                    'Yes' if record['termination_risk_flag'] else 'No',
                    'Yes' if record['excessive_early_out_flag'] else 'No',
                    record['flag_reason'] or '',
                    record['conversion_reason'] or '',
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting enhanced daily attendance report: {str(e)}")
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)
