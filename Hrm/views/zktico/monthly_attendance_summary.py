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

class MonthlyAttendanceSummaryForm(forms.Form):
    """Form for generating monthly attendance summary report."""
    
    # Month and Year Selection
    year = forms.IntegerField(
        label=_("Year"),
        min_value=2020,
        max_value=2030,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Select the year for the monthly summary.")
    )
    
    month = forms.ChoiceField(
        label=_("Month"),
        choices=[
            (1, _('January')), (2, _('February')), (3, _('March')),
            (4, _('April')), (5, _('May')), (6, _('June')),
            (7, _('July')), (8, _('August')), (9, _('September')),
            (10, _('October')), (11, _('November')), (12, _('December'))
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Select the month for the summary.")
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
    
    # Summary Options
    include_detailed_breakdown = forms.BooleanField(
        label=_("Include Detailed Breakdown"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include day-by-day breakdown for each employee.")
    )
    
    show_overtime_summary = forms.BooleanField(
        label=_("Show Overtime Summary"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include overtime hours summary.")
    )
    
    show_leave_summary = forms.BooleanField(
        label=_("Show Leave Summary"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include leave days summary.")
    )
    
    calculate_attendance_percentage = forms.BooleanField(
        label=_("Calculate Attendance Percentage"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Calculate and show attendance percentage for each employee.")
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
    
    # Late to Absent Conversion
    late_to_absent_days = forms.IntegerField(
        label=_("Late to Absent Conversion (Days)"),
        initial=3,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Convert consecutive late days to absent after this threshold.")
    )
    
    holiday_before_after_absent = forms.BooleanField(
        label=_("Holiday Before/After Absent Rule"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Mark holidays as absent if employee is absent before and after.")
    )
    
    weekend_before_after_absent = forms.BooleanField(
        label=_("Weekend Before/After Absent Rule"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Mark weekends as absent if employee is absent before and after.")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current year and month as default
        now = timezone.now()
        self.fields['year'].initial = now.year
        self.fields['month'].initial = now.month

class MonthlyAttendanceSummaryView(LoginRequiredMixin, View):
    """View for generating monthly attendance summary reports."""
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
                report_data = self._generate_monthly_summary_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'summary_data': report_data['summary_data'],
                    'employee_summaries': report_data['employee_summaries'],
                    'month_info': report_data['month_info'],
                    'overall_statistics': report_data['overall_statistics'],
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, _("Monthly attendance summary generated successfully for {} {}.").format(
                    calendar.month_name[int(form.cleaned_data['month'])], form.cleaned_data['year']))
                
            except Exception as e:
                logger.error(f"Error generating monthly attendance summary: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'page_title': _("Monthly Attendance Summary"),
            'report_generated': False,
        }
    
    def _generate_monthly_summary_report(self, form_data):
        """Generate monthly attendance summary using UnifiedAttendanceProcessor."""
        year = int(form_data['year'])
        month = int(form_data['month'])
        
        # Calculate month date range
        start_date = datetime(year, month, 1).date()
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day).date()
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        
        # Get holidays for the month
        holidays = Holiday.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Get ZK attendance logs for the month
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
        
        employee_summaries = []
        overall_statistics = {
            'total_employees': len(employees),
            'total_working_days': 0,
            'total_present_days': 0,
            'total_absent_days': 0,
            'total_late_days': 0,
            'total_leave_days': 0,
            'total_holiday_days': 0,
            'total_half_days': 0,
            'total_working_hours': 0.0,
            'total_overtime_hours': 0.0,
            'average_attendance_percentage': 0.0,
            'employees_with_perfect_attendance': 0,
            'employees_with_overtime': 0,
            'most_absent_employee': None,
            'most_overtime_employee': None,
        }
        
        attendance_percentages = []
        max_absent_days = 0
        max_overtime_hours = 0.0
        
        for employee in employees:
            employee_logs = zk_logs.filter(user_id=employee.employee_id)
            employee_roster_data = roster_data.get(employee.id, {})
            
            # Get leave applications for this employee and month
            leave_applications = LeaveApplication.objects.filter(
                employee=employee,
                status='APP',
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            # Process attendance for this employee for the entire month
            attendance_result = processor.process_employee_attendance(
                employee, start_date, end_date, employee_logs,
                holidays, leave_applications, employee_roster_data
            )
            
            # Create employee summary
            summary_stats = attendance_result.get('summary_stats', {})
            daily_records = attendance_result.get('daily_records', [])
            
            # Ensure summary_stats has all required fields with defaults
            summary_stats = {
                'total_days': summary_stats.get('total_days', 0),
                'present_days': summary_stats.get('present_days', 0),
                'absent_days': summary_stats.get('absent_days', 0),
                'late_days': summary_stats.get('late_days', 0),
                'leave_days': summary_stats.get('leave_days', 0),
                'holiday_days': summary_stats.get('holiday_days', 0),
                'half_days': summary_stats.get('half_days', 0),
                'total_working_hours': summary_stats.get('total_working_hours', 0.0),
                'total_overtime_hours': summary_stats.get('total_overtime_hours', 0.0),
                'attendance_percentage': summary_stats.get('attendance_percentage', 0.0),
                'punctuality_percentage': summary_stats.get('punctuality_percentage', 0.0),
                'max_consecutive_absences': summary_stats.get('max_consecutive_absences', 0),
                'converted_absents': summary_stats.get('converted_absents', 0),
                'original_late_days': summary_stats.get('original_late_days', 0),
            }
            
            employee_summary = {
                'employee': employee,
                'employee_id': employee.employee_id,
                'employee_name': employee.get_full_name(),
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'summary_stats': summary_stats,
                'daily_breakdown': daily_records if form_data.get('include_detailed_breakdown', False) else [],
                'perfect_attendance': summary_stats['absent_days'] == 0 and summary_stats['late_days'] == 0,
                'has_overtime': summary_stats['total_overtime_hours'] > 0,
                'consecutive_absences': summary_stats['max_consecutive_absences'],
                'converted_absents': summary_stats['converted_absents'],
                'original_late_days': summary_stats['original_late_days'],
            }
            
            employee_summaries.append(employee_summary)
            
            # Update overall statistics
            working_days = summary_stats['total_days'] - summary_stats['holiday_days'] - summary_stats['leave_days']
            overall_statistics['total_working_days'] += working_days
            overall_statistics['total_present_days'] += summary_stats['present_days']
            overall_statistics['total_absent_days'] += summary_stats['absent_days']
            overall_statistics['total_late_days'] += summary_stats['late_days']
            overall_statistics['total_leave_days'] += summary_stats['leave_days']
            overall_statistics['total_holiday_days'] += summary_stats['holiday_days']
            overall_statistics['total_half_days'] += summary_stats['half_days']
            overall_statistics['total_working_hours'] += summary_stats['total_working_hours']
            overall_statistics['total_overtime_hours'] += summary_stats['total_overtime_hours']
            
            if employee_summary['perfect_attendance']:
                overall_statistics['employees_with_perfect_attendance'] += 1
            
            if employee_summary['has_overtime']:
                overall_statistics['employees_with_overtime'] += 1
            
            # Track attendance percentage
            attendance_percentages.append(summary_stats['attendance_percentage'])
            
            # Track most absent employee
            if summary_stats['absent_days'] > max_absent_days:
                max_absent_days = summary_stats['absent_days']
                overall_statistics['most_absent_employee'] = employee_summary
            
            # Track most overtime employee
            if summary_stats['total_overtime_hours'] > max_overtime_hours:
                max_overtime_hours = summary_stats['total_overtime_hours']
                overall_statistics['most_overtime_employee'] = employee_summary
        
        # Calculate average attendance percentage
        if attendance_percentages:
            overall_statistics['average_attendance_percentage'] = round(
                sum(attendance_percentages) / len(attendance_percentages), 2
            )
        
        # Month information
        month_info = {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'start_date': start_date,
            'end_date': end_date,
            'total_days': (end_date - start_date).days + 1,
            'working_days': self._calculate_working_days(start_date, end_date, holidays, form_data.get('weekend_days', [])),
            'holidays': list(holidays.values('date', 'name')),
            'weekend_days': [calendar.day_name[int(day)] for day in form_data.get('weekend_days', [])],
        }
        
        return {
            'summary_data': employee_summaries,
            'employee_summaries': employee_summaries,
            'month_info': month_info,
            'overall_statistics': overall_statistics,
        }
    
    def _calculate_working_days(self, start_date, end_date, holidays, weekend_days):
        """Calculate working days excluding weekends and holidays."""
        total_days = (end_date - start_date).days + 1
        weekend_days = [int(day) for day in weekend_days] if weekend_days else []
        
        working_days = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Check if it's not a weekend
            if current_date.weekday() not in weekend_days:
                # Check if it's not a holiday
                if not holidays.filter(date=current_date).exists():
                    working_days += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def _get_filtered_employees(self, form_data):
        """Get employees based on filter criteria."""
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
        """Handle CSV export of monthly attendance summary."""
        form = MonthlyAttendanceSummaryForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please fix form errors before exporting."))
            return self.post(request)
        
        try:
            report_data = self._generate_monthly_summary_report(form.cleaned_data)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="monthly_attendance_summary_{form.cleaned_data["year"]}_{form.cleaned_data["month"]:02d}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Employee ID', 'Employee Name', 'Department', 'Designation',
                'Total Days', 'Present Days', 'Absent Days', 'Late Days', 'Leave Days',
                'Holiday Days', 'Half Days', 'Working Hours', 'Overtime Hours',
                'Attendance %', 'Punctuality %', 'Max Consecutive Absences',
                'Converted Absents', 'Perfect Attendance'
            ])
            
            for summary in report_data['employee_summaries']:
                stats = summary['summary_stats']
                writer.writerow([
                    summary['employee_id'],
                    summary['employee_name'],
                    summary['department'],
                    summary['designation'],
                    stats['total_days'],
                    stats['present_days'],
                    stats['absent_days'],
                    stats['late_days'],
                    stats['leave_days'],
                    stats['holiday_days'],
                    stats['half_days'],
                    stats['total_working_hours'],
                    stats['total_overtime_hours'],
                    stats['attendance_percentage'],
                    stats['punctuality_percentage'],
                    stats['max_consecutive_absences'],
                    stats['converted_absents'],
                    'Yes' if summary['perfect_attendance'] else 'No',
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting monthly attendance summary: {str(e)}")
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)
