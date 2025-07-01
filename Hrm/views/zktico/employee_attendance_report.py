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
from decimal import Decimal, ROUND_HALF_UP

from Hrm.models import *
from .unified_attendance_processor import UnifiedAttendanceProcessor

logger = logging.getLogger(__name__)

class EmployeeDetailedAttendanceReportForm(forms.Form):
    """Enhanced form for generating employee detailed attendance report with dynamic shift options and 🔥 NEW RULES."""
    
    # Employee Selection (Single employee instead of multiple)
    employee = forms.ModelChoiceField(
        label=_("Select Employee"),
        queryset=Employee.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Select the employee for detailed attendance report.")
    )
    
    # Date Range Selection
    start_date = forms.DateField(
        label=_("Start Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the start date for detailed attendance report.")
    )
    
    end_date = forms.DateField(
        label=_("End Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the end date for detailed attendance report.")
    )
    
    # 🔥 NEW RULE 1: Minimum Working Hours Rule (EXACT SAME)
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
    
    # 🔥 NEW RULE 2: Half Day Rule Based on Working Hours (EXACT SAME)
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
    
    # 🔥 NEW RULE 3: In-time and Out-time Both Must Rule (EXACT SAME)
    require_both_in_and_out = forms.BooleanField(
        label=_("🔥 Require Both In-time and Out-time"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Mark as Absent if either check-in or check-out is missing")
    )
    
    # 🔥 NEW RULE 4: Maximum Allowable Working Hours Rule (EXACT SAME)
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
    
    # 🔥 NEW RULE 5: Dynamic Shift Detection Override Rule (EXACT SAME)
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
    
    # 🔥 NEW RULE 6: Grace Time per Shift Instead of Global (EXACT SAME)
    use_shift_grace_time = forms.BooleanField(
        label=_("🔥 Use Shift-Specific Grace Time"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Use grace time defined in shift settings instead of global grace time")
    )
    
    # 🔥 NEW RULE 7: Consecutive Absence to Flag as Termination Risk (EXACT SAME)
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
    
    # 🔥 NEW RULE 8: Max Early Out Threshold (EXACT SAME)
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
    
    # 🔥 ENHANCED SHIFT DETECTION OPTIONS (EXACT SAME)
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
    
    # 🔥 ADVANCED OVERTIME CONFIGURATION (EXACT SAME)
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
    
    # 🔥 ENHANCED BREAK TIME CONFIGURATION (EXACT SAME)
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
    
    # Display Options (EXACT SAME)
    show_absent_employees = forms.BooleanField(
        label=_("Show Absent Days"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include days when employee was absent.")
    )
    
    show_leave_employees = forms.BooleanField(
        label=_("Show Leave Days"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include days when employee was on approved leave.")
    )
    
    show_holiday_status = forms.BooleanField(
        label=_("Show Holiday Status"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Show holiday information for each day.")
    )
    
    include_roster_info = forms.BooleanField(
        label=_("Include Roster Information"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Show roster and shift information for each day.")
    )
    
    show_shift_analysis = forms.BooleanField(
        label=_("Show Shift Analysis"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Display detailed shift detection and analysis information.")
    )
    
    show_raw_logs = forms.BooleanField(
        label=_("Show Raw Attendance Logs"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Display raw ZK attendance logs for each day.")
    )
    
    # Weekend and Grace Settings (EXACT SAME)
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
    
    # 🔥 ADVANCED RULES (EXACT SAME)
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
    
    # 🔥 EMPLOYEE OVERRIDE SETTINGS (EXACT SAME)
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

class EmployeeDetailedAttendanceReportView(LoginRequiredMixin, View):
    """Enhanced view for generating employee detailed attendance reports with dynamic shift options and 🔥 NEW RULES."""
    template_name = 'report/hrm/employee_detailed_attendance_report.html'
    
    def get(self, request, *args, **kwargs):
        form = EmployeeDetailedAttendanceReportForm()
        
        # Set default date range to current month
        today = timezone.now().date()
        first_day = today.replace(day=1)
        form.fields['start_date'].initial = first_day
        form.fields['end_date'].initial = today
        
        context_data = self._get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        # Handle export request
        if 'export' in request.POST:
            return self._handle_export(request)
        
        form = EmployeeDetailedAttendanceReportForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                report_data = self._generate_employee_detailed_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'employee_info': report_data['employee_info'],
                    'daily_records': report_data['daily_records'],
                    'summary_stats': report_data['summary_stats'],
                    'period_overview': report_data['period_overview'],
                    'shift_analysis': report_data.get('shift_analysis', {}),
                    'config_applied': report_data.get('config_applied', {}),
                    'flagged_records': report_data.get('flagged_records', []),
                    'raw_logs': report_data.get('raw_logs', {}),
                    'form_data': form.cleaned_data,
                    'total_days': len(report_data['daily_records']),
                    'start_date': form.cleaned_data['start_date'],
                    'end_date': form.cleaned_data['end_date'],
                })
                
                messages.success(request, _("🔥 Enhanced employee detailed attendance report generated successfully for {} with new rules applied.").format(
                    report_data['employee_info']['employee_name']))
                
            except Exception as e:
                logger.error(f"Error generating employee detailed attendance report: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'shifts': Shift.objects.all().order_by('name'),
            'employees': Employee.objects.filter(is_active=True).order_by('employee_id'),
            'page_title': _("🔥 Enhanced Employee Detailed Attendance Report with New Rules"),
            'report_generated': False,
        }
    
    def _generate_employee_detailed_report(self, form_data):
        """Generate employee detailed attendance report using enhanced UnifiedAttendanceProcessor with 🔥 NEW RULES."""
        employee = form_data['employee']
        start_date = form_data['start_date']
        end_date = form_data['end_date']
        
        # Get holidays for the date range
        holidays = Holiday.objects.filter(date__range=[start_date, end_date])
        holiday_dates = set(holidays.values_list('date', flat=True))
        
        # Get ZK attendance logs for the employee in the date range
        zk_logs = ZKAttendanceLog.objects.filter(
            user_id=employee.employee_id,
            timestamp__date__range=[start_date, end_date]
        ).order_by('timestamp')
        
        # Get roster data for the employee
        roster_data = self._get_roster_data([employee], start_date, end_date)
        employee_roster_data = roster_data.get(employee.id, {})
        
        # Get leave applications for this employee in the date range
        leave_applications = LeaveApplication.objects.filter(
            employee=employee,
            status='APP',
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        # 🔥 Initialize enhanced processor with all form options including NEW RULES
        processor = UnifiedAttendanceProcessor(form_data)
        
        # 🔥 Process attendance with enhanced processor including NEW RULES
        attendance_result = processor.process_employee_attendance(
            employee, start_date, end_date, zk_logs,
            holidays, leave_applications, employee_roster_data
        )
        
        # Prepare daily records for display
        daily_records = []
        for daily_record in attendance_result.get('daily_records', []):
            # Apply display filters
            should_include = True
            
            if not form_data['show_absent_employees'] and daily_record['status'] == 'ABS':
                should_include = False
            elif not form_data['show_leave_employees'] and daily_record['status'] == 'LEA':
                should_include = False
            
            if should_include:
                # 🔥 Create enhanced daily record for display with NEW RULE fields
                display_record = {
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
                    'is_holiday': daily_record['date'] in holiday_dates,
                    'is_weekend': daily_record['date'].weekday() in [int(d) for d in form_data.get('weekend_days', [4, 5])],
                    
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
                
                daily_records.append(display_record)
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(daily_records, start_date, end_date, holiday_dates, form_data)
        
        # Period overview
        period_overview = {
            'start_date': start_date,
            'end_date': end_date,
            'total_days': (end_date - start_date).days + 1,
            'working_days': self._count_working_days(start_date, end_date, holiday_dates, form_data['weekend_days']),
            'weekend_days': self._count_weekend_days(start_date, end_date, form_data['weekend_days']),
            'holiday_days': len([d for d in holiday_dates if start_date <= d <= end_date]),
        }
        
        # Employee information
        employee_info = {
            'employee_id': employee.employee_id,
            'employee_name': employee.get_full_name(),
            'department': employee.department.name if employee.department else 'N/A',
            'designation': employee.designation.name if employee.designation else 'N/A',
            'default_shift': employee.default_shift.name if employee.default_shift else 'N/A',
            'join_date': employee.date_joined if hasattr(employee, 'date_joined') else 'N/A',
        }
        
        # Raw logs (if requested)
        raw_logs = {}
        if form_data.get('show_raw_logs', False):
            for record in daily_records:
                date = record['date']
                logs = zk_logs.filter(timestamp__date=date).order_by('timestamp')
                raw_logs[date] = [
                    {
                        'timestamp': log.timestamp,
                        'punch_type': log.punch_type,
                        'device_id': log.device_id,
                        'verification_type': getattr(log, 'verification_type', 'Unknown'),
                    }
                    for log in logs
                ]
        
        return {
            'employee_info': employee_info,
            'daily_records': daily_records,
            'summary_stats': summary_stats,
            'period_overview': period_overview,
            'shift_analysis': attendance_result.get('shift_analysis', {}),
            'config_applied': processor.get_config_summary() if hasattr(processor, 'get_config_summary') else {},
            'flagged_records': attendance_result.get('flagged_records', []),
            'raw_logs': raw_logs,
        }
    
    def _calculate_summary_stats(self, daily_records, start_date, end_date, holiday_dates, form_data):
        """Calculate summary statistics from daily records."""
        stats = {
            'total_days': len(daily_records),
            'present_days': 0,
            'absent_days': 0,
            'late_days': 0,
            'leave_days': 0,
            'half_days': 0,
            'overtime_days': 0,
            'early_out_days': 0,
            'holiday_work_days': 0,
            'weekend_work_days': 0,
            'perfect_attendance_days': 0,
            'total_working_hours': Decimal('0'),
            'total_overtime_hours': Decimal('0'),
            'total_late_minutes': 0,
            'total_early_out_minutes': 0,
            'max_consecutive_absent': 0,
            'attendance_percentage': Decimal('0'),
            'punctuality_percentage': Decimal('0'),
            'average_daily_hours': Decimal('0'),
            'attendance_category': 'Poor',
            # 🔥 NEW RULE STATS
            'converted_from_minimum_hours': 0,
            'converted_to_half_day': 0,
            'converted_from_incomplete_punch': 0,
            'excessive_working_hours_days': 0,
            'termination_risk_days': 0,
            'excessive_early_out_days': 0,
            'dynamic_shift_days': 0,
        }
        
        consecutive_absent = 0
        max_consecutive = 0
        working_days = 0
        weekend_day_numbers = [int(d) for d in form_data.get('weekend_days', [4, 5])]
        
        for record in daily_records:
            status = record['status']
            date = record['date']
            
            # Count working days
            is_weekend = date.weekday() in weekend_day_numbers
            is_holiday = date in holiday_dates
            
            if not is_weekend and not is_holiday:
                working_days += 1
            
            # Count by status
            if status == 'PRE':
                stats['present_days'] += 1
                consecutive_absent = 0
                
                # Check for perfect attendance
                if record['late_minutes'] == 0 and record['early_out_minutes'] == 0:
                    stats['perfect_attendance_days'] += 1
                    
            elif status == 'ABS':
                if not is_weekend and not is_holiday:
                    stats['absent_days'] += 1
                consecutive_absent += 1
                max_consecutive = max(max_consecutive, consecutive_absent)
                
            elif status == 'LAT':
                stats['late_days'] += 1
                stats['present_days'] += 1
                stats['total_late_minutes'] += record['late_minutes']
                consecutive_absent = 0
                
            elif status == 'LEA':
                stats['leave_days'] += 1
                consecutive_absent = 0
                
            elif status == 'HAL':
                stats['half_days'] += 1
                consecutive_absent = 0
            
            # Count working hours and overtime
            stats['total_working_hours'] += Decimal(str(record['working_hours']))
            stats['total_overtime_hours'] += Decimal(str(record['overtime_hours']))
            
            if record['overtime_hours'] > 0:
                stats['overtime_days'] += 1
            
            if record['early_out_minutes'] > 0:
                stats['early_out_days'] += 1
                stats['total_early_out_minutes'] += record['early_out_minutes']
            
            # Check for holiday/weekend work
            if status in ['PRE', 'LAT'] and is_holiday:
                stats['holiday_work_days'] += 1
            elif status in ['PRE', 'LAT'] and is_weekend:
                stats['weekend_work_days'] += 1
            
            # 🔥 Count NEW RULE conversions
            if record.get('converted_from_minimum_hours', False):
                stats['converted_from_minimum_hours'] += 1
            if record.get('converted_to_half_day', False):
                stats['converted_to_half_day'] += 1
            if record.get('converted_from_incomplete_punch', False):
                stats['converted_from_incomplete_punch'] += 1
            if record.get('excessive_working_hours_flag', False):
                stats['excessive_working_hours_days'] += 1
            if record.get('termination_risk_flag', False):
                stats['termination_risk_days'] += 1
            if record.get('excessive_early_out_flag', False):
                stats['excessive_early_out_days'] += 1
            if record.get('dynamic_shift_used', False):
                stats['dynamic_shift_days'] += 1
        
        stats['max_consecutive_absent'] = max_consecutive
        
        # Calculate percentages
        if working_days > 0:
            stats['attendance_percentage'] = (
                Decimal(stats['present_days']) / Decimal(working_days) * 100
            ).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            
            if stats['present_days'] > 0:
                stats['punctuality_percentage'] = (
                    Decimal(stats['present_days'] - stats['late_days']) / 
                    Decimal(stats['present_days']) * 100
                ).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                
                stats['average_daily_hours'] = (
                    stats['total_working_hours'] / Decimal(stats['present_days'])
                ).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        
        # Determine attendance category
        attendance_pct = stats['attendance_percentage']
        if attendance_pct >= 95:
            stats['attendance_category'] = 'Excellent'
        elif attendance_pct >= 85:
            stats['attendance_category'] = 'Good'
        elif attendance_pct >= 70:
            stats['attendance_category'] = 'Average'
        else:
            stats['attendance_category'] = 'Poor'
        
        return stats
    
    def _get_status_display(self, status):
        """Get human-readable status display (EXACT SAME as daily report)."""
        status_map = {
            'PRE': _('Present'),
            'ABS': _('Absent'),
            'LAT': _('Late'),
            'LEA': _('Leave'),
            'HOL': _('Holiday'),
            'HAL': _('Half Day'),
        }
        return status_map.get(status, status)
    
    def _count_working_days(self, start_date, end_date, holiday_dates, weekend_days):
        """Count working days in the date range (EXACT SAME as summary report)."""
        working_days = 0
        current_date = start_date
        weekend_day_numbers = [int(d) for d in weekend_days]
        
        while current_date <= end_date:
            if (current_date not in holiday_dates and 
                current_date.weekday() not in weekend_day_numbers):
                working_days += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def _count_weekend_days(self, start_date, end_date, weekend_days):
        """Count weekend days in the date range (EXACT SAME as summary report)."""
        weekend_count = 0
        current_date = start_date
        weekend_day_numbers = [int(d) for d in weekend_days]
        
        while current_date <= end_date:
            if current_date.weekday() in weekend_day_numbers:
                weekend_count += 1
            current_date += timedelta(days=1)
        
        return weekend_count
    
    def _get_roster_data(self, employees, start_date, end_date):
        """Get roster data for employees (EXACT SAME as daily report)."""
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
        """Handle CSV export of employee detailed attendance report with 🔥 NEW RULE fields."""
        form = EmployeeDetailedAttendanceReportForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please fix form errors before exporting."))
            return self.post(request)
        
        try:
            report_data = self._generate_employee_detailed_report(form.cleaned_data)
            
            employee_name = report_data['employee_info']['employee_name'].replace(' ', '_')
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="🔥_enhanced_employee_detailed_report_with_new_rules_{employee_name}_{form.cleaned_data["start_date"].strftime("%Y%m%d")}_{form.cleaned_data["end_date"].strftime("%Y%m%d")}.csv"'
            
            writer = csv.writer(response)
            
            # 🔥 Enhanced CSV headers with NEW RULE fields
            writer.writerow([
                'Date', 'Day', 'Status', 'Original Status', 'Check In', 'Check Out',
                'Working Hours', 'Net Working Hours', 'Late Minutes', 'Early Out Minutes', 
                'Overtime Hours', 'Break Minutes', 'OT Break Minutes',
                'Shift', 'Shift Source', 'Shift Start', 'Shift End', 'Total Logs', 
                'Expected Hours', 'Is Holiday', 'Is Weekend', 'Dynamic Shift Used', 
                'Shift Confidence', 'Multiple Shifts Found', 'Converted From Late', 
                'Holiday OT', 'Weekend OT',
                # 🔥 NEW RULE COLUMNS
                'Converted From Min Hours', 'Converted To Half Day', 'Converted From Incomplete Punch',
                'Excessive Working Hours Flag', 'Termination Risk Flag', 'Excessive Early Out Flag',
                'Flag Reason', 'Conversion Reason'
            ])
            
            for record in report_data['daily_records']:
                writer.writerow([
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
                    'Yes' if record['is_holiday'] else 'No',
                    'Yes' if record['is_weekend'] else 'No',
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
            logger.error(f"Error exporting enhanced employee detailed attendance report: {str(e)}")
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)
