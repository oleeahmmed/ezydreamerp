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
import calendar

from Hrm.models import *
from .unified_attendance_processor import UnifiedAttendanceProcessor

logger = logging.getLogger(__name__)

class MonthlyAttendanceSummaryForm(forms.Form):
    """Enhanced form for generating monthly attendance summary report with dynamic shift options and 🔥 NEW RULES."""
    
    # Month/Year Selection
    month = forms.ChoiceField(
        label=_("Month"),
        choices=[(i, calendar.month_name[i]) for i in range(1, 13)],
        initial=timezone.now().month,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Select the month for monthly attendance summary.")
    )
    
    year = forms.IntegerField(
        label=_("Year"),
        initial=timezone.now().year,
        min_value=2020,
        max_value=2030,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Select the year for monthly attendance summary.")
    )
    
    # Employee Filtering (EXACT SAME as other reports)
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
    
    # Display Options
    show_absent_employees = forms.BooleanField(
        label=_("Show Absent Employees"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include employees who had absences in the month.")
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
        help_text=_("Show holiday information for the month.")
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
    
    group_by_department = forms.BooleanField(
        label=_("Group by Department"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Group employees by department in the report.")
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

class MonthlyAttendanceSummaryView(LoginRequiredMixin, View):
    """Enhanced view for generating monthly attendance summary reports with dynamic shift options and 🔥 NEW RULES."""
    template_name = 'report/hrm/monthly_attendance_summary.html'
    
    def get(self, request, *args, **kwargs):
        form = MonthlyAttendanceSummaryForm()
        context_data = self._get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        # Handle export request
        if 'export' in request.POST:
            return self._handle_export(request)
        
        form = MonthlyAttendanceSummaryForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                logger.info("Starting monthly attendance summary report generation")
                report_data = self._generate_monthly_summary_report(form.cleaned_data)
                
                logger.info(f"Generated report for {len(report_data['employee_summaries'])} employees")
                
                context_data.update({
                    'report_generated': True,
                    'employee_summaries': report_data['employee_summaries'],
                    'overall_stats': report_data['overall_stats'],
                    'period_overview': report_data['period_overview'],
                    'shift_analysis': report_data.get('shift_analysis', {}),
                    'config_applied': report_data.get('config_applied', {}),
                    'flagged_records': report_data.get('flagged_records', []),
                    'monthly_trends': report_data.get('monthly_trends', {}),
                    'form_data': form.cleaned_data,
                    'employee_count': len(report_data['employee_summaries']),
                    'month_name': calendar.month_name[form.cleaned_data['month']],
                    'year': form.cleaned_data['year'],
                })
                
                messages.success(request, _("🔥 Enhanced monthly attendance summary report generated successfully for {} employees with new rules applied.").format(
                    len(report_data['employee_summaries'])))
                
            except Exception as e:
                logger.error(f"Error generating monthly attendance summary report: {str(e)}", exc_info=True)
                messages.error(request, _("Failed to generate report: {}").format(str(e)))
        else:
            logger.error(f"Form validation errors: {form.errors}")
            messages.error(request, _("Please fix form errors before generating report."))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'shifts': Shift.objects.all().order_by('name'),
            'page_title': _("🔥 Enhanced Monthly Attendance Summary Report with New Rules"),
            'report_generated': False,
        }
    
    def _generate_monthly_summary_report(self, form_data):
        """Generate monthly attendance summary report using enhanced UnifiedAttendanceProcessor with 🔥 NEW RULES."""
        month = form_data['month']
        year = form_data['year']
        
        logger.info(f"Generating monthly report for {calendar.month_name[month]} {year}")
        
        # Calculate start and end dates for the month
        start_date = datetime(year, month, 1).date()
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day).date()
        
        logger.info(f"Date range: {start_date} to {end_date}")
        
        # Update form_data with calculated dates
        form_data['start_date'] = start_date
        form_data['end_date'] = end_date
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        logger.info(f"Found {len(employees)} employees to process")
        
        if not employees:
            logger.warning("No employees found for the given criteria")
            return {
                'employee_summaries': [],
                'overall_stats': self._get_empty_overall_stats(),
                'period_overview': self._get_period_overview(start_date, end_date, month, year, set(), form_data),
                'shift_analysis': {},
                'config_applied': {},
                'flagged_records': [],
                'monthly_trends': {},
            }
        
        # Get holidays for the month
        holidays = Holiday.objects.filter(date__range=[start_date, end_date])
        holiday_dates = set(holidays.values_list('date', flat=True))
        logger.info(f"Found {len(holiday_dates)} holidays in the month")
        
        # Get roster data for the entire month
        roster_data = self._get_roster_data(employees, start_date, end_date)
        
        # 🔥 Initialize enhanced processor with all form options including NEW RULES
        processor = UnifiedAttendanceProcessor(form_data)
        
        employee_summaries = []
        overall_stats = self._get_empty_overall_stats()
        overall_stats['total_employees'] = len(employees)
        
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
            try:
                logger.debug(f"Processing employee: {employee.employee_id}")
                
                # Get ZK attendance logs for the employee in the month
                zk_logs = ZKAttendanceLog.objects.filter(
                    user_id=employee.employee_id,
                    timestamp__date__range=[start_date, end_date]
                ).order_by('timestamp')
                
                logger.debug(f"Found {len(zk_logs)} attendance logs for {employee.employee_id}")
                
                employee_roster_data = roster_data.get(employee.id, {})
                
                # Get leave applications for this employee in the month
                leave_applications = LeaveApplication.objects.filter(
                    employee=employee,
                    status='APP',
                    start_date__lte=end_date,
                    end_date__gte=start_date
                )
                
                logger.debug(f"Found {len(leave_applications)} leave applications for {employee.employee_id}")
                
                # 🔥 Process attendance with enhanced processor including NEW RULES
                attendance_result = processor.process_employee_attendance(
                    employee, start_date, end_date, zk_logs,
                    holidays, leave_applications, employee_roster_data
                )
                
                # Calculate monthly summary data for this employee
                employee_summary = self._calculate_employee_monthly_summary(
                    employee, attendance_result, start_date, end_date, holiday_dates, form_data
                )
                
                if employee_summary:
                    employee_summaries.append(employee_summary)
                    logger.debug(f"Added summary for {employee.employee_id}")
                    
                    # Update overall statistics
                    self._update_overall_stats(overall_stats, employee_summary, attendance_result)
                else:
                    logger.warning(f"No summary generated for employee {employee.employee_id}")
                
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
                        
            except Exception as e:
                logger.error(f"Error processing employee {employee.employee_id}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Successfully processed {len(employee_summaries)} employees")
        
        # Calculate final averages and percentages
        self._finalize_overall_stats(overall_stats, employee_summaries)
        
        # Group by department if requested
        if form_data.get('group_by_department'):
            employee_summaries = self._group_summaries_by_department(employee_summaries)
        
        # Period overview
        period_overview = self._get_period_overview(start_date, end_date, month, year, holiday_dates, form_data)
        
        # Monthly trends (week-by-week analysis)
        monthly_trends = self._calculate_monthly_trends(employee_summaries, start_date, end_date)
        
        return {
            'employee_summaries': employee_summaries,
            'overall_stats': overall_stats,
            'period_overview': period_overview,
            'shift_analysis': shift_analysis,
            'config_applied': processor.get_config_summary() if hasattr(processor, 'get_config_summary') else {},
            'flagged_records': all_flagged_records,
            'monthly_trends': monthly_trends,
        }
    
    def _get_empty_overall_stats(self):
        """Get empty overall stats structure."""
        return {
            'total_employees': 0,
            'total_working_days': 0,
            'total_present_days': 0,
            'total_absent_days': 0,
            'total_late_days': 0,
            'total_leave_days': 0,
            'total_holiday_days': 0,
            'total_half_days': 0,
            'total_overtime_days': 0,
            'total_early_out_days': 0,
            'total_working_hours': Decimal('0'),
            'total_overtime_hours': Decimal('0'),
            'total_break_hours': Decimal('0'),
            'average_attendance_percentage': Decimal('0'),
            'average_punctuality_percentage': Decimal('0'),
            'average_working_hours_per_employee': Decimal('0'),
            'excellent_attendance_count': 0,
            'good_attendance_count': 0,
            'average_attendance_count': 0,
            'poor_attendance_count': 0,
            'employees_with_overtime': 0,
            'perfect_attendance_count': 0,
            'employees_at_risk': 0,
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
    
    def _get_period_overview(self, start_date, end_date, month, year, holiday_dates, form_data):
        """Get period overview data."""
        holidays = Holiday.objects.filter(date__range=[start_date, end_date])
        
        return {
            'month': month,
            'year': year,
            'month_name': calendar.month_name[month],
            'start_date': start_date,
            'end_date': end_date,
            'total_days': (end_date - start_date).days + 1,
            'working_days': self._count_working_days(start_date, end_date, holiday_dates, form_data.get('weekend_days', [4, 5])),
            'weekend_days': self._count_weekend_days(start_date, end_date, form_data.get('weekend_days', [4, 5])),
            'holiday_days': len(holiday_dates),
            'holidays': list(holidays.values('date', 'name')),
        }
    
    def _calculate_employee_monthly_summary(self, employee, attendance_result, start_date, end_date, holiday_dates, form_data):
        """Calculate monthly summary statistics for a single employee."""
        daily_records = attendance_result.get('daily_records', [])
        
        if not daily_records:
            logger.warning(f"No daily records found for employee {employee.employee_id}")
            return None
        
        # Initialize counters
        summary = {
            'employee_id': employee.employee_id,
            'employee_name': employee.get_full_name(),
            'department': employee.department.name if employee.department else 'N/A',
            'designation': employee.designation.name if employee.designation else 'N/A',
            'working_days': 0,
            'present_days': 0,
            'absent_days': 0,
            'late_days': 0,
            'half_days': 0,
            'early_out_days': 0,
            'leave_days': 0,
            'holiday_work_days': 0,
            'weekend_work_days': 0,
            'working_hours': Decimal('0'),
            'overtime_hours': Decimal('0'),
            'overtime_days': 0,
            'total_late_minutes': 0,
            'total_early_out_minutes': 0,
            'perfect_attendance_days': 0,
            'max_consecutive_absent': 0,
            'attendance_percentage': Decimal('0'),
            'punctuality_percentage': Decimal('0'),
            'average_daily_hours': Decimal('0'),
            'attendance_category': 'Poor',
            # 🔥 NEW RULE FIELDS
            'converted_from_minimum_hours': 0,
            'converted_to_half_day': 0,
            'converted_from_incomplete_punch': 0,
            'excessive_working_hours_days': 0,
            'termination_risk_flag': False,
            'excessive_early_out_flag': False,
            'dynamic_shift_days': 0,
            # Monthly specific fields
            'first_week_attendance': Decimal('0'),
            'second_week_attendance': Decimal('0'),
            'third_week_attendance': Decimal('0'),
            'fourth_week_attendance': Decimal('0'),
            'monthly_trend': 'Stable',
        }
        
        consecutive_absent = 0
        max_consecutive = 0
        weekend_day_numbers = [int(d) for d in form_data.get('weekend_days', [4, 5])]
        
        # Weekly attendance tracking
        weekly_stats = [{'present': 0, 'total': 0} for _ in range(4)]
        
        for daily_record in daily_records:
            # Handle both dictionary and object access
            if isinstance(daily_record, dict):
                date = daily_record['date']
                status = daily_record['status']
                late_minutes = daily_record.get('late_minutes', 0)
                early_out_minutes = daily_record.get('early_out_minutes', 0)
                working_hours = daily_record.get('working_hours', 0)
                overtime_hours = daily_record.get('overtime_hours', 0)
            else:
                # Handle object access
                date = getattr(daily_record, 'date', None)
                status = getattr(daily_record, 'status', 'ABS')
                late_minutes = getattr(daily_record, 'late_minutes', 0)
                early_out_minutes = getattr(daily_record, 'early_out_minutes', 0)
                working_hours = getattr(daily_record, 'working_hours', 0)
                overtime_hours = getattr(daily_record, 'overtime_hours', 0)
            
            if not date:
                continue
                
            # Determine which week this date falls into
            week_number = min((date.day - 1) // 7, 3)
            
            # Count working days (exclude weekends and holidays)
            is_weekend = date.weekday() in weekend_day_numbers
            is_holiday = date in holiday_dates
            
            if not is_weekend and not is_holiday:
                summary['working_days'] += 1
                weekly_stats[week_number]['total'] += 1
            
            # Count by status
            if status == 'PRE':
                summary['present_days'] += 1
                consecutive_absent = 0
                weekly_stats[week_number]['present'] += 1
                
                # Check for perfect attendance
                if late_minutes == 0 and early_out_minutes == 0:
                    summary['perfect_attendance_days'] += 1
                    
            elif status == 'ABS':
                if not is_weekend and not is_holiday:
                    summary['absent_days'] += 1
                consecutive_absent += 1
                max_consecutive = max(max_consecutive, consecutive_absent)
                
            elif status == 'LAT':
                summary['late_days'] += 1
                summary['present_days'] += 1
                summary['total_late_minutes'] += late_minutes
                consecutive_absent = 0
                weekly_stats[week_number]['present'] += 1
                
            elif status == 'LEA':
                summary['leave_days'] += 1
                consecutive_absent = 0
                
            elif status == 'HAL':
                summary['half_days'] += 1
                consecutive_absent = 0
                weekly_stats[week_number]['present'] += 0.5
            
            # Count working hours and overtime
            summary['working_hours'] += Decimal(str(working_hours))
            summary['overtime_hours'] += Decimal(str(overtime_hours))
            
            if overtime_hours > 0:
                summary['overtime_days'] += 1
            
            if early_out_minutes > 0:
                summary['early_out_days'] += 1
                summary['total_early_out_minutes'] += early_out_minutes
            
            # Check for holiday/weekend work
            if status in ['PRE', 'LAT'] and is_holiday:
                summary['holiday_work_days'] += 1
            elif status in ['PRE', 'LAT'] and is_weekend:
                summary['weekend_work_days'] += 1
            
            # 🔥 Count NEW RULE conversions - handle both dict and object access
            if isinstance(daily_record, dict):
                if daily_record.get('converted_from_minimum_hours', False):
                    summary['converted_from_minimum_hours'] += 1
                if daily_record.get('converted_to_half_day', False):
                    summary['converted_to_half_day'] += 1
                if daily_record.get('converted_from_incomplete_punch', False):
                    summary['converted_from_incomplete_punch'] += 1
                if daily_record.get('excessive_working_hours_flag', False):
                    summary['excessive_working_hours_days'] += 1
                if daily_record.get('termination_risk_flag', False):
                    summary['termination_risk_flag'] = True
                if daily_record.get('excessive_early_out_flag', False):
                    summary['excessive_early_out_flag'] = True
                if daily_record.get('dynamic_shift_used', False):
                    summary['dynamic_shift_days'] += 1
            else:
                # Handle object access
                if getattr(daily_record, 'converted_from_minimum_hours', False):
                    summary['converted_from_minimum_hours'] += 1
                if getattr(daily_record, 'converted_to_half_day', False):
                    summary['converted_to_half_day'] += 1
                if getattr(daily_record, 'converted_from_incomplete_punch', False):
                    summary['converted_from_incomplete_punch'] += 1
                if getattr(daily_record, 'excessive_working_hours_flag', False):
                    summary['excessive_working_hours_days'] += 1
                if getattr(daily_record, 'termination_risk_flag', False):
                    summary['termination_risk_flag'] = True
                if getattr(daily_record, 'excessive_early_out_flag', False):
                    summary['excessive_early_out_flag'] = True
                if getattr(daily_record, 'dynamic_shift_used', False):
                    summary['dynamic_shift_days'] += 1
        
        summary['max_consecutive_absent'] = max_consecutive
        
        # Calculate weekly attendance percentages
        for i, week_stat in enumerate(weekly_stats):
            if week_stat['total'] > 0:
                week_attendance = (Decimal(str(week_stat['present'])) / Decimal(str(week_stat['total'])) * 100).quantize(Decimal('0.1'))
                if i == 0:
                    summary['first_week_attendance'] = week_attendance
                elif i == 1:
                    summary['second_week_attendance'] = week_attendance
                elif i == 2:
                    summary['third_week_attendance'] = week_attendance
                elif i == 3:
                    summary['fourth_week_attendance'] = week_attendance
        
        # Calculate overall percentages
        if summary['working_days'] > 0:
            summary['attendance_percentage'] = (
                Decimal(str(summary['present_days'])) / Decimal(str(summary['working_days'])) * 100
            ).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            
            if summary['present_days'] > 0:
                summary['punctuality_percentage'] = (
                    Decimal(str(summary['present_days'] - summary['late_days'])) / 
                    Decimal(str(summary['present_days'])) * 100
                ).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                
                summary['average_daily_hours'] = (
                    summary['working_hours'] / Decimal(str(summary['present_days']))
                ).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        
        # Determine monthly trend
        weekly_percentages = [
            summary['first_week_attendance'],
            summary['second_week_attendance'],
            summary['third_week_attendance'],
            summary['fourth_week_attendance']
        ]
        
        # Filter out zero values (weeks that don't exist)
        valid_weeks = [p for p in weekly_percentages if p > 0]
        
        if len(valid_weeks) >= 2:
            if valid_weeks[-1] > valid_weeks[0] + 5:
                summary['monthly_trend'] = 'Improving'
            elif valid_weeks[-1] < valid_weeks[0] - 5:
                summary['monthly_trend'] = 'Declining'
            else:
                summary['monthly_trend'] = 'Stable'
        
        # Determine attendance category
        attendance_pct = summary['attendance_percentage']
        if attendance_pct >= 95:
            summary['attendance_category'] = 'Excellent'
        elif attendance_pct >= 85:
            summary['attendance_category'] = 'Good'
        elif attendance_pct >= 70:
            summary['attendance_category'] = 'Average'
        else:
            summary['attendance_category'] = 'Poor'
        
        return summary
    
    def _update_overall_stats(self, overall_stats, employee_summary, attendance_result):
        """Update overall statistics with employee data."""
        overall_stats['total_working_days'] += employee_summary['working_days']
        overall_stats['total_present_days'] += employee_summary['present_days']
        overall_stats['total_absent_days'] += employee_summary['absent_days']
        overall_stats['total_late_days'] += employee_summary['late_days']
        overall_stats['total_leave_days'] += employee_summary['leave_days']
        overall_stats['total_half_days'] += employee_summary['half_days']
        overall_stats['total_overtime_days'] += employee_summary['overtime_days']
        overall_stats['total_early_out_days'] += employee_summary['early_out_days']
        overall_stats['total_working_hours'] += employee_summary['working_hours']
        overall_stats['total_overtime_hours'] += employee_summary['overtime_hours']
        
        # Count by category
        category = employee_summary['attendance_category']
        if category == 'Excellent':
            overall_stats['excellent_attendance_count'] += 1
        elif category == 'Good':
            overall_stats['good_attendance_count'] += 1
        elif category == 'Average':
            overall_stats['average_attendance_count'] += 1
        else:
            overall_stats['poor_attendance_count'] += 1
        
        if employee_summary['overtime_hours'] > 0:
            overall_stats['employees_with_overtime'] += 1
        
        if employee_summary['attendance_percentage'] == 100:
            overall_stats['perfect_attendance_count'] += 1
        
        if employee_summary['attendance_percentage'] < 70:
            overall_stats['employees_at_risk'] += 1
        
        if employee_summary['dynamic_shift_days'] > 0:
            overall_stats['dynamic_detection_count'] += 1
        
        # 🔥 Count NEW RULE conversions
        if employee_summary['converted_from_minimum_hours'] > 0:
            overall_stats['new_rule_conversions']['minimum_hours'] += 1
        if employee_summary['converted_to_half_day'] > 0:
            overall_stats['new_rule_conversions']['half_day'] += 1
        if employee_summary['converted_from_incomplete_punch'] > 0:
            overall_stats['new_rule_conversions']['incomplete_punch'] += 1
        if employee_summary['excessive_working_hours_days'] > 0:
            overall_stats['new_rule_conversions']['excessive_hours'] += 1
        if employee_summary['termination_risk_flag']:
            overall_stats['new_rule_conversions']['termination_risk'] += 1
        if employee_summary['excessive_early_out_flag']:
            overall_stats['new_rule_conversions']['excessive_early_out'] += 1
        
        # Count flagged employees
        if (employee_summary['termination_risk_flag'] or 
            employee_summary['excessive_early_out_flag'] or
            employee_summary['excessive_working_hours_days'] > 0):
            overall_stats['flagged_employees'] += 1
    
    def _finalize_overall_stats(self, overall_stats, employee_summaries):
        """Calculate final averages and percentages."""
        total_employees = len(employee_summaries)
        
        if total_employees > 0:
            # Calculate average attendance percentage
            total_attendance = sum(emp['attendance_percentage'] for emp in employee_summaries)
            overall_stats['average_attendance_percentage'] = (
                total_attendance / total_employees
            ).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            
            # Calculate average punctuality percentage
            total_punctuality = sum(emp['punctuality_percentage'] for emp in employee_summaries)
            overall_stats['average_punctuality_percentage'] = (
                total_punctuality / total_employees
            ).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            
            # Calculate average working hours per employee
            overall_stats['average_working_hours_per_employee'] = (
                overall_stats['total_working_hours'] / total_employees
            ).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    
    def _calculate_monthly_trends(self, employee_summaries, start_date, end_date):
        """Calculate monthly trends and patterns."""
        trends = {
            'improving_employees': 0,
            'declining_employees': 0,
            'stable_employees': 0,
            'best_performing_week': 1,
            'worst_performing_week': 1,
            'weekly_averages': [Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0')],
        }
        
        if not employee_summaries:
            return trends
        
        # Count trend categories
        for emp in employee_summaries:
            trend = emp.get('monthly_trend', 'Stable')
            if trend == 'Improving':
                trends['improving_employees'] += 1
            elif trend == 'Declining':
                trends['declining_employees'] += 1
            else:
                trends['stable_employees'] += 1
        
        # Calculate weekly averages
        weekly_totals = [Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0')]
        weekly_counts = [0, 0, 0, 0]
        
        for emp in employee_summaries:
            weekly_attendances = [
                emp.get('first_week_attendance', Decimal('0')),
                emp.get('second_week_attendance', Decimal('0')),
                emp.get('third_week_attendance', Decimal('0')),
                emp.get('fourth_week_attendance', Decimal('0'))
            ]
            
            for i, attendance in enumerate(weekly_attendances):
                if attendance > 0:
                    weekly_totals[i] += attendance
                    weekly_counts[i] += 1
        
        # Calculate averages and find best/worst weeks
        best_avg = Decimal('0')
        worst_avg = Decimal('100')
        
        for i in range(4):
            if weekly_counts[i] > 0:
                avg = (weekly_totals[i] / weekly_counts[i]).quantize(Decimal('0.1'))
                trends['weekly_averages'][i] = avg
                
                if avg > best_avg:
                    best_avg = avg
                    trends['best_performing_week'] = i + 1
                
                if avg < worst_avg:
                    worst_avg = avg
                    trends['worst_performing_week'] = i + 1
        
        return trends
    
    def _count_working_days(self, start_date, end_date, holiday_dates, weekend_days):
        """Count working days in the date range."""
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
        """Count weekend days in the date range."""
        weekend_count = 0
        current_date = start_date
        weekend_day_numbers = [int(d) for d in weekend_days]
        
        while current_date <= end_date:
            if current_date.weekday() in weekend_day_numbers:
                weekend_count += 1
            current_date += timedelta(days=1)
        
        return weekend_count
    
    def _get_filtered_employees(self, form_data):
        """Get employees based on filter criteria."""
        employee_filter = form_data['employee_filter']
        
        queryset = Employee.objects.filter(is_active=True).select_related(
            'department', 'designation', 'default_shift'
        )
        
        if employee_filter == 'department':
            departments = form_data.get('departments', [])
            if departments:
                return queryset.filter(department__in=departments)
        elif employee_filter == 'designation':
            designations = form_data.get('designations', [])
            if designations:
                return queryset.filter(designation__in=designations)
        elif employee_filter == 'specific':
            employee_ids_str = form_data.get('employee_ids', '')
            if employee_ids_str:
                employee_ids = [id.strip() for id in employee_ids_str.split(',') if id.strip()]
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
    
    def _group_summaries_by_department(self, employee_summaries):
        """Group employee summaries by department."""
        from collections import defaultdict, OrderedDict
        
        grouped = defaultdict(list)
        
        for summary in employee_summaries:
            dept = summary['department']
            grouped[dept].append(summary)
        
        # Sort departments and employees within each department
        result = OrderedDict()
        for dept in sorted(grouped.keys()):
            result[dept] = sorted(grouped[dept], key=lambda x: x['employee_id'])
        
        return result
    
    def _handle_export(self, request):
        """Handle CSV export of monthly attendance summary report with 🔥 NEW RULE fields."""
        form = MonthlyAttendanceSummaryForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please fix form errors before exporting."))
            return self.post(request)
        
        try:
            report_data = self._generate_monthly_summary_report(form.cleaned_data)
            
            month_name = calendar.month_name[form.cleaned_data['month']]
            year = form.cleaned_data['year']
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="🔥_enhanced_monthly_attendance_summary_with_new_rules_{month_name}_{year}.csv"'
            
            writer = csv.writer(response)
            
            # 🔥 Enhanced CSV headers with NEW RULE fields
            writer.writerow([
                'Employee ID', 'Employee Name', 'Department', 'Designation',
                'Working Days', 'Present Days', 'Absent Days', 'Late Days',
                'Half Days', 'Early Out Days', 'Leave Days', 'Holiday Work Days',
                'Weekend Work Days', 'Working Hours', 'Overtime Hours', 'Overtime Days',
                'Total Late Minutes', 'Total Early Out Minutes', 'Perfect Attendance Days',
                'Max Consecutive Absent', 'Attendance %', 'Punctuality %', 
                'Average Daily Hours', 'Category', 'Monthly Trend',
                'Week 1 Attendance %', 'Week 2 Attendance %', 'Week 3 Attendance %', 'Week 4 Attendance %',
                # 🔥 NEW RULE COLUMNS
                'Converted From Min Hours', 'Converted To Half Day', 'Converted From Incomplete Punch',
                'Excessive Working Hours Days', 'Termination Risk Flag', 'Excessive Early Out Flag',
                'Dynamic Shift Days'
            ])
            
            for summary in report_data['employee_summaries']:
                writer.writerow([
                    summary['employee_id'],
                    summary['employee_name'],
                    summary['department'],
                    summary['designation'],
                    summary['working_days'],
                    summary['present_days'],
                    summary['absent_days'],
                    summary['late_days'],
                    summary['half_days'],
                    summary['early_out_days'],
                    summary['leave_days'],
                    summary['holiday_work_days'],
                    summary['weekend_work_days'],
                    float(summary['working_hours']),
                    float(summary['overtime_hours']),
                    summary['overtime_days'],
                    summary['total_late_minutes'],
                    summary['total_early_out_minutes'],
                    summary['perfect_attendance_days'],
                    summary['max_consecutive_absent'],
                    float(summary['attendance_percentage']),
                    float(summary['punctuality_percentage']),
                    float(summary['average_daily_hours']),
                    summary['attendance_category'],
                    summary['monthly_trend'],
                    float(summary['first_week_attendance']),
                    float(summary['second_week_attendance']),
                    float(summary['third_week_attendance']),
                    float(summary['fourth_week_attendance']),
                    # 🔥 NEW RULE DATA
                    summary['converted_from_minimum_hours'],
                    summary['converted_to_half_day'],
                    summary['converted_from_incomplete_punch'],
                    summary['excessive_working_hours_days'],
                    'Yes' if summary['termination_risk_flag'] else 'No',
                    'Yes' if summary['excessive_early_out_flag'] else 'No',
                    summary['dynamic_shift_days'],
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting enhanced monthly attendance summary report: {str(e)}")
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)