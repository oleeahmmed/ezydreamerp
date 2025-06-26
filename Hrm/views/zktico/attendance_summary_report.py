import logging
from datetime import timedelta, datetime, time
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.db.models import Q, Min, Max, Prefetch, Count, Sum, Avg
from django.http import JsonResponse
from django.db import transaction
import json
from collections import defaultdict, OrderedDict

from Hrm.models import *
from .unified_attendance_processor import UnifiedAttendanceProcessor

logger = logging.getLogger(__name__)

class AttendanceSummaryReportForm(forms.Form):
    """Enhanced form with advanced modal options matching detailed employee report."""
    
    # Date Range
    start_date = forms.DateField(
        label=_("Start Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the start date for attendance summary period.")
    )
    end_date = forms.DateField(
        label=_("End Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the end date for attendance summary period.")
    )
    
    # Weekend Configuration (Multiple Days)
    WEEKDAY_CHOICES = [
        (0, _('Monday')), (1, _('Tuesday')), (2, _('Wednesday')), 
        (3, _('Thursday')), (4, _('Friday')), (5, _('Saturday')), (6, _('Sunday'))
    ]
    
    weekend_days = forms.MultipleChoiceField(
        label=_("Weekend Days"),
        choices=WEEKDAY_CHOICES,
        initial=[4],  # Friday by default
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text=_("Select weekend days. Multiple days can be selected.")
    )
    
    # Employee Filtering Options
    employee_filter = forms.ChoiceField(
        label=_("Employee Filter Type"),
        choices=[
            ('all', _('All Active Employees')),
            ('department', _('Filter by Department')),
            ('designation', _('Filter by Designation')),
            ('specific', _('Specific Employee IDs')),
        ],
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Choose how you want to filter employees for the summary report.")
    )
    
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
        help_text=_("Select departments for filtering.")
    )
    
    designations = forms.ModelMultipleChoiceField(
        queryset=Designation.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
        help_text=_("Select designations for filtering.")
    )
    
    employee_ids = forms.CharField(
        label=_("Specific Employee IDs"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'EMP001, EMP002, EMP003'
        }),
        help_text=_("Enter specific employee IDs separated by commas.")
    )
    
    # Modal Configuration Options (Same as Detailed Report)
    grace_minutes = forms.IntegerField(
        label=_("Grace Time (Minutes)"),
        initial=15,
        min_value=0,
        max_value=60,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Grace time for late arrival. Uses employee setting if not specified.")
    )
    
    early_out_threshold_minutes = forms.IntegerField(
        label=_("Early Out Threshold (Minutes)"),
        initial=30,
        min_value=0,
        max_value=120,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Minimum minutes before shift end to count as early out.")
    )
    
    overtime_start_after_minutes = forms.IntegerField(
        label=_("Overtime Start After (Minutes)"),
        initial=15,
        min_value=0,
        max_value=60,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Minutes after expected work hours to start counting overtime.")
    )
    
    minimum_overtime_minutes = forms.IntegerField(
        label=_("Minimum Overtime Minutes"),
        initial=60,
        min_value=15,
        max_value=240,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Minimum minutes to count as overtime (e.g., 60 = 1 hour minimum).")
    )
    
    late_to_absent_days = forms.IntegerField(
        label=_("Late to Absent Conversion"),
        initial=3,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Number of late days that convert to 1 absent day.")
    )
    
    # Holiday and Weekend Rules
    holiday_before_after_absent = forms.BooleanField(
        label=_("Holiday Between Absences Rule"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Mark holiday as absent if employee is absent before and after holiday.")
    )
    
    weekend_before_after_absent = forms.BooleanField(
        label=_("Weekend Between Absences Rule"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Apply same rule for weekends as holidays.")
    )
    
    require_holiday_presence = forms.BooleanField(
        label=_("Require Presence Before/After Holiday"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Employee must be present before or after holiday to get holiday benefit.")
    )
    
    # Analysis Options
    include_holiday_analysis = forms.BooleanField(
        label=_("Include Holiday Analysis"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Analyze attendance patterns around holidays and mark consecutive absences.")
    )
    
    holiday_buffer_days = forms.IntegerField(
        label=_("Holiday Buffer Days"),
        initial=1,
        min_value=0,
        max_value=5,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Days before/after holidays to check for absence patterns.")
    )
    
    include_leave_analysis = forms.BooleanField(
        label=_("Include Leave Analysis"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include approved leave applications in the summary.")
    )
    
    # Summary Options
    show_overtime_details = forms.BooleanField(
        label=_("Show Overtime Details"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include detailed overtime calculations in summary.")
    )
    
    show_leave_balance = forms.BooleanField(
        label=_("Show Leave Balance"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include current leave balance information.")
    )
    
    group_by_department = forms.BooleanField(
        label=_("Group by Department"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Group summary results by department.")
    )
    
    show_roster_details = forms.BooleanField(
        label=_("Show Roster Details"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Show detailed roster assignment information.")
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("Start date cannot be after end date.")
            
            # Check date range is reasonable
            if (end_date - start_date).days > 365:
                raise forms.ValidationError("Date range cannot exceed 365 days for performance reasons.")
        
        return cleaned_data

class AttendanceSummaryReportView(LoginRequiredMixin, View):
    """Unified view using shared attendance processing logic."""
    template_name = 'report/hrm/attendance_summary_report.html'
    
    def get(self, request, *args, **kwargs):
        form = AttendanceSummaryReportForm()
        
        # Set default dates
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        form.fields['start_date'].initial = start_of_month
        form.fields['end_date'].initial = today
        
        context_data = self._get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        form = AttendanceSummaryReportForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                summary_data = self._generate_unified_attendance_summary_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'summary_data': summary_data,
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, "Unified attendance summary report generated successfully for {} employees with consistent logic.".format(
                    len(summary_data.get('employee_summaries', []))))
                
            except Exception as e:
                logger.error(f"Error generating unified attendance summary report: {str(e)}")
                messages.error(request, "Failed to generate summary report: {}".format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'report_generated': False,
            'page_title': "Unified Attendance Summary Report with Consistent Logic",
        }
    
    def _generate_unified_attendance_summary_report(self, form_data):
        """Generate comprehensive attendance summary report using unified processor."""
        start_date = form_data['start_date']
        end_date = form_data['end_date']
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        
        # Get holidays in the period
        holidays = self._get_holidays_in_period(start_date, end_date)
        
        # Get leave applications
        leave_applications = self._get_leave_applications(employees, start_date, end_date) if form_data.get('include_leave_analysis', True) else {}
        
        # Get ZK attendance logs for detailed analysis
        zk_logs = self._get_zk_attendance_logs(employees, start_date, end_date)
        
        # Get roster data
        roster_data = self._get_roster_data(employees, start_date, end_date)
        
        # Initialize unified processor
        processor = UnifiedAttendanceProcessor(form_data)
        
        # Generate employee summaries using unified processing
        employee_summaries = []
        department_summaries = defaultdict(lambda: {
            'total_employees': 0,
            'total_present_days': 0,
            'total_absent_days': 0,
            'total_leave_days': 0,
            'total_holiday_days': 0,
            'total_overtime_hours': 0,
            'total_late_days': 0,
            'total_early_out_days': 0,
            'converted_absents': 0,
            'employees': []
        })
        
        for employee in employees:
            # Process employee attendance using unified logic
            result = processor.process_employee_attendance(
                employee, start_date, end_date, 
                zk_logs.filter(user_id=employee.employee_id),
                holidays,
                leave_applications.get(employee.id, []),
                roster_data.get(employee.id, {'assignments': {}, 'days': {}})
            )
            
            # Convert to summary format
            employee_summary = self._convert_to_summary_format(employee, result['summary_stats'], form_data)
            employee_summaries.append(employee_summary)
            
            # Add to department summary
            dept_name = employee.department.name if employee.department else 'No Department'
            dept_summary = department_summaries[dept_name]
            dept_summary['total_employees'] += 1
            dept_summary['total_present_days'] += employee_summary['total_present_days']
            dept_summary['total_absent_days'] += employee_summary['total_absent_days']
            dept_summary['total_leave_days'] += employee_summary['total_leave_days']
            dept_summary['total_holiday_days'] += employee_summary['total_holiday_days']
            dept_summary['total_overtime_hours'] += employee_summary['total_overtime_hours']
            dept_summary['total_late_days'] += employee_summary['total_late_days']
            dept_summary['total_early_out_days'] += employee_summary['total_early_out_days']
            dept_summary['converted_absents'] += employee_summary['converted_absents']
            dept_summary['employees'].append(employee_summary)
        
        # Calculate overall statistics
        overall_stats = self._calculate_unified_overall_statistics(employee_summaries, start_date, end_date)
        
        return {
            'employee_summaries': employee_summaries,
            'department_summaries': dict(department_summaries),
            'overall_stats': overall_stats,
            'period_info': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': (end_date - start_date).days + 1,
                'working_days': self._calculate_working_days(start_date, end_date, [int(day) for day in form_data['weekend_days']], holidays),
                'weekend_days': [int(day) for day in form_data['weekend_days']],
                'holidays': holidays,
            },
            'applied_config': form_data,
        }
    
    def _convert_to_summary_format(self, employee, summary_stats, form_data):
        """Convert unified summary stats to expected summary format."""
        
        # Get leave balance information
        leave_balances = []
        if form_data.get('show_leave_balance', True):
            current_year = timezone.now().year
            try:
                leave_balances = employee.leave_balances.filter(year=current_year)
            except:
                leave_balances = []
        
        return {
            'employee': employee,
            'employee_id': employee.employee_id,
            'employee_name': employee.get_full_name(),
            'department': employee.department.name if employee.department else 'No Department',
            'designation': employee.designation.name if employee.designation else 'No Designation',
            'expected_work_hours': employee.expected_work_hours,
            'overtime_grace_minutes': employee.overtime_grace_minutes,
            
            # Attendance Summary (directly from unified processor)
            'total_days': summary_stats['total_days'],
            'working_days': summary_stats['total_days'] - summary_stats['holiday_days'] - summary_stats['leave_days'],
            'total_present_days': summary_stats['present_days'],
            'total_absent_days': summary_stats['absent_days'],
            'total_late_days': summary_stats['late_days'],
            'total_half_days': summary_stats['half_days'],
            'total_leave_days': summary_stats['leave_days'],
            'total_holiday_days': summary_stats['holiday_days'],
            'attendance_percentage': summary_stats['attendance_percentage'],
            
            # Work Hours Summary
            'total_work_hours': summary_stats['total_working_hours'],
            'total_overtime_hours': summary_stats['total_overtime_hours'],
            'average_daily_hours': summary_stats['average_daily_hours'],
            'total_early_out_days': summary_stats['early_out_days'],
            
            # Advanced Metrics
            'converted_absents': summary_stats['converted_absents'],
            'original_late_days': summary_stats['original_late_days'],
            'punctuality_percentage': summary_stats['punctuality_percentage'],
            
            # Leave Information
            'leave_balances': leave_balances,
            'approved_leaves': 0,  # This would need to be calculated separately if needed
            
            # Status Indicators
            'has_attendance_issues': summary_stats['absent_days'] > (summary_stats['total_days'] * 0.1),
            'has_holiday_pattern': False,  # This would need holiday analysis
            'has_excessive_overtime': summary_stats['total_overtime_hours'] > (summary_stats['total_days'] * 2),
        }
    
    # Helper methods (same as before but using unified logic)
    def _get_filtered_employees(self, form_data):
        """Get employees based on filter criteria."""
        employee_filter = form_data['employee_filter']
        
        queryset = Employee.objects.filter(is_active=True).select_related(
            'department', 'designation', 'default_shift'
        ).prefetch_related('leave_balances')
        
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
    
    def _get_holidays_in_period(self, start_date, end_date):
        """Get holidays in the specified period."""
        try:
            return Holiday.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date')
        except:
            return []
    
    def _get_leave_applications(self, employees, start_date, end_date):
        """Get leave applications for employees in the period."""
        try:
            leave_apps = LeaveApplication.objects.filter(
                employee__in=employees,
                start_date__lte=end_date,
                end_date__gte=start_date
            ).select_related('employee', 'leave_type')
            
            # Group by employee
            employee_leaves = defaultdict(list)
            for leave_app in leave_apps:
                employee_leaves[leave_app.employee.id].append(leave_app)
            
            return employee_leaves
        except:
            return {}
    
    def _get_zk_attendance_logs(self, employees, start_date, end_date):
        """Get ZK attendance logs for detailed analysis."""
        employee_ids = [emp.employee_id for emp in employees]
        
        try:
            return ZKAttendanceLog.objects.filter(
                user_id__in=employee_ids,
                timestamp__date__gte=start_date,
                timestamp__date__lte=end_date
            ).select_related('device').order_by('user_id', 'timestamp')
        except:
            return ZKAttendanceLog.objects.none()
    
    def _get_roster_data(self, employees, start_date, end_date):
        """Get roster assignments and roster days for employees."""
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
            ).select_related('shift', 'roster_assignment__roster', 'roster_assignment__shift')
            
        except Exception as e:
            logger.warning(f"Could not fetch roster data: {str(e)}")
            roster_assignments = []
            roster_days = []
        
        # Organize data by employee
        for employee in employees:
            roster_data[employee.id] = {
                'assignments': {},
                'days': {} }
            roster_data[employee.id] = {
                'assignments': {},
                'days': {}
            }
        
        # Organize roster assignments by date range
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
    
    def _calculate_working_days(self, start_date, end_date, weekend_days, holidays):
        """Calculate working days excluding weekend days and public holidays."""
        working_days = 0
        holiday_dates = {h.date for h in holidays}
        
        current_date = start_date
        while current_date <= end_date:
            if (current_date.weekday() not in weekend_days and 
                current_date not in holiday_dates):
                working_days += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def _calculate_unified_overall_statistics(self, employee_summaries, start_date, end_date):
        """Calculate unified overall statistics from employee summaries."""
        if not employee_summaries:
            return {}
        
        total_employees = len(employee_summaries)
        total_present_days = sum(emp['total_present_days'] for emp in employee_summaries)
        total_absent_days = sum(emp['total_absent_days'] for emp in employee_summaries)
        total_leave_days = sum(emp['total_leave_days'] for emp in employee_summaries)
        total_overtime_hours = sum(emp['total_overtime_hours'] for emp in employee_summaries)
        total_late_days = sum(emp['total_late_days'] for emp in employee_summaries)
        total_converted_absents = sum(emp['converted_absents'] for emp in employee_summaries)
        total_early_out_days = sum(emp['total_early_out_days'] for emp in employee_summaries)
        
        employees_with_issues = sum(1 for emp in employee_summaries if emp['has_attendance_issues'])
        employees_with_holiday_pattern = sum(1 for emp in employee_summaries if emp['has_holiday_pattern'])
        employees_with_excessive_overtime = sum(1 for emp in employee_summaries if emp['has_excessive_overtime'])
        
        avg_attendance_percentage = sum(emp['attendance_percentage'] for emp in employee_summaries) / total_employees
        avg_punctuality_percentage = sum(emp['punctuality_percentage'] for emp in employee_summaries) / total_employees
        
        return {
            'total_employees': total_employees,
            'total_present_days': total_present_days,
            'total_absent_days': total_absent_days,
            'total_leave_days': total_leave_days,
            'total_overtime_hours': round(total_overtime_hours, 2),
            'total_late_days': total_late_days,
            'total_converted_absents': total_converted_absents,
            'total_early_out_days': total_early_out_days,
            'average_attendance_percentage': round(avg_attendance_percentage, 2),
            'average_punctuality_percentage': round(avg_punctuality_percentage, 2),
            'employees_with_issues': employees_with_issues,
            'employees_with_holiday_pattern': employees_with_holiday_pattern,
            'employees_with_excessive_overtime': employees_with_excessive_overtime,
            'period_days': (end_date - start_date).days + 1,
        }
