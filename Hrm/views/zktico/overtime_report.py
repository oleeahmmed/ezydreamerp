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
import calendar

from Hrm.models import *
from .unified_attendance_processor import UnifiedAttendanceProcessor

logger = logging.getLogger(__name__)

class OvertimeReportForm(forms.Form):
    """Enhanced form for generating comprehensive overtime reports."""
    
    # Date Range Selection
    start_date = forms.DateField(
        label=_("Start Date"),
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text=_("Select the start date for the overtime report.")
    )
    
    end_date = forms.DateField(
        label=_("End Date"),
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text=_("Select the end date for the overtime report.")
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
    
    # 🔥 OVERTIME FILTERING OPTIONS
    minimum_overtime_hours = forms.FloatField(
        label=_("Minimum Overtime Hours"),
        initial=0.0,
        min_value=0.0,
        max_value=24.0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        help_text=_("Show only employees with at least this many overtime hours.")
    )
    
    overtime_type_filter = forms.ChoiceField(
        label=_("Overtime Type Filter"),
        choices=[
            ('all', _('All Overtime Types')),
            ('regular', _('Regular Overtime Only')),
            ('holiday', _('Holiday Overtime Only')),
            ('weekend', _('Weekend Overtime Only')),
        ],
        initial='all',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    
    show_daily_breakdown = forms.BooleanField(
        label=_("Show Daily Breakdown"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include detailed daily overtime breakdown for each employee.")
    )
    
    group_by_department = forms.BooleanField(
        label=_("Group by Department"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Group employees by department in the report.")
    )
    
    include_zero_overtime = forms.BooleanField(
        label=_("Include Zero Overtime Days"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include days with zero overtime in daily breakdown.")
    )
    
    # 🔥 ENHANCED SHIFT DETECTION OPTIONS
    enable_dynamic_shift_detection = forms.BooleanField(
        label=_("Enable Dynamic Shift Detection"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Automatically detect shifts based on actual check-in/out times.")
    )
    
    dynamic_shift_tolerance_minutes = forms.IntegerField(
        label=_("Dynamic Shift Tolerance (Minutes)"),
        initial=30,
        min_value=5,
        max_value=120,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    multiple_shift_priority = forms.ChoiceField(
        label=_("Multiple Shift Match Priority"),
        choices=[
            ('least_break', _('Least Break Time')),
            ('shortest_duration', _('Shortest Duration')),
            ('alphabetical', _('Alphabetical Order')),
        ],
        initial='least_break',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    
    # 🔥 ADVANCED OVERTIME CONFIGURATION
    overtime_calculation_method = forms.ChoiceField(
        label=_("Overtime Calculation Method"),
        choices=[
            ('shift_based', _('Shift-Based (After shift end time)')),
            ('expected_hours', _('Expected Hours-Based (After expected work hours)')),
        ],
        initial='shift_based',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    
    holiday_overtime_full_day = forms.BooleanField(
        label=_("Holiday Overtime - Full Day"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    
    weekend_overtime_full_day = forms.BooleanField(
        label=_("Weekend Overtime - Full Day"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    
    late_affects_overtime = forms.BooleanField(
        label=_("Late Arrival Affects Overtime"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    
    separate_ot_break_time = forms.IntegerField(
        label=_("Separate Overtime Break Time (Minutes)"),
        initial=0,
        min_value=0,
        max_value=120,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    # 🔥 ENHANCED BREAK TIME CONFIGURATION
    use_shift_break_time = forms.BooleanField(
        label=_("Use Shift-Specific Break Time"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    
    default_break_minutes = forms.IntegerField(
        label=_("Default Break Time (Minutes)"),
        initial=60,
        min_value=0,
        max_value=240,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    break_deduction_method = forms.ChoiceField(
        label=_("Break Deduction Method"),
        choices=[
            ('fixed', _('Fixed Break Time')),
            ('proportional', _('Proportional to Working Hours')),
        ],
        initial='fixed',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    
    # Weekend and Grace Settings
    weekend_days = forms.MultipleChoiceField(
        label=_("Weekend Days"),
        choices=[
            ('0', _('Monday')), ('1', _('Tuesday')), ('2', _('Wednesday')),
            ('3', _('Thursday')), ('4', _('Friday')), ('5', _('Saturday')), ('6', _('Sunday'))
        ],
        initial=['4', '5'],  # Friday and Saturday as strings
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )
    
    grace_minutes = forms.IntegerField(
        label=_("Grace Minutes"),
        initial=15,
        min_value=0,
        max_value=120,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    early_out_threshold_minutes = forms.IntegerField(
        label=_("Early Out Threshold (Minutes)"),
        initial=30,
        min_value=0,
        max_value=240,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    overtime_start_after_minutes = forms.IntegerField(
        label=_("Overtime Start After (Minutes)"),
        initial=15,
        min_value=0,
        max_value=120,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    minimum_overtime_minutes = forms.IntegerField(
        label=_("Minimum Overtime (Minutes)"),
        initial=60,
        min_value=0,
        max_value=480,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    # 🔥 ADVANCED RULES
    late_to_absent_days = forms.IntegerField(
        label=_("Late to Absent Conversion (Days)"),
        initial=3,
        min_value=1,
        max_value=10,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    
    holiday_before_after_absent = forms.BooleanField(
        label=_("Holiday Before/After Absent Rule"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    
    weekend_before_after_absent = forms.BooleanField(
        label=_("Weekend Before/After Absent Rule"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    
    # 🔥 EMPLOYEE OVERRIDE SETTINGS
    use_employee_specific_grace = forms.BooleanField(
        label=_("Use Employee-Specific Grace Time"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    
    use_employee_specific_overtime = forms.BooleanField(
        label=_("Use Employee-Specific Overtime Rules"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    
    use_employee_expected_hours = forms.BooleanField(
        label=_("Use Employee Expected Hours"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    
    # 🔥 OVERTIME ANALYSIS OPTIONS
    show_overtime_trends = forms.BooleanField(
        label=_("Show Overtime Trends"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include overtime trend analysis (weekly patterns, etc.).")
    )
    
    show_cost_analysis = forms.BooleanField(
        label=_("Show Cost Analysis"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include overtime cost analysis (requires hourly rates).")
    )
    
    overtime_rate_multiplier = forms.FloatField(
        label=_("Overtime Rate Multiplier"),
        initial=1.5,
        min_value=1.0,
        max_value=3.0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        help_text=_("Multiplier for overtime rate calculation (e.g., 1.5 for time-and-a-half).")
    )

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(_("Start date must be before end date."))
            
            # Check if date range is not too large (max 6 months for overtime reports)
            if (end_date - start_date).days > 180:
                raise forms.ValidationError(_("Date range cannot exceed 180 days for overtime reports."))
            
            # Check if dates are not in the future
            today = timezone.now().date()
            if start_date > today:
                raise forms.ValidationError(_("Start date cannot be in the future."))
            if end_date > today:
                cleaned_data['end_date'] = today
        
        # Ensure None values are converted to defaults for required fields
        if cleaned_data.get('grace_minutes') is None:
            cleaned_data['grace_minutes'] = 15
        if cleaned_data.get('early_out_threshold_minutes') is None:
            cleaned_data['early_out_threshold_minutes'] = 30
        if cleaned_data.get('overtime_start_after_minutes') is None:
            cleaned_data['overtime_start_after_minutes'] = 15
        if cleaned_data.get('minimum_overtime_minutes') is None:
            cleaned_data['minimum_overtime_minutes'] = 60
        if cleaned_data.get('late_to_absent_days') is None:
            cleaned_data['late_to_absent_days'] = 3
        if cleaned_data.get('dynamic_shift_tolerance_minutes') is None:
            cleaned_data['dynamic_shift_tolerance_minutes'] = 30
        if cleaned_data.get('default_break_minutes') is None:
            cleaned_data['default_break_minutes'] = 60
        if cleaned_data.get('separate_ot_break_time') is None:
            cleaned_data['separate_ot_break_time'] = 0
        if cleaned_data.get('minimum_overtime_hours') is None:
            cleaned_data['minimum_overtime_hours'] = 0.0
        if cleaned_data.get('overtime_rate_multiplier') is None:
            cleaned_data['overtime_rate_multiplier'] = 1.5
        
        return cleaned_data

    def clean_weekend_days(self):
        """Convert weekend days to integers."""
        weekend_days = self.cleaned_data.get('weekend_days', [])
        try:
            return [int(day) for day in weekend_days]
        except (ValueError, TypeError):
            raise forms.ValidationError(_("Invalid weekend day format."))

class OvertimeReportView(LoginRequiredMixin, View):
    """Enhanced view for generating comprehensive overtime reports."""
    template_name = 'report/hrm/overtime_report.html'
    
    def get(self, request, *args, **kwargs):
        form = OvertimeReportForm()
        
        # Set default date range (last 30 days)
        today = timezone.now().date()
        form.fields['end_date'].initial = today
        form.fields['start_date'].initial = today - timedelta(days=30)
        
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
                    'overtime_summary': report_data['overtime_summary'],
                    'employee_overtime_data': report_data['employee_overtime_data'],
                    'department_summaries': report_data.get('department_summaries', {}),
                    'period_overview': report_data['period_overview'],
                    'overtime_trends': report_data.get('overtime_trends', {}),
                    'cost_analysis': report_data.get('cost_analysis', {}),
                    'shift_analysis': report_data.get('shift_analysis', {}),
                    'config_applied': report_data.get('config_applied', {}),
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, _("Overtime report generated successfully for {} to {}.").format(
                    form.cleaned_data['start_date'].strftime('%Y-%m-%d'),
                    form.cleaned_data['end_date'].strftime('%Y-%m-%d')
                ))
                
            except Exception as e:
                logger.error(f"Error generating overtime report: {str(e)}", exc_info=True)
                messages.error(request, _("Failed to generate report: {}").format(str(e)))
        else:
            # Log form errors for debugging
            logger.error(f"Form validation errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        try:
            return {
                'form': form,
                'employees': Employee.objects.filter(is_active=True).select_related('department', 'designation').order_by('employee_id'),
                'departments': Department.objects.all().order_by('name'),
                'designations': Designation.objects.all().order_by('name'),
                'shifts': Shift.objects.all().order_by('name'),
                'page_title': _("Overtime Report"),
                'report_generated': False,
            }
        except Exception as e:
            logger.error(f"Error getting context data: {str(e)}", exc_info=True)
            return {
                'form': form,
                'employees': [],
                'departments': [],
                'designations': [],
                'shifts': [],
                'page_title': _("Overtime Report"),
                'report_generated': False,
            }
    
    def _generate_overtime_report(self, form_data):
        """Generate comprehensive overtime report."""
        try:
            start_date = form_data['start_date']
            end_date = form_data['end_date']
            
            # Validate date range
            if start_date > end_date:
                raise ValueError(_("Start date must be before end date."))
            
            # Get employees based on filter
            employees = self._get_filtered_employees(form_data)
            if not employees.exists():
                raise ValueError(_("No employees found matching the filter criteria."))
            
            # Get holidays for the period
            try:
                holidays = Holiday.objects.filter(date__gte=start_date, date__lte=end_date)
                holiday_dates = {h.date: h.name for h in holidays}
            except Exception as e:
                logger.warning(f"Error fetching holidays: {str(e)}")
                holiday_dates = {}
            
            # Get weekend dates
            weekend_days = form_data.get('weekend_days', [])
            if isinstance(weekend_days, list) and weekend_days:
                try:
                    weekend_days = [int(day) for day in weekend_days]
                except (ValueError, TypeError):
                    logger.warning("Invalid weekend days format, using default [4, 5]")
                    weekend_days = [4, 5]  # Friday and Saturday
            else:
                weekend_days = [4, 5]  # Default to Friday and Saturday
            
            weekend_dates = []
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() in weekend_days:
                    weekend_dates.append(current_date)
                current_date += timedelta(days=1)
            
            # Initialize enhanced processor
            try:
                processor = UnifiedAttendanceProcessor(form_data)
            except Exception as e:
                logger.error(f"Error initializing processor: {str(e)}")
                raise ValueError(_("Error initializing attendance processor: {}").format(str(e)))
            
            # Process each employee's overtime
            employee_overtime_data = []
            department_summaries = {}
            overall_summary = {
                'total_employees': len(employees),
                'total_overtime_hours': 0.0,
                'total_regular_overtime': 0.0,
                'total_holiday_overtime': 0.0,
                'total_weekend_overtime': 0.0,
                'total_overtime_days': 0,
                'average_overtime_per_employee': 0.0,
                'employees_with_overtime': 0,
                'highest_overtime_employee': None,
                'highest_overtime_hours': 0.0,
                'total_estimated_cost': 0.0,
            }
            
            # Enhanced shift analysis tracking
            shift_analysis = {
                'roster_day_usage': 0,
                'roster_assignment_usage': 0,
                'default_shift_usage': 0,
                'dynamic_detection_usage': 0,
                'no_shift_days': 0,
                'multiple_shift_matches': 0,
            }
            
            for employee in employees:
                try:
                    # Get ZK logs for this employee
                    employee_logs = ZKAttendanceLog.objects.filter(
                        user_id=employee.employee_id,
                        timestamp__date__gte=start_date,
                        timestamp__date__lte=end_date
                    ).order_by('timestamp')
                    
                    # Get roster data
                    roster_data = self._get_roster_data(employee, start_date, end_date)
                    
                    # Get leave applications
                    try:
                        leave_applications = LeaveApplication.objects.filter(
                            employee=employee,
                            status='APP',
                            start_date__lte=end_date,
                            end_date__gte=start_date
                        )
                    except Exception as e:
                        logger.warning(f"Error fetching leave applications for {employee.employee_id}: {str(e)}")
                        leave_applications = LeaveApplication.objects.none()
                    
                    # Process attendance with overtime focus
                    try:
                        attendance_result = processor.process_employee_attendance(
                            employee, start_date, end_date, employee_logs,
                            holidays, leave_applications, roster_data
                        )
                    except Exception as e:
                        logger.error(f"Error processing attendance for {employee.employee_id}: {str(e)}")
                        continue
                    
                    # Extract overtime data
                    overtime_data = self._extract_overtime_data(
                        employee, attendance_result, start_date, end_date, form_data
                    )
                    
                    # Apply minimum overtime filter
                    min_overtime = form_data.get('minimum_overtime_hours', 0.0)
                    if overtime_data['total_overtime_hours'] >= min_overtime:
                        employee_overtime_data.append(overtime_data)
                        
                        # Update overall summary
                        self._update_overtime_summary(overall_summary, overtime_data)
                        
                        # Update shift analysis
                        if 'shift_analysis' in attendance_result:
                            result_analysis = attendance_result['shift_analysis']
                            for key in shift_analysis:
                                shift_analysis[key] += result_analysis.get(key, 0)
                        
                        # Group by department if requested
                        if form_data.get('group_by_department', False):
                            dept_name = employee.department.name if employee.department else 'No Department'
                            if dept_name not in department_summaries:
                                department_summaries[dept_name] = {
                                    'employees': [],
                                    'total_employees': 0,
                                    'total_overtime_hours': 0.0,
                                    'total_regular_overtime': 0.0,
                                    'total_holiday_overtime': 0.0,
                                    'total_weekend_overtime': 0.0,
                                    'average_overtime_per_employee': 0.0,
                                }
                            
                            department_summaries[dept_name]['employees'].append(overtime_data)
                            department_summaries[dept_name]['total_employees'] += 1
                            department_summaries[dept_name]['total_overtime_hours'] += overtime_data['total_overtime_hours']
                            department_summaries[dept_name]['total_regular_overtime'] += overtime_data['regular_overtime_hours']
                            department_summaries[dept_name]['total_holiday_overtime'] += overtime_data['holiday_overtime_hours']
                            department_summaries[dept_name]['total_weekend_overtime'] += overtime_data['weekend_overtime_hours']
                
                except Exception as e:
                    logger.error(f"Error processing employee {employee.employee_id}: {str(e)}", exc_info=True)
                    continue
            
            # Calculate department averages
            for dept_name, dept_data in department_summaries.items():
                if dept_data['total_employees'] > 0:
                    dept_data['average_overtime_per_employee'] = round(
                        dept_data['total_overtime_hours'] / dept_data['total_employees'], 2
                    )
            
            # Calculate overall averages
            if len(employee_overtime_data) > 0:
                overall_summary['average_overtime_per_employee'] = round(
                    overall_summary['total_overtime_hours'] / len(employee_overtime_data), 2
                )
                overall_summary['employees_with_overtime'] = len(employee_overtime_data)
            
            # Generate overtime trends if requested
            overtime_trends = {}
            if form_data.get('show_overtime_trends', True):
                try:
                    overtime_trends = self._generate_overtime_trends(
                        employee_overtime_data, start_date, end_date, weekend_dates, holiday_dates
                    )
                except Exception as e:
                    logger.warning(f"Error generating overtime trends: {str(e)}")
                    overtime_trends = {}
            
            # Generate cost analysis if requested
            cost_analysis = {}
            if form_data.get('show_cost_analysis', False):
                try:
                    cost_analysis = self._generate_cost_analysis(
                        employee_overtime_data, form_data.get('overtime_rate_multiplier', 1.5)
                    )
                except Exception as e:
                    logger.warning(f"Error generating cost analysis: {str(e)}")
                    cost_analysis = {}
            
            # Prepare period overview
            period_overview = {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': (end_date - start_date).days + 1,
                'working_days': (end_date - start_date).days + 1 - len(holiday_dates) - len(weekend_dates),
                'weekend_days': len(weekend_dates),
                'holiday_days': len(holiday_dates),
                'period_description': f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}",
            }
            
            return {
                'overtime_summary': overall_summary,
                'employee_overtime_data': employee_overtime_data,
                'department_summaries': department_summaries,
                'period_overview': period_overview,
                'overtime_trends': overtime_trends,
                'cost_analysis': cost_analysis,
                'shift_analysis': shift_analysis,
                'config_applied': processor.get_config_summary() if hasattr(processor, 'get_config_summary') else {},
                'holiday_info': {
                    'holidays': holiday_dates,
                    'total_holidays': len(holiday_dates),
                },
                'weekend_info': {
                    'weekend_dates': weekend_dates,
                    'total_weekends': len(weekend_dates),
                },
            }
            
        except Exception as e:
            logger.error(f"Error in _generate_overtime_report: {str(e)}", exc_info=True)
            raise
    
    def _extract_overtime_data(self, employee, attendance_result, start_date, end_date, form_data):
        """Extract overtime-specific data from attendance result."""
        try:
            daily_records = attendance_result.get('daily_records', [])
            summary_stats = attendance_result.get('summary_stats', {})
            
            # Filter overtime days based on form settings
            overtime_days = []
            overtime_type_filter = form_data.get('overtime_type_filter', 'all')
            include_zero_overtime = form_data.get('include_zero_overtime', False)
            
            for record in daily_records:
                overtime_hours = record.get('overtime_hours', 0.0)
                
                # Apply zero overtime filter
                if not include_zero_overtime and overtime_hours == 0:
                    continue
                
                # Apply overtime type filter
                if overtime_type_filter != 'all':
                    if overtime_type_filter == 'regular' and (record.get('holiday_overtime', False) or record.get('weekend_overtime', False)):
                        continue
                    elif overtime_type_filter == 'holiday' and not record.get('holiday_overtime', False):
                        continue
                    elif overtime_type_filter == 'weekend' and not record.get('weekend_overtime', False):
                        continue
                
                overtime_days.append({
                    'date': record['date'],
                    'day_name': record['day_name'],
                    'overtime_hours': overtime_hours,
                    'overtime_type': 'Holiday' if record.get('holiday_overtime', False) else 
                                   'Weekend' if record.get('weekend_overtime', False) else 'Regular',
                    'shift_name': record.get('shift_name', 'No Shift'),
                    'working_hours': record.get('working_hours', 0.0),
                    'in_time': record.get('in_time'),
                    'out_time': record.get('out_time'),
                    'break_time_minutes': record.get('break_time_minutes', 0),
                    'is_holiday': record.get('is_holiday', False),
                    'holiday_name': record.get('holiday_name', ''),
                })
            
            # Calculate overtime statistics
            total_overtime_hours = sum(day['overtime_hours'] for day in overtime_days)
            regular_overtime = sum(day['overtime_hours'] for day in overtime_days if day['overtime_type'] == 'Regular')
            holiday_overtime = sum(day['overtime_hours'] for day in overtime_days if day['overtime_type'] == 'Holiday')
            weekend_overtime = sum(day['overtime_hours'] for day in overtime_days if day['overtime_type'] == 'Weekend')
            
            return {
                'employee': employee,
                'employee_id': employee.employee_id,
                'employee_name': employee.get_full_name(),
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'total_overtime_hours': round(total_overtime_hours, 2),
                'regular_overtime_hours': round(regular_overtime, 2),
                'holiday_overtime_hours': round(holiday_overtime, 2),
                'weekend_overtime_hours': round(weekend_overtime, 2),
                'overtime_days_count': len([d for d in overtime_days if d['overtime_hours'] > 0]),
                'total_working_hours': round(summary_stats.get('total_working_hours', 0.0), 2),
                'average_daily_overtime': round(total_overtime_hours / len(daily_records) if daily_records else 0, 2),
                'max_daily_overtime': round(max([d['overtime_hours'] for d in overtime_days], default=0), 2),
                'overtime_percentage': round((total_overtime_hours / summary_stats.get('total_working_hours', 1)) * 100, 2) if summary_stats.get('total_working_hours', 0) > 0 else 0,
                'daily_breakdown': overtime_days if form_data.get('show_daily_breakdown', True) else [],
                'summary_stats': summary_stats,
            }
            
        except Exception as e:
            logger.error(f"Error extracting overtime data for {employee.employee_id}: {str(e)}", exc_info=True)
            return {
                'employee': employee,
                'employee_id': employee.employee_id,
                'employee_name': employee.get_full_name(),
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'total_overtime_hours': 0.0,
                'regular_overtime_hours': 0.0,
                'holiday_overtime_hours': 0.0,
                'weekend_overtime_hours': 0.0,
                'overtime_days_count': 0,
                'total_working_hours': 0.0,
                'average_daily_overtime': 0.0,
                'max_daily_overtime': 0.0,
                'overtime_percentage': 0.0,
                'daily_breakdown': [],
                'summary_stats': {},
            }
    
    def _update_overtime_summary(self, overall_summary, overtime_data):
        """Update overall overtime summary with employee data."""
        try:
            overall_summary['total_overtime_hours'] += overtime_data['total_overtime_hours']
            overall_summary['total_regular_overtime'] += overtime_data['regular_overtime_hours']
            overall_summary['total_holiday_overtime'] += overtime_data['holiday_overtime_hours']
            overall_summary['total_weekend_overtime'] += overtime_data['weekend_overtime_hours']
            overall_summary['total_overtime_days'] += overtime_data['overtime_days_count']
            
            # Track highest overtime employee
            if overtime_data['total_overtime_hours'] > overall_summary['highest_overtime_hours']:
                overall_summary['highest_overtime_hours'] = overtime_data['total_overtime_hours']
                overall_summary['highest_overtime_employee'] = overtime_data['employee_name']
                
        except Exception as e:
            logger.warning(f"Error updating overtime summary: {str(e)}")
    
    def _generate_overtime_trends(self, employee_overtime_data, start_date, end_date, weekend_dates, holiday_dates):
        """Generate overtime trend analysis."""
        try:
            trends = {
                'weekly_patterns': {},
                'department_comparison': {},
                'overtime_distribution': {},
                'daily_trends': [],
            }
            
            # Weekly patterns (by day of week)
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for i, day_name in enumerate(day_names):
                daily_overtime = []
                for emp_data in employee_overtime_data:
                    for day in emp_data.get('daily_breakdown', []):
                        if day['date'].weekday() == i:
                            daily_overtime.append(day['overtime_hours'])
                
                trends['weekly_patterns'][day_name] = {
                    'total_overtime_hours': round(sum(daily_overtime), 2),
                    'average_overtime_hours': round(sum(daily_overtime) / len(daily_overtime) if daily_overtime else 0, 2),
                    'overtime_instances': len([ot for ot in daily_overtime if ot > 0]),
                    'max_overtime': round(max(daily_overtime, default=0), 2),
                }
            
            # Department comparison
            dept_stats = {}
            for emp_data in employee_overtime_data:
                dept = emp_data.get('department', 'Unknown')
                if dept not in dept_stats:
                    dept_stats[dept] = {
                        'employees': 0,
                        'total_overtime_hours': 0.0,
                        'total_regular_overtime': 0.0,
                        'total_holiday_overtime': 0.0,
                        'total_weekend_overtime': 0.0,
                    }
                
                dept_stats[dept]['employees'] += 1
                dept_stats[dept]['total_overtime_hours'] += emp_data['total_overtime_hours']
                dept_stats[dept]['total_regular_overtime'] += emp_data['regular_overtime_hours']
                dept_stats[dept]['total_holiday_overtime'] += emp_data['holiday_overtime_hours']
                dept_stats[dept]['total_weekend_overtime'] += emp_data['weekend_overtime_hours']
            
            # Calculate department averages
            for dept, stats in dept_stats.items():
                if stats['employees'] > 0:
                    trends['department_comparison'][dept] = {
                        'employees': stats['employees'],
                        'average_overtime_hours': round(stats['total_overtime_hours'] / stats['employees'], 2),
                        'average_regular_overtime': round(stats['total_regular_overtime'] / stats['employees'], 2),
                        'average_holiday_overtime': round(stats['total_holiday_overtime'] / stats['employees'], 2),
                        'average_weekend_overtime': round(stats['total_weekend_overtime'] / stats['employees'], 2),
                    }
            
            # Overtime distribution
            overtime_ranges = {
                '0-10h': 0, '10-20h': 0, '20-30h': 0, '30-40h': 0, '40h+': 0
            }
            
            for emp_data in employee_overtime_data:
                total_ot = emp_data['total_overtime_hours']
                if total_ot <= 10:
                    overtime_ranges['0-10h'] += 1
                elif total_ot <= 20:
                    overtime_ranges['10-20h'] += 1
                elif total_ot <= 30:
                    overtime_ranges['20-30h'] += 1
                elif total_ot <= 40:
                    overtime_ranges['30-40h'] += 1
                else:
                    overtime_ranges['40h+'] += 1
            
            trends['overtime_distribution'] = overtime_ranges
            
            return trends
            
        except Exception as e:
            logger.error(f"Error generating overtime trends: {str(e)}", exc_info=True)
            return {
                'weekly_patterns': {},
                'department_comparison': {},
                'overtime_distribution': {},
                'daily_trends': [],
            }
    
    def _generate_cost_analysis(self, employee_overtime_data, overtime_rate_multiplier):
        """Generate overtime cost analysis."""
        try:
            cost_analysis = {
                'total_estimated_cost': 0.0,
                'regular_overtime_cost': 0.0,
                'holiday_overtime_cost': 0.0,
                'weekend_overtime_cost': 0.0,
                'employee_costs': [],
                'department_costs': {},
            }
            
            for emp_data in employee_overtime_data:
                employee = emp_data['employee']
                
                # Get hourly rate (you may need to adjust this based on your Employee model)
                hourly_rate = getattr(employee, 'hourly_rate', 0.0)
                if hourly_rate == 0.0:
                    # Estimate from monthly salary if available
                    monthly_salary = getattr(employee, 'salary', 0.0)
                    if monthly_salary > 0:
                        # Assume 22 working days, 8 hours per day
                        hourly_rate = monthly_salary / (22 * 8)
                
                if hourly_rate > 0:
                    overtime_rate = hourly_rate * overtime_rate_multiplier
                    
                    regular_cost = emp_data['regular_overtime_hours'] * overtime_rate
                    holiday_cost = emp_data['holiday_overtime_hours'] * overtime_rate * 2  # Double rate for holidays
                    weekend_cost = emp_data['weekend_overtime_hours'] * overtime_rate * 1.5  # 1.5x rate for weekends
                    
                    total_cost = regular_cost + holiday_cost + weekend_cost
                    
                    cost_analysis['total_estimated_cost'] += total_cost
                    cost_analysis['regular_overtime_cost'] += regular_cost
                    cost_analysis['holiday_overtime_cost'] += holiday_cost
                    cost_analysis['weekend_overtime_cost'] += weekend_cost
                    
                    cost_analysis['employee_costs'].append({
                        'employee_id': emp_data['employee_id'],
                        'employee_name': emp_data['employee_name'],
                        'department': emp_data['department'],
                        'hourly_rate': hourly_rate,
                        'overtime_rate': overtime_rate,
                        'total_cost': round(total_cost, 2),
                        'regular_cost': round(regular_cost, 2),
                        'holiday_cost': round(holiday_cost, 2),
                        'weekend_cost': round(weekend_cost, 2),
                    })
            
            return cost_analysis
            
        except Exception as e:
            logger.error(f"Error generating cost analysis: {str(e)}", exc_info=True)
            return {
                'total_estimated_cost': 0.0,
                'regular_overtime_cost': 0.0,
                'holiday_overtime_cost': 0.0,
                'weekend_overtime_cost': 0.0,
                'employee_costs': [],
                'department_costs': {},
            }
    
    def _get_filtered_employees(self, form_data):
        """Get employees based on filter criteria."""
        try:
            employee_filter = form_data.get('employee_filter', 'all')
            
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
                    if employee_ids:
                        return queryset.filter(employee_id__in=employee_ids)
            
            return queryset
            
        except Exception as e:
            logger.error(f"Error filtering employees: {str(e)}", exc_info=True)
            return Employee.objects.none()
    
    def _get_roster_data(self, employee, start_date, end_date):
        """Get roster data for employee."""
        roster_data = {
            'assignments': {},
            'days': {}
        }
        
        try:
            # Get roster assignments
            try:
                roster_assignments = RosterAssignment.objects.filter(
                    employee=employee,
                    roster__start_date__lte=end_date,
                    roster__end_date__gte=start_date
                ).select_related('roster', 'shift')
                
                # Organize roster assignments
                for assignment in roster_assignments:
                    current_date = max(assignment.roster.start_date, start_date)
                    end_assignment_date = min(assignment.roster.end_date, end_date)
                    
                    while current_date <= end_assignment_date:
                        roster_data['assignments'][current_date] = assignment
                        current_date += timedelta(days=1)
                        
            except Exception as e:
                logger.warning(f"Error fetching roster assignments: {str(e)}")
            
            # Get roster days
            try:
                roster_days = RosterDay.objects.filter(
                    roster_assignment__employee=employee,
                    date__gte=start_date,
                    date__lte=end_date
                ).select_related('shift', 'roster_assignment__roster')
                
                # Organize roster days
                for roster_day in roster_days:
                    roster_data['days'][roster_day.date] = roster_day
                    
            except Exception as e:
                logger.warning(f"Error fetching roster days: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error getting roster data: {str(e)}", exc_info=True)
        
        return roster_data
    
    def _handle_export(self, request):
        """Handle CSV export of overtime report."""
        try:
            form = OvertimeReportForm(request.POST)
            if not form.is_valid():
                messages.error(request, _("Please fix form errors before exporting."))
                return self.post(request)
            
            report_data = self._generate_overtime_report(form.cleaned_data)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="overtime_report_{form.cleaned_data["start_date"]}_{form.cleaned_data["end_date"]}.csv"'
            
            writer = csv.writer(response)
            
            # Write header information
            writer.writerow(['Overtime Report'])
            writer.writerow(['Period', f"{form.cleaned_data['start_date']} to {form.cleaned_data['end_date']}"])
            writer.writerow(['Generated', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])  # Empty row
            
            # Write summary
            summary = report_data['overtime_summary']
            writer.writerow(['Summary Statistics'])
            writer.writerow(['Total Employees', summary['total_employees']])
            writer.writerow(['Employees with Overtime', summary['employees_with_overtime']])
            writer.writerow(['Total Overtime Hours', summary['total_overtime_hours']])
            writer.writerow(['Regular Overtime Hours', summary['total_regular_overtime']])
            writer.writerow(['Holiday Overtime Hours', summary['total_holiday_overtime']])
            writer.writerow(['Weekend Overtime Hours', summary['total_weekend_overtime']])
            writer.writerow(['Average Overtime per Employee', summary['average_overtime_per_employee']])
            writer.writerow([])  # Empty row
            
            # Write employee data header
            writer.writerow([
                'Employee ID', 'Employee Name', 'Department', 'Designation',
                'Total Overtime Hours', 'Regular OT Hours', 'Holiday OT Hours', 'Weekend OT Hours',
                'Overtime Days', 'Total Working Hours', 'Average Daily OT', 'Max Daily OT', 'OT Percentage'
            ])
            
            # Write employee data
            for emp_data in report_data['employee_overtime_data']:
                try:
                    writer.writerow([
                        emp_data['employee_id'],
                        emp_data['employee_name'],
                        emp_data['department'],
                        emp_data['designation'],
                        emp_data['total_overtime_hours'],
                        emp_data['regular_overtime_hours'],
                        emp_data['holiday_overtime_hours'],
                        emp_data['weekend_overtime_hours'],
                        emp_data['overtime_days_count'],
                        emp_data['total_working_hours'],
                        emp_data['average_daily_overtime'],
                        emp_data['max_daily_overtime'],
                        emp_data['overtime_percentage'],
                    ])
                except Exception as e:
                    logger.warning(f"Error writing CSV row for employee: {str(e)}")
                    continue
            
            # Write daily breakdown if requested
            if form.cleaned_data.get('show_daily_breakdown', True):
                writer.writerow([])  # Empty row
                writer.writerow(['Daily Overtime Breakdown'])
                writer.writerow(['Employee ID', 'Date', 'Day', 'Overtime Hours', 'Overtime Type', 'Shift', 'Working Hours'])
                
                for emp_data in report_data['employee_overtime_data']:
                    for day in emp_data.get('daily_breakdown', []):
                        if day['overtime_hours'] > 0:  # Only include days with overtime
                            writer.writerow([
                                emp_data['employee_id'],
                                day['date'].strftime('%Y-%m-%d'),
                                day['day_name'],
                                day['overtime_hours'],
                                day['overtime_type'],
                                day['shift_name'],
                                day['working_hours'],
                            ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting overtime report: {str(e)}", exc_info=True)
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)
