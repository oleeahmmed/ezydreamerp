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

logger = logging.getLogger(__name__)

class AttendanceSummaryReportForm(forms.Form):
    """Enhanced form for generating comprehensive attendance summary report."""
    
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
    
    # Weekly Holiday Selection
    WEEKDAY_CHOICES = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]
    
    weekly_holidays = forms.MultipleChoiceField(
        label=_("Weekly Holidays"),
        choices=WEEKDAY_CHOICES,
        initial=[4],  # Friday by default
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text=_("Select weekly holidays. Multiple days can be selected. Friday is selected by default.")
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
    
    # Holiday and Leave Options
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
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1'
        }),
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
    """Enhanced view to generate comprehensive attendance summary report."""
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
                summary_data = self._generate_attendance_summary_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'summary_data': summary_data,
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, "Attendance summary report generated successfully for {} employees.".format(
                    len(summary_data.get('employee_summaries', []))))
                
            except Exception as e:
                logger.error(f"Error generating attendance summary report: {str(e)}")
                messages.error(request, "Failed to generate summary report: {}".format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'report_generated': False,
            'page_title': "Comprehensive Attendance Summary Report",
        }
    
    def _generate_attendance_summary_report(self, form_data):
        """Generate comprehensive attendance summary report with holiday and leave analysis."""
        start_date = form_data['start_date']
        end_date = form_data['end_date']
        weekly_holidays = [int(day) for day in form_data['weekly_holidays']]
        include_holiday_analysis = form_data['include_holiday_analysis']
        include_leave_analysis = form_data['include_leave_analysis']
        holiday_buffer_days = form_data.get('holiday_buffer_days', 1)
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        
        # Get holidays in the period
        holidays = self._get_holidays_in_period(start_date, end_date)
        
        # Get leave applications
        leave_applications = self._get_leave_applications(employees, start_date, end_date) if include_leave_analysis else {}
        
        # Get attendance data
        attendance_data = self._get_attendance_data(employees, start_date, end_date)
        
        # Get ZK attendance logs for detailed analysis
        zk_logs = self._get_zk_attendance_logs(employees, start_date, end_date)
        
        # Get roster data
        roster_data = self._get_roster_data(employees, start_date, end_date)
        
        # Generate employee summaries
        employee_summaries = []
        department_summaries = defaultdict(lambda: {
            'total_employees': 0,
            'total_present_days': 0,
            'total_absent_days': 0,
            'total_leave_days': 0,
            'total_holiday_days': 0,
            'total_overtime_hours': 0,
            'employees': []
        })
        
        for employee in employees:
            employee_summary = self._generate_employee_summary(
                employee, start_date, end_date, weekly_holidays, holidays,
                attendance_data.get(employee.id, []),
                zk_logs.filter(user_id=employee.employee_id),
                leave_applications.get(employee.id, []),
                roster_data.get(employee.id, {}),
                form_data
            )
            
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
            dept_summary['employees'].append(employee_summary)
        
        # Calculate overall statistics
        overall_stats = self._calculate_overall_statistics(employee_summaries, start_date, end_date)
        
        return {
            'employee_summaries': employee_summaries,
            'department_summaries': dict(department_summaries),
            'overall_stats': overall_stats,
            'period_info': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': (end_date - start_date).days + 1,
                'working_days': self._calculate_working_days(start_date, end_date, weekly_holidays, holidays),
                'weekly_holidays': weekly_holidays,
                'holidays': holidays,
            }
        }
    
    def _generate_employee_summary(self, employee, start_date, end_date, weekly_holidays, 
                                 holidays, attendance_records, zk_logs, leave_applications, roster_data, form_data):
        """Generate comprehensive summary for a single employee."""
        
        total_days = (end_date - start_date).days + 1
        working_days = self._calculate_working_days(start_date, end_date, weekly_holidays, holidays)
        
        # Initialize counters
        present_days = 0
        absent_days = 0
        late_days = 0
        half_days = 0
        leave_days = 0
        holiday_days = 0
        weekly_holiday_days = 0
        total_overtime_minutes = 0
        total_work_hours = 0
        
        # Holiday analysis
        holiday_absent_before = 0
        holiday_absent_after = 0
        consecutive_holiday_absences = []
        
        # Process each day
        current_date = start_date
        daily_records = {}
        
        # Organize attendance records by date
        for record in attendance_records:
            daily_records[record.date] = record
        
        # Organize leave applications by date
        leave_dates = set()
        for leave_app in leave_applications:
            if leave_app.status == 'APP':  # Approved leaves only
                current_leave_date = leave_app.start_date
                while current_leave_date <= leave_app.end_date:
                    if start_date <= current_leave_date <= end_date:
                        leave_dates.add(current_leave_date)
                    current_leave_date += timedelta(days=1)
        
        while current_date <= end_date:
            is_weekly_holiday = current_date.weekday() in weekly_holidays
            is_holiday = current_date in [h.date for h in holidays]
            is_leave = current_date in leave_dates
            
            if is_weekly_holiday:
                weekly_holiday_days += 1
            elif is_holiday:
                holiday_days += 1
            elif is_leave:
                leave_days += 1
            elif current_date in daily_records:
                # Employee was present
                record = daily_records[current_date]
                present_days += 1
                
                if record.status == 'LAT':
                    late_days += 1
                elif record.status == 'HAL':
                    half_days += 1
                
                total_overtime_minutes += record.overtime_minutes
                if hasattr(record, 'working_hours'):
                    total_work_hours += record.working_hours
            else:
                # Check ZK logs for this date to determine if truly absent
                daily_zk_logs = zk_logs.filter(timestamp__date=current_date)
                if daily_zk_logs.exists():
                    # Has ZK logs but no attendance record - process manually
                    shift_info = self._get_shift_for_date(employee, current_date, roster_data)
                    daily_record = self._process_zk_logs_for_date(employee, current_date, daily_zk_logs, shift_info)
                    
                    if daily_record and daily_record['work_minutes'] >= 30:  # Minimum work threshold
                        present_days += 1
                        if daily_record['status'] == 'LAT':
                            late_days += 1
                        elif daily_record['status'] == 'HAL':
                            half_days += 1
                        total_overtime_minutes += daily_record.get('overtime_minutes', 0)
                        total_work_hours += daily_record.get('work_hours', 0)
                    else:
                        absent_days += 1
                        # Check for holiday absence patterns
                        if form_data.get('include_holiday_analysis', True):
                            self._check_holiday_absence_pattern(
                                current_date, holidays, form_data.get('holiday_buffer_days', 1),
                                holiday_absent_before, holiday_absent_after, consecutive_holiday_absences
                            )
                else:
                    # Employee was absent
                    absent_days += 1
                    
                    # Check for holiday absence patterns
                    if form_data.get('include_holiday_analysis', True):
                        self._check_holiday_absence_pattern(
                            current_date, holidays, form_data.get('holiday_buffer_days', 1),
                            holiday_absent_before, holiday_absent_after, consecutive_holiday_absences
                        )
            
            current_date += timedelta(days=1)
        
        # Calculate attendance percentage
        attendance_percentage = (present_days / working_days * 100) if working_days > 0 else 0
        
        # Get leave balance information
        leave_balances = []
        if form_data.get('show_leave_balance', True):
            current_year = timezone.now().year
            try:
                leave_balances = employee.leave_balances.filter(year=current_year)
            except:
                leave_balances = []
        
        # Calculate overtime hours
        total_overtime_hours = round(total_overtime_minutes / 60, 2)
        
        # Holiday issues analysis
        holiday_issues = []
        if form_data.get('include_holiday_analysis', True):
            if holiday_absent_before > 0:
                holiday_issues.append(f"Absent {holiday_absent_before} day(s) before holidays")
            if holiday_absent_after > 0:
                holiday_issues.append(f"Absent {holiday_absent_after} day(s) after holidays")
            if consecutive_holiday_absences:
                holiday_issues.append(f"Consecutive absences around holidays: {len(consecutive_holiday_absences)} instance(s)")
        
        return {
            'employee': employee,
            'employee_id': employee.employee_id,
            'employee_name': employee.get_full_name(),
            'department': employee.department.name if employee.department else 'No Department',
            'designation': employee.designation.name if employee.designation else 'No Designation',
            'expected_work_hours': employee.expected_work_hours,
            'overtime_grace_minutes': employee.overtime_grace_minutes,
            
            # Attendance Summary
            'total_days': total_days,
            'working_days': working_days,
            'total_present_days': present_days,
            'total_absent_days': absent_days,
            'total_late_days': late_days,
            'total_half_days': half_days,
            'total_leave_days': leave_days,
            'total_holiday_days': holiday_days,
            'total_weekly_holiday_days': weekly_holiday_days,
            'attendance_percentage': round(attendance_percentage, 2),
            
            # Work Hours Summary
            'total_work_hours': round(total_work_hours, 2),
            'total_overtime_hours': total_overtime_hours,
            'total_overtime_minutes': total_overtime_minutes,
            'average_daily_hours': round(total_work_hours / present_days, 2) if present_days > 0 else 0,
            
            # Holiday Analysis
            'holiday_absent_before': holiday_absent_before,
            'holiday_absent_after': holiday_absent_after,
            'total_holiday_pattern_absences': holiday_absent_before + holiday_absent_after,
            'consecutive_holiday_absences': consecutive_holiday_absences,
            'holiday_issues': holiday_issues,
            
            # Leave Information
            'leave_balances': leave_balances,
            'approved_leaves': len(leave_applications),
            
            # Status Indicators
            'has_attendance_issues': absent_days > (working_days * 0.1),  # More than 10% absent
            'has_holiday_pattern': (holiday_absent_before + holiday_absent_after) > 0,
            'has_excessive_overtime': total_overtime_hours > (working_days * 2),  # More than 2h avg OT
        }
    
    def _check_holiday_absence_pattern(self, current_date, holidays, holiday_buffer_days, 
                                      holiday_absent_before, holiday_absent_after, consecutive_holiday_absences):
        """Check for absence patterns around holidays and track consecutive absences."""
        try:
            holiday_dates = [h.date for h in holidays]
            
            # Check if absent before holiday
            for holiday in holiday_dates:
                for i in range(1, holiday_buffer_days + 1):
                    if current_date == holiday - timedelta(days=i):
                        holiday_absent_before += 1
                        # Check for consecutive absence
                        if (current_date - timedelta(days=1)) in holiday_dates or \
                           (current_date - timedelta(days=1)) in [h - timedelta(days=j) for h in holiday_dates for j in range(1, holiday_buffer_days + 1)]:
                            consecutive_holiday_absences.append(current_date)
                        return  # Exit early to avoid double-counting
            
            # Check if absent after holiday
            for holiday in holiday_dates:
                for i in range(1, holiday_buffer_days + 1):
                    if current_date == holiday + timedelta(days=i):
                        holiday_absent_after += 1
                        # Check for consecutive absence
                        if (current_date + timedelta(days=1)) in holiday_dates or \
                           (current_date + timedelta(days=1)) in [h + timedelta(days=j) for h in holiday_dates for j in range(1, holiday_buffer_days + 1)]:
                            consecutive_holiday_absences.append(current_date)
                        return  # Exit early to avoid double-counting
        except Exception as e:
            logger.warning(f"Error checking holiday absence pattern: {str(e)}")
    
    def _process_zk_logs_for_date(self, employee, date, daily_logs, shift_info):
        """Process ZK logs for a specific date to determine attendance."""
        if not daily_logs.exists():
            return None
        
        # Get first and last punch
        first_punch = daily_logs.first()
        last_punch = daily_logs.last()
        
        # Calculate work duration
        if first_punch != last_punch:
            work_duration = last_punch.timestamp - first_punch.timestamp
            work_minutes = work_duration.total_seconds() / 60
        else:
            work_minutes = 0
        
        # Basic attendance record
        record = {
            'date': date,
            'check_in': first_punch.timestamp,
            'check_out': last_punch.timestamp if first_punch != last_punch else None,
            'work_minutes': int(work_minutes),
            'work_hours': round(work_minutes / 60, 2),
            'late_minutes': 0,
            'overtime_minutes': 0,
            'status': 'PRE',
        }
        
        # Calculate late arrival using employee's grace time
        if shift_info['expected_start'] and employee.overtime_grace_minutes is not None:
            expected_start_with_grace = shift_info['expected_start'] + timedelta(minutes=employee.overtime_grace_minutes)
            if first_punch.timestamp > expected_start_with_grace:
                late_duration = first_punch.timestamp - shift_info['expected_start']
                record['late_minutes'] = int(late_duration.total_seconds() / 60)
                record['status'] = 'LAT'
        
        # Calculate overtime using employee's overtime grace minutes
        if shift_info['expected_end'] and record['check_out'] and employee.overtime_grace_minutes is not None:
            overtime_threshold = shift_info['expected_end'] + timedelta(minutes=employee.overtime_grace_minutes)
            if record['check_out'] > overtime_threshold:
                overtime_duration = record['check_out'] - overtime_threshold
                record['overtime_minutes'] = int(overtime_duration.total_seconds() / 60)
        
        # Determine final status based on employee's expected work hours
        half_day_threshold = employee.expected_work_hours / 2
        if record['work_hours'] < half_day_threshold:
            record['status'] = 'HAL'
        
        return record
    
    def _get_shift_for_date(self, employee, date, roster_data):
        """Get shift information for employee on specific date with priority logic."""
        
        # Priority 1: Check RosterDay for specific date
        if 'days' in roster_data and date in roster_data['days']:
            roster_day = roster_data['days'][date]
            if roster_day.shift:
                try:
                    expected_start = timezone.datetime.combine(date, roster_day.shift.start_time)
                    expected_start = timezone.make_aware(expected_start, timezone.get_default_timezone())
                    
                    expected_end = timezone.datetime.combine(date, roster_day.shift.end_time)
                    expected_end = timezone.make_aware(expected_end, timezone.get_default_timezone())
                    
                    # Handle overnight shifts
                    if roster_day.shift.end_time < roster_day.shift.start_time:
                        expected_end += timedelta(days=1)
                    
                    return {
                        'shift': roster_day.shift,
                        'source': 'RosterDay',
                        'expected_start': expected_start,
                        'expected_end': expected_end,
                    }
                except Exception as e:
                    logger.warning(f"Error processing roster day shift: {str(e)}")
        
        # Priority 2: Check RosterAssignment for date range
        if 'assignments' in roster_data and date in roster_data['assignments']:
            roster_assignment = roster_data['assignments'][date]
            
            if roster_assignment.shift:
                try:
                    expected_start = timezone.datetime.combine(date, roster_assignment.shift.start_time)
                    expected_start = timezone.make_aware(expected_start, timezone.get_default_timezone())
                    
                    expected_end = timezone.datetime.combine(date, roster_assignment.shift.end_time)
                    expected_end = timezone.make_aware(expected_end, timezone.get_default_timezone())
                    
                    # Handle overnight shifts
                    if roster_assignment.shift.end_time < roster_assignment.shift.start_time:
                        expected_end += timedelta(days=1)
                    
                    return {
                        'shift': roster_assignment.shift,
                        'source': 'RosterAssignment',
                        'expected_start': expected_start,
                        'expected_end': expected_end,
                    }
                except Exception as e:
                    logger.warning(f"Error processing roster assignment shift: {str(e)}")
            
            elif employee.default_shift:
                try:
                    expected_start = timezone.datetime.combine(date, employee.default_shift.start_time)
                    expected_start = timezone.make_aware(expected_start, timezone.get_default_timezone())
                    
                    expected_end = timezone.datetime.combine(date, employee.default_shift.end_time)
                    expected_end = timezone.make_aware(expected_end, timezone.get_default_timezone())
                    
                    # Handle overnight shifts
                    if employee.default_shift.end_time < employee.default_shift.start_time:
                        expected_end += timedelta(days=1)
                    
                    return {
                        'shift': employee.default_shift,
                        'source': 'RosterAssignment',
                        'expected_start': expected_start,
                        'expected_end': expected_end,
                    }
                except Exception as e:
                    logger.warning(f"Error processing default shift from roster: {str(e)}")
        
        # Priority 3: Use employee's default shift
        if employee.default_shift:
            try:
                expected_start = timezone.datetime.combine(date, employee.default_shift.start_time)
                expected_start = timezone.make_aware(expected_start, timezone.get_default_timezone())
                
                expected_end = timezone.datetime.combine(date, employee.default_shift.end_time)
                expected_end = timezone.make_aware(expected_end, timezone.get_default_timezone())
                
                # Handle overnight shifts
                if employee.default_shift.end_time < employee.default_shift.start_time:
                    expected_end += timedelta(days=1)
                
                return {
                    'shift': employee.default_shift,
                    'source': 'Default',
                    'expected_start': expected_start,
                    'expected_end': expected_end,
                }
            except Exception as e:
                logger.warning(f"Error processing employee default shift: {str(e)}")
        
        # No shift found
        return {
            'shift': None,
            'source': 'None',
            'expected_start': None,
            'expected_end': None,
        }
    
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
    
    def _get_attendance_data(self, employees, start_date, end_date):
        """Get attendance records for employees in the period."""
        try:
            attendance_records = Attendance.objects.filter(
                employee__in=employees,
                date__gte=start_date,
                date__lte=end_date
            ).select_related('employee')
            
            # Group by employee
            employee_attendance = defaultdict(list)
            for record in attendance_records:
                employee_attendance[record.employee.id].append(record)
            
            return employee_attendance
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
    
    def _calculate_working_days(self, start_date, end_date, weekly_holidays, holidays):
        """Calculate working days excluding weekly holidays and public holidays."""
        working_days = 0
        holiday_dates = {h.date for h in holidays}
        
        current_date = start_date
        while current_date <= end_date:
            if (current_date.weekday() not in weekly_holidays and 
                current_date not in holiday_dates):
                working_days += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def _calculate_overall_statistics(self, employee_summaries, start_date, end_date):
        """Calculate overall statistics from employee summaries."""
        if not employee_summaries:
            return {}
        
        total_employees = len(employee_summaries)
        total_present_days = sum(emp['total_present_days'] for emp in employee_summaries)
        total_absent_days = sum(emp['total_absent_days'] for emp in employee_summaries)
        total_leave_days = sum(emp['total_leave_days'] for emp in employee_summaries)
        total_overtime_hours = sum(emp['total_overtime_hours'] for emp in employee_summaries)
        
        employees_with_issues = sum(1 for emp in employee_summaries if emp['has_attendance_issues'])
        employees_with_holiday_pattern = sum(1 for emp in employee_summaries if emp['has_holiday_pattern'])
        employees_with_excessive_overtime = sum(1 for emp in employee_summaries if emp['has_excessive_overtime'])
        
        avg_attendance_percentage = sum(emp['attendance_percentage'] for emp in employee_summaries) / total_employees
        
        return {
            'total_employees': total_employees,
            'total_present_days': total_present_days,
            'total_absent_days': total_absent_days,
            'total_leave_days': total_leave_days,
            'total_overtime_hours': round(total_overtime_hours, 2),
            'average_attendance_percentage': round(avg_attendance_percentage, 2),
            'employees_with_issues': employees_with_issues,
            'employees_with_holiday_pattern': employees_with_holiday_pattern,
            'employees_with_excessive_overtime': employees_with_excessive_overtime,
            'period_days': (end_date - start_date).days + 1,
        }