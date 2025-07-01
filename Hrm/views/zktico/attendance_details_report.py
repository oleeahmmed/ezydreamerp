import logging
from datetime import timedelta, datetime, time
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.db.models import Q, Min, Max, Prefetch
from django.http import JsonResponse
from django.db import transaction
import json

from Hrm.models import *

logger = logging.getLogger(__name__)

class AttendanceDetailsReportForm(forms.Form):
    """Advanced form for generating attendance details report for import to Attendance model."""
    
    # Date Range
    start_date = forms.DateField(
        label=_("Start Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the start date for attendance processing. This will be the beginning of your report period.")
    )
    end_date = forms.DateField(
        label=_("End Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the end date for attendance processing. This will be the end of your report period.")
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
        help_text=_("Choose how you want to filter employees for the report. 'All' includes every active employee.")
    )
    
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
        help_text=_("Select one or more departments. Hold Ctrl/Cmd to select multiple departments.")
    )
    
    designations = forms.ModelMultipleChoiceField(
        queryset=Designation.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
        help_text=_("Select one or more designations. Hold Ctrl/Cmd to select multiple designations.")
    )
    
    employee_ids = forms.CharField(
        label=_("Specific Employee IDs"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'EMP001, EMP002, EMP003'
        }),
        help_text=_("Enter specific employee IDs separated by commas (e.g., EMP001, EMP002). Leave blank if not using specific filter.")
    )
    
    # Attendance Processing Options
    include_incomplete_days = forms.BooleanField(
        label=_("Include Incomplete Attendance"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include days where employee has only check-in OR check-out (not both). Useful for identifying incomplete punches.")
    )
    
    minimum_work_minutes = forms.IntegerField(
        label=_("Minimum Work Duration (Minutes)"),
        initial=30,
        min_value=0,
        max_value=1440,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '30'
        }),
        help_text=_("Minimum minutes between first and last punch to consider as valid attendance. Records below this will be filtered out.")
    )
    
    grace_minutes = forms.IntegerField(
        label=_("Late Arrival Grace Period (Minutes)"),
        initial=15,
        min_value=0,
        max_value=120,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '15'
        }),
        help_text=_("Default grace time for late arrival. Individual employee settings will override this.")
    )
    
    early_departure_threshold = forms.IntegerField(
        label=_("Early Departure Threshold (Minutes)"),
        initial=15,
        min_value=0,
        max_value=120,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '15'
        }),
        help_text=_("Minutes before shift end time to consider as early departure. Leaving before this will be flagged.")
    )
    
    half_day_threshold_hours = forms.FloatField(
        label=_("Half Day Threshold (Hours)"),
        initial=4.0,
        min_value=1.0,
        max_value=8.0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '4.0',
            'step': '0.5'
        }),
        help_text=_("Work hours below this threshold will be marked as half day. Individual employee expected hours will be considered.")
    )
    
    # Advanced Options
    exclude_holidays = forms.BooleanField(
        label=_("Exclude Holiday Dates"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Exclude dates that are marked as holidays in the system. Recommended to avoid false absent records.")
    )
    
    exclude_weekends = forms.BooleanField(
        label=_("Exclude Weekends"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Exclude Saturday and Sunday from absent employee calculation. Enable if your organization doesn't work on weekends.")
    )
    
    include_separated_employees = forms.BooleanField(
        label=_("Include Separated Employees"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include employees who have been separated/terminated during the report period.")
    )
    
    show_device_info = forms.BooleanField(
        label=_("Show Device Information"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Display which ZK device was used for each punch. Useful for tracking attendance sources.")
    )
    
    # Absent Employee Options
    track_absent_employees = forms.BooleanField(
        label=_("Track Absent Employees"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Generate a separate report for employees who were absent during the selected period.")
    )
    
    absent_consecutive_days = forms.IntegerField(
        label=_("Highlight Consecutive Absent Days"),
        initial=3,
        min_value=1,
        max_value=30,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '3'
        }),
        help_text=_("Highlight employees who have been absent for this many consecutive days or more.")
    )
    
    # Import Options
    create_attendance_records = forms.BooleanField(
        label=_("Auto-Create Attendance Records"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Automatically create Attendance model records from processed data. Use with caution.")
    )
    
    update_existing_records = forms.BooleanField(
        label=_("Update Existing Records"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Update existing attendance records if they already exist. Will overwrite current data.")
    )
    
    import_only_complete = forms.BooleanField(
        label=_("Import Only Complete Records"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Only import records that have both check-in and check-out times. Recommended for data integrity.")
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        employee_filter = cleaned_data.get('employee_filter')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(_("Start date cannot be after end date."))
            
            # Check date range is not too large
            if (end_date - start_date).days > 365:
                raise forms.ValidationError(_("Date range cannot exceed 365 days for performance reasons."))
        
        # Validate employee filter options
        if employee_filter == 'department':
            departments = cleaned_data.get('departments')
            if not departments:
                raise forms.ValidationError(_("Please select at least one department when filtering by department."))
        
        if employee_filter == 'designation':
            designations = cleaned_data.get('designations')
            if not designations:
                raise forms.ValidationError(_("Please select at least one designation when filtering by designation."))
                
        if employee_filter == 'specific':
            employee_ids = cleaned_data.get('employee_ids')
            if not employee_ids:
                raise forms.ValidationError(_("Please enter employee IDs when using specific employee filter."))

        return cleaned_data

class AttendanceDetailsReportView(LoginRequiredMixin, View):
    """Advanced view to generate attendance details report from ZKAttendanceLog for Attendance model import."""
    template_name = 'report/hrm/attendance_details_report.html'
    
    def get(self, request, *args, **kwargs):
        form = AttendanceDetailsReportForm()
        
        # Set default dates to current date
        today = timezone.now().date()
        form.fields['start_date'].initial = today
        form.fields['end_date'].initial = today
        
        # Get context data
        context_data = self._get_context_data(form)
        
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        # Handle AJAX import request
        if request.headers.get('Content-Type') == 'application/json':
            return self._handle_attendance_import(request)
        
        form = AttendanceDetailsReportForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                report_data = self._generate_attendance_details_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'attendance_data': report_data['attendance_data'],
                    'absent_data': report_data['absent_data'],
                    'summary_data': report_data['summary_data'],
                    'form_data': form.cleaned_data,
                    'total_present_records': len(report_data['attendance_data']),
                    'total_absent_records': len(report_data['absent_data']),
                })
                
                messages.success(request, _("Attendance details report generated successfully. Present: {}, Absent: {}").format(
                    len(report_data['attendance_data']), len(report_data['absent_data'])))
                
            except Exception as e:
                logger.error(f"Error generating attendance details report: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'employees': Employee.objects.filter(is_active=True).values('employee_id', 'first_name', 'last_name').order_by('employee_id'),
            'report_generated': False,
            'page_title': _("Advanced Attendance Details Report"),
        }
    
    def _generate_attendance_details_report(self, form_data):
        """Generate comprehensive attendance details report from ZKAttendanceLog data."""
        start_date = form_data['start_date']
        end_date = form_data['end_date']
        track_absent = form_data['track_absent_employees']
        exclude_holidays = form_data['exclude_holidays']
        exclude_weekends = form_data['exclude_weekends']
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        
        # Get holidays if excluding them
        holidays = set()
        if exclude_holidays:
            try:
                holiday_dates = Holiday.objects.filter(
                    date__gte=start_date,
                    date__lte=end_date
                ).values_list('date', flat=True)
                holidays = set(holiday_dates)
            except Exception as e:
                logger.warning(f"Could not fetch holidays: {str(e)}")
        
        # Get ZK attendance logs for the period and employees
        attendance_logs = self._get_zk_attendance_logs(employees, start_date, end_date)
        
        # Get roster and shift data
        roster_data = self._get_roster_data(employees, start_date, end_date)
        
        # Process attendance data
        attendance_data = []
        absent_data = []
        summary_data = {
            'total_employees': len(employees),
            'total_days_processed': (end_date - start_date).days + 1,
            'total_present_records': 0,
            'total_absent_records': 0,
            'complete_records': 0,
            'incomplete_records': 0,
            'overtime_records': 0,
            'late_records': 0,
            'early_out_records': 0,
            'half_day_records': 0,
            'consecutive_absent_employees': 0,
        }
        
        for employee in employees:
            employee_logs = attendance_logs.filter(user_id=employee.employee_id)
            employee_roster_data = roster_data.get(employee.id, {})
            employee_absent_days = []
            
            # Process each day for this employee
            current_date = start_date
            while current_date <= end_date:
                # Skip if should exclude this date
                if self._should_exclude_date(current_date, holidays, exclude_weekends):
                    current_date += timedelta(days=1)
                    continue
                
                daily_record = self._process_daily_attendance(
                    employee, current_date, employee_logs, employee_roster_data, form_data
                )
                
                if daily_record:
                    attendance_data.append(daily_record)
                    summary_data['total_present_records'] += 1
                    
                    # Update summary statistics
                    if daily_record['check_out']:
                        summary_data['complete_records'] += 1
                    else:
                        summary_data['incomplete_records'] += 1
                    
                    if daily_record['status'] == 'LAT':
                        summary_data['late_records'] += 1
                    elif daily_record['status'] == 'HAL':
                        summary_data['half_day_records'] += 1
                    
                    if daily_record['overtime_minutes'] > 0:
                        summary_data['overtime_records'] += 1
                    
                    if daily_record['early_out_minutes'] > 0:
                        summary_data['early_out_records'] += 1
                        
                elif track_absent:
                    # Employee was absent on this day - check for partial attendance
                    shift_info = self._get_shift_for_date(employee, current_date, employee_roster_data)
                    absent_reason_info = self._determine_absent_reason(employee, current_date, employee_logs, shift_info)
                    
                    absent_record = {
                        'employee': employee,
                        'employee_id': employee.employee_id,
                        'employee_name': employee.get_full_name(),
                        'department': employee.department.name if employee.department else 'N/A',
                        'designation': employee.designation.name if employee.designation else 'N/A',
                        'date': current_date,
                        'day_name': current_date.strftime('%A'),
                        'shift_info': shift_info,
                        'is_consecutive': False,
                        'absent_reason': absent_reason_info['reason'],
                        'check_in': absent_reason_info['check_in'],
                        'check_out': absent_reason_info['check_out'],
                        'total_logs': absent_reason_info['total_logs'],
                        'partial_attendance': absent_reason_info['partial_attendance'],
                        'work_minutes': 0,
                        'work_hours': 0.0,
                        'expected_work_hours': employee.expected_work_hours,
                        'overtime_grace_minutes': employee.overtime_grace_minutes,
                    }
                    
                    # Calculate work time if there are check-in/out times
                    if absent_record['check_in'] and absent_record['check_out']:
                        work_duration = absent_record['check_out'] - absent_record['check_in']
                        absent_record['work_minutes'] = int(work_duration.total_seconds() / 60)
                        absent_record['work_hours'] = round(absent_record['work_minutes'] / 60, 2)
                    
                    employee_absent_days.append(absent_record)
                
                current_date += timedelta(days=1)
            
            # Process absent days for consecutive tracking
            if track_absent and employee_absent_days:
                consecutive_count = self._mark_consecutive_absent_days(
                    employee_absent_days, form_data.get('absent_consecutive_days', 3)
                )
                if consecutive_count > 0:
                    summary_data['consecutive_absent_employees'] += 1
                
                absent_data.extend(employee_absent_days)
                summary_data['total_absent_records'] += len(employee_absent_days)
        
        return {
            'attendance_data': attendance_data,
            'absent_data': absent_data,
            'summary_data': summary_data,
        }
    
    def _should_exclude_date(self, date, holidays, exclude_weekends):
        """Check if date should be excluded from processing."""
        if date in holidays:
            return True
        
        if exclude_weekends and date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return True
            
        return False
    
    def _mark_consecutive_absent_days(self, absent_days, threshold):
        """Mark consecutive absent days and return count of employees with consecutive absences."""
        if not absent_days or len(absent_days) < threshold:
            return 0
        
        # Sort by date
        absent_days.sort(key=lambda x: x['date'])
        
        consecutive_count = 1
        max_consecutive = 1
        
        for i in range(1, len(absent_days)):
            current_date = absent_days[i]['date']
            prev_date = absent_days[i-1]['date']
            
            if (current_date - prev_date).days == 1:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 1
        
        # Mark consecutive days if threshold is met
        if max_consecutive >= threshold:
            consecutive_count = 1
            for i in range(1, len(absent_days)):
                current_date = absent_days[i]['date']
                prev_date = absent_days[i-1]['date']
                
                if (current_date - prev_date).days == 1:
                    consecutive_count += 1
                    if consecutive_count >= threshold:
                        # Mark current and previous days as consecutive
                        absent_days[i]['is_consecutive'] = True
                        absent_days[i-1]['is_consecutive'] = True
                else:
                    consecutive_count = 1
            
            return 1
        
        return 0
    
    def _get_filtered_employees(self, form_data):
        """Get employees based on advanced filter criteria."""
        employee_filter = form_data['employee_filter']
        include_separated = form_data['include_separated_employees']
        
        # Base queryset
        queryset = Employee.objects.select_related('department', 'designation', 'default_shift')
        
        if not include_separated:
            queryset = queryset.filter(is_active=True)
        
        if employee_filter == 'all':
            return queryset
        
        elif employee_filter == 'department':
            departments = form_data['departments']
            return queryset.filter(department__in=departments)
        
        elif employee_filter == 'designation':
            designations = form_data['designations']
            return queryset.filter(designation__in=designations)
        
        elif employee_filter == 'specific':
            employee_ids = [id.strip() for id in form_data['employee_ids'].split(',') if id.strip()]
            return queryset.filter(employee_id__in=employee_ids)
        
        return queryset.none()
    
    def _get_zk_attendance_logs(self, employees, start_date, end_date):
        """Get ZK attendance logs for employees and date range."""
        employee_ids = [emp.employee_id for emp in employees]
        
        return ZKAttendanceLog.objects.filter(
            user_id__in=employee_ids,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        ).select_related('device').order_by('user_id', 'timestamp')
    
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
    
    def _process_daily_attendance(self, employee, date, employee_logs, roster_data, form_data):
        """Process attendance for a single day with employee-specific settings."""
        
        # Get logs for this specific date
        daily_logs = employee_logs.filter(timestamp__date=date).order_by('timestamp')
        
        if not daily_logs.exists():
            return None
        
        # Get first and last punch
        first_punch = daily_logs.first()
        last_punch = daily_logs.last()
        
        # Check if we have both in and out (or if incomplete days are allowed)
        if first_punch == last_punch and not form_data.get('include_incomplete_days', True):
            return None
        
        # Calculate work duration
        if first_punch != last_punch:
            work_duration = last_punch.timestamp - first_punch.timestamp
            work_minutes = work_duration.total_seconds() / 60
        else:
            work_minutes = 0
        
        # Skip if work duration is below minimum
        minimum_work_minutes = form_data.get('minimum_work_minutes', 30)
        if work_minutes < minimum_work_minutes:
            return None
        
        # Get shift information for this date
        shift_info = self._get_shift_for_date(employee, date, roster_data)
        
        # Calculate attendance metrics with employee-specific settings
        attendance_record = {
            'employee': employee,
            'employee_id': employee.employee_id,
            'employee_name': employee.get_full_name(),
            'department': employee.department.name if employee.department else 'N/A',
            'designation': employee.designation.name if employee.designation else 'N/A',
            'date': date,
            'day_name': date.strftime('%A'),
            'check_in': first_punch.timestamp,
            'check_out': last_punch.timestamp if first_punch != last_punch else None,
            'total_logs': daily_logs.count(),
            'work_minutes': int(work_minutes),
            'work_hours': round(work_minutes / 60, 2),
            'shift': shift_info['shift'],
            'shift_name': shift_info['shift'].name if shift_info['shift'] else 'No Shift',
            'shift_source': shift_info['source'],
            'roster_info': shift_info['roster_info'],
            'expected_start': shift_info['expected_start'],
            'expected_end': shift_info['expected_end'],
            'late_minutes': 0,
            'early_out_minutes': 0,
            'overtime_minutes': 0,
            'status': 'PRE',
            'is_roster_day': shift_info['source'] in ['RosterDay', 'RosterAssignment'],
            'ready_for_import': True,
            'device_info': first_punch.device.name if form_data.get('show_device_info', False) and first_punch.device else '',
            'expected_work_hours': employee.expected_work_hours,
            'overtime_grace_minutes': employee.overtime_grace_minutes,
        }
        
        # Calculate late arrival using employee's grace time or form default
        employee_grace_minutes = employee.overtime_grace_minutes if hasattr(employee, 'overtime_grace_minutes') else form_data.get('grace_minutes', 15)
        if shift_info['expected_start'] and employee_grace_minutes is not None:
            expected_start_with_grace = shift_info['expected_start'] + timedelta(minutes=employee_grace_minutes)
            if first_punch.timestamp > expected_start_with_grace:
                late_duration = first_punch.timestamp - shift_info['expected_start']
                attendance_record['late_minutes'] = int(late_duration.total_seconds() / 60)
                attendance_record['status'] = 'LAT'
        
        # Calculate early departure
        early_departure_threshold = form_data.get('early_departure_threshold', 15)
        if shift_info['expected_end'] and attendance_record['check_out'] and early_departure_threshold is not None:
            early_threshold = shift_info['expected_end'] - timedelta(minutes=early_departure_threshold)
            if attendance_record['check_out'] < early_threshold:
                early_duration = shift_info['expected_end'] - attendance_record['check_out']
                attendance_record['early_out_minutes'] = int(early_duration.total_seconds() / 60)
        
        # Calculate overtime using employee's overtime grace minutes
        employee_overtime_grace = employee.overtime_grace_minutes if hasattr(employee, 'overtime_grace_minutes') else 15
        if shift_info['expected_end'] and attendance_record['check_out'] and employee_overtime_grace is not None:
            overtime_threshold = shift_info['expected_end'] + timedelta(minutes=employee_overtime_grace)
            if attendance_record['check_out'] > overtime_threshold:
                overtime_duration = attendance_record['check_out'] - overtime_threshold
                attendance_record['overtime_minutes'] = int(overtime_duration.total_seconds() / 60)
        
        # Determine final status based on employee's expected work hours
        employee_expected_hours = employee.expected_work_hours if hasattr(employee, 'expected_work_hours') else 8
        half_day_threshold = employee_expected_hours / 2  # Half of employee's expected hours
        
        if attendance_record['work_hours'] < half_day_threshold:
            attendance_record['status'] = 'HAL'
        
        return attendance_record
    
    def _get_shift_for_date(self, employee, date, roster_data):
        """Get shift information for employee on specific date with priority logic."""
        
        # Priority 1: Check RosterDay for specific date
        if date in roster_data.get('days', {}):
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
                        'roster_info': f"Roster Day: {roster_day.roster_assignment.roster.name}",
                        'expected_start': expected_start,
                        'expected_end': expected_end,
                    }
                except Exception as e:
                    logger.warning(f"Error processing roster day shift: {str(e)}")
        
        # Priority 2: Check RosterAssignment for date range
        if date in roster_data.get('assignments', {}):
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
                        'roster_info': f"Roster Assignment: {roster_assignment.roster.name}",
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
                        'roster_info': f"Roster Assignment (Default Shift): {roster_assignment.roster.name}",
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
                    'roster_info': "Employee Default Shift",
                    'expected_start': expected_start,
                    'expected_end': expected_end,
                }
            except Exception as e:
                logger.warning(f"Error processing employee default shift: {str(e)}")
        
        # No shift found
        return {
            'shift': None,
            'source': 'None',
            'roster_info': "No Shift Assigned",
            'expected_start': None,
            'expected_end': None,
        }
    
    def _handle_attendance_import(self, request):
        """Handle AJAX request for importing attendance records."""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'import_attendance':
                attendance_records = data.get('attendance_records', [])
                update_existing = data.get('update_existing', False)
                import_only_complete = data.get('import_only_complete', True)
                return self._import_attendance_records(attendance_records, update_existing, import_only_complete, request.user)
            else:
                return JsonResponse({'success': False, 'message': 'Invalid action'})
                
        except Exception as e:
            logger.error(f"Error in attendance import: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    
    def _import_attendance_records(self, attendance_records, update_existing, import_only_complete, user):
        """Import attendance records to Attendance model with advanced options."""
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        error_details = []
        
        try:
            with transaction.atomic():
                for record_data in attendance_records:
                    try:
                        # Skip incomplete records if option is set
                        if import_only_complete and not record_data.get('check_out'):
                            skipped_count += 1
                            continue
                        
                        employee = Employee.objects.get(employee_id=record_data['employee_id'])
                        date = datetime.strptime(record_data['date'], '%Y-%m-%d').date()
                        
                        # Check for existing attendance record
                        existing_record = Attendance.objects.filter(
                            employee=employee,
                            date=date
                        ).first()
                        
                        if existing_record and not update_existing:
                            skipped_count += 1
                            continue
                        
                        # Prepare attendance data
                        attendance_data = {
                            'employee': employee,
                            'date': date,
                            'status': record_data.get('status', 'PRE'),
                            'check_in': datetime.fromisoformat(record_data['check_in'].replace('Z', '+00:00')) if record_data.get('check_in') else None,
                            'check_out': datetime.fromisoformat(record_data['check_out'].replace('Z', '+00:00')) if record_data.get('check_out') else None,
                            'late_minutes': record_data.get('late_minutes', 0),
                            'early_out_minutes': record_data.get('early_out_minutes', 0),
                            'overtime_minutes': record_data.get('overtime_minutes', 0),
                            'is_manual': False,
                            'remarks': f"Imported from ZK attendance logs on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} by {user.username}. Employee Expected Hours: {employee.expected_work_hours}h, Overtime Grace: {employee.overtime_grace_minutes}m",
                        }
                        
                        if existing_record:
                            # Update existing record
                            for key, value in attendance_data.items():
                                if key != 'employee':  # Don't update employee field
                                    setattr(existing_record, key, value)
                            existing_record.save()
                            updated_count += 1
                        else:
                            # Create new record
                            Attendance.objects.create(**attendance_data)
                            imported_count += 1
                            
                    except Employee.DoesNotExist:
                        error_count += 1
                        error_details.append(f"Employee not found: {record_data.get('employee_id')}")
                        continue
                    except Exception as e:
                        logger.error(f"Error importing attendance record: {str(e)}")
                        error_count += 1
                        error_details.append(f"Error processing {record_data.get('employee_id')} on {record_data.get('date')}: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Transaction error in attendance import: {str(e)}")
            return JsonResponse({
                'success': False, 
                'message': f'Transaction failed: {str(e)}'
            })
        
        message = f'Attendance import completed. Imported: {imported_count}, Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'imported': imported_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': error_count,
            'error_details': error_details[:10],  # Limit error details
        })

    def _determine_absent_reason(self, employee, date, employee_logs, shift_info):
        """Determine the reason for absence and any partial attendance."""
        daily_logs = employee_logs.filter(timestamp__date=date).order_by('timestamp')
        
        if not daily_logs.exists():
            return {
                'reason': 'No Attendance',
                'check_in': None,
                'check_out': None,
                'total_logs': 0,
                'partial_attendance': False
            }
        
        # Has some logs but might be incomplete
        first_punch = daily_logs.first()
        last_punch = daily_logs.last()
        
        # Check if we have both in and out
        if first_punch == last_punch:
            # Only one punch
            return {
                'reason': 'Incomplete Attendance (Single Punch)',
                'check_in': first_punch.timestamp,
                'check_out': None,
                'total_logs': daily_logs.count(),
                'partial_attendance': True
            }
        
        # Calculate work duration
        work_duration = last_punch.timestamp - first_punch.timestamp
        work_minutes = work_duration.total_seconds() / 60
        
        # Check against minimum work minutes
        minimum_work_minutes = 30  # Default minimum
        if work_minutes < minimum_work_minutes:
            return {
                'reason': f'Insufficient Work Time ({int(work_minutes)}m < {minimum_work_minutes}m)',
                'check_in': first_punch.timestamp,
                'check_out': last_punch.timestamp,
                'total_logs': daily_logs.count(),
                'partial_attendance': True
            }
        
        # Should not reach here if properly filtered, but just in case
        return {
            'reason': 'Other',
            'check_in': first_punch.timestamp,
            'check_out': last_punch.timestamp,
            'total_logs': daily_logs.count(),
            'partial_attendance': True
        }