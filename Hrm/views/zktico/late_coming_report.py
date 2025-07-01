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

class LateComingReportForm(forms.Form):
    """Form for generating late coming report."""
    
    # Date Range
    start_date = forms.DateField(
        label=_("Start Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the start date for the late coming report.")
    )
    end_date = forms.DateField(
        label=_("End Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the end date for the late coming report.")
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
    
    # Late Coming Criteria
    minimum_late_minutes = forms.IntegerField(
        label=_("Minimum Late Minutes"),
        initial=1,
        min_value=1,
        max_value=480,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Show only late arrivals with at least this many minutes.")
    )
    
    late_category_filter = forms.ChoiceField(
        label=_("Late Category Filter"),
        choices=[
            ('all', _('All Late Arrivals')),
            ('minor', _('Minor Late (1-15 minutes)')),
            ('moderate', _('Moderate Late (16-30 minutes)')),
            ('major', _('Major Late (31-60 minutes)')),
            ('severe', _('Severe Late (60+ minutes)')),
        ],
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Filter late arrivals by severity category.")
    )
    
    # Reporting Options
    show_repeated_offenders = forms.BooleanField(
        label=_("Highlight Repeated Offenders"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Highlight employees with multiple late arrivals.")
    )
    
    repeated_offender_threshold = forms.IntegerField(
        label=_("Repeated Offender Threshold"),
        initial=3,
        min_value=2,
        max_value=20,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Number of late days to consider as repeated offender.")
    )
    
    include_converted_absents = forms.BooleanField(
        label=_("Include Converted Absents"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include late days that were converted to absent due to policy.")
    )
    
    group_by_employee = forms.BooleanField(
        label=_("Group by Employee"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Group results by employee instead of chronological order.")
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
        help_text=_("Grace period for late arrival in minutes.")
    )
    
    exclude_holidays = forms.BooleanField(
        label=_("Exclude Holidays"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Exclude holiday dates from late coming analysis.")
    )
    
    exclude_leave_days = forms.BooleanField(
        label=_("Exclude Leave Days"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Exclude approved leave days from late coming analysis.")
    )
    
    # Late to Absent Conversion Settings
    late_to_absent_days = forms.IntegerField(
        label=_("Late to Absent Conversion (Days)"),
        initial=3,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Convert consecutive late days to absent after this threshold.")
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(_("Start date cannot be after end date."))
            
            if (end_date - start_date).days > 180:
                raise forms.ValidationError(_("Date range cannot exceed 180 days for performance reasons."))
        
        return cleaned_data

class LateComingReportView(LoginRequiredMixin, View):
    """View for generating late coming reports."""
    template_name = 'report/hrm/late_coming_report.html'
    
    def get(self, request, *args, **kwargs):
        form = LateComingReportForm()
        
        # Set default dates
        today = timezone.now().date()
        form.fields['start_date'].initial = today - timedelta(days=30)
        form.fields['end_date'].initial = today
        
        context_data = self._get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        # Handle export request
        if 'export' in request.POST:
            return self._handle_export(request)
        
        form = LateComingReportForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                report_data = self._generate_late_coming_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'late_coming_data': report_data['late_coming_data'],
                    'summary_data': report_data['summary_data'],
                    'repeated_offenders': report_data['repeated_offenders'],
                    'category_breakdown': report_data['category_breakdown'],
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, _("Late coming report generated successfully. Found {} late arrival records.").format(
                    len(report_data['late_coming_data'])))
                
            except Exception as e:
                logger.error(f"Error generating late coming report: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'page_title': _("Late Coming Report"),
            'report_generated': False,
        }
    
    def _generate_late_coming_report(self, form_data):
        """Generate late coming report using UnifiedAttendanceProcessor."""
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
        
        late_coming_data = []
        employee_late_counts = {}
        category_breakdown = {
            'minor': 0,    # 1-15 minutes
            'moderate': 0, # 16-30 minutes
            'major': 0,    # 31-60 minutes
            'severe': 0,   # 60+ minutes
        }
        
        summary_data = {
            'total_employees': len(employees),
            'total_days_checked': (end_date - start_date).days + 1,
            'total_late_instances': 0,
            'employees_with_late_arrivals': 0,
            'average_late_minutes': 0.0,
            'total_late_minutes': 0,
            'most_late_employee': None,
            'most_late_day': None,
            'converted_to_absent': 0,
        }
        
        total_late_minutes = 0
        employees_with_late = set()
        daily_late_counts = {}
        max_employee_late_count = 0
        max_late_employee = None
        
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
            
            employee_late_count = 0
            
            # Analyze late arrivals from daily records
            for daily_record in attendance_result['daily_records']:
                late_record = self._analyze_late_arrival(
                    daily_record, employee, form_data
                )
                
                if late_record:
                    late_coming_data.append(late_record)
                    employee_late_count += 1
                    employees_with_late.add(employee.id)
                    
                    # Update category breakdown
                    late_minutes = late_record['late_minutes']
                    if late_minutes <= 15:
                        category_breakdown['minor'] += 1
                    elif late_minutes <= 30:
                        category_breakdown['moderate'] += 1
                    elif late_minutes <= 60:
                        category_breakdown['major'] += 1
                    else:
                        category_breakdown['severe'] += 1
                    
                    # Track daily late counts
                    date_str = daily_record['date'].strftime('%Y-%m-%d')
                    daily_late_counts[date_str] = daily_late_counts.get(date_str, 0) + 1
                    
                    total_late_minutes += late_minutes
                    
                    # Check if converted to absent
                    if daily_record.get('converted_from_late', False):
                        summary_data['converted_to_absent'] += 1
            
            if employee_late_count > 0:
                employee_late_counts[employee.id] = employee_late_count
                
                # Track most late employee
                if employee_late_count > max_employee_late_count:
                    max_employee_late_count = employee_late_count
                    max_late_employee = {
                        'employee': employee,
                        'late_count': employee_late_count
                    }
        
        # Filter by late category if specified
        if form_data['late_category_filter'] != 'all':
            late_coming_data = self._filter_by_category(
                late_coming_data, form_data['late_category_filter']
            )
        
        # Filter by minimum late minutes
        min_late_minutes = form_data['minimum_late_minutes']
        late_coming_data = [
            record for record in late_coming_data
            if record['late_minutes'] >= min_late_minutes
        ]
        
        # Group by employee if requested
        if form_data['group_by_employee']:
            late_coming_data = self._group_by_employee(late_coming_data)
        
        # Identify repeated offenders
        repeated_offenders = []
        threshold = form_data['repeated_offender_threshold']
        
        if form_data['show_repeated_offenders']:
            for employee_id, late_count in employee_late_counts.items():
                if late_count >= threshold:
                    employee = Employee.objects.get(id=employee_id)
                    repeated_offenders.append({
                        'employee': employee,
                        'employee_id': employee.employee_id,
                        'employee_name': employee.get_full_name(),
                        'department': employee.department.name if employee.department else 'N/A',
                        'designation': employee.designation.name if employee.designation else 'N/A',
                        'late_count': late_count,
                        'late_records': [r for r in late_coming_data if r['employee_id'] == employee.employee_id]
                    })
        
        # Update summary statistics
        summary_data['total_late_instances'] = len(late_coming_data)
        summary_data['employees_with_late_arrivals'] = len(employees_with_late)
        summary_data['total_late_minutes'] = total_late_minutes
        summary_data['most_late_employee'] = max_late_employee
        
        if total_late_minutes > 0 and len(late_coming_data) > 0:
            summary_data['average_late_minutes'] = round(total_late_minutes / len(late_coming_data), 2)
        
        # Find most late day
        if daily_late_counts:
            most_late_day = max(daily_late_counts.items(), key=lambda x: x[1])
            summary_data['most_late_day'] = {
                'date': most_late_day[0],
                'count': most_late_day[1]
            }
        
        return {
            'late_coming_data': late_coming_data,
            'summary_data': summary_data,
            'repeated_offenders': repeated_offenders,
            'category_breakdown': category_breakdown,
        }
    
    def _analyze_late_arrival(self, daily_record, employee, form_data):
        """Analyze daily record for late arrival."""
        # Skip if not a late arrival
        if daily_record['status'] != 'LAT' or daily_record['late_minutes'] <= 0:
            return None
        
        # Skip holidays, leaves, and weekends if configured
        if daily_record['status'] in ['HOL', 'LEA']:
            return None
        
        # Skip weekends if configured
        if daily_record['date'].weekday() in form_data['weekend_days']:
            return None
        
        # Skip if converted to absent and not including converted absents
        if (daily_record.get('converted_from_late', False) and 
            not form_data['include_converted_absents']):
            return None
        
        return {
            'employee': employee,
            'employee_id': employee.employee_id,
            'employee_name': employee.get_full_name(),
            'department': employee.department.name if employee.department else 'N/A',
            'designation': employee.designation.name if employee.designation else 'N/A',
            'date': daily_record['date'],
            'day_name': daily_record['day_name'],
            'late_minutes': daily_record['late_minutes'],
            'late_category': self._get_late_category(daily_record['late_minutes']),
            'shift_name': daily_record['shift_name'],
            'shift_start_time': daily_record['shift_start_time'],
            'expected_in_time': daily_record['shift_start_time'],
            'actual_in_time': daily_record['in_time'],
            'out_time': daily_record['out_time'],
            'working_hours': daily_record['working_hours'],
            'overtime_hours': daily_record['overtime_hours'],
            'roster_info': daily_record['roster_info'],
            'converted_from_late': daily_record.get('converted_from_late', False),
            'late_count_running': daily_record.get('late_count_running', 0),
        }
    
    def _get_late_category(self, late_minutes):
        """Get late category based on minutes."""
        if late_minutes <= 15:
            return 'minor'
        elif late_minutes <= 30:
            return 'moderate'
        elif late_minutes <= 60:
            return 'major'
        else:
            return 'severe'
    
    def _filter_by_category(self, late_data, category):
        """Filter late data by category."""
        return [record for record in late_data if record['late_category'] == category]
    
    def _group_by_employee(self, late_data):
        """Group late data by employee."""
        grouped_data = {}
        
        for record in late_data:
            employee_id = record['employee_id']
            if employee_id not in grouped_data:
                grouped_data[employee_id] = []
            grouped_data[employee_id].append(record)
        
        # Convert back to flat list, grouped by employee
        result = []
        for employee_id in sorted(grouped_data.keys()):
            # Sort employee's records by date
            employee_records = sorted(grouped_data[employee_id], key=lambda x: x['date'])
            result.extend(employee_records)
        
        return result
    
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
        """Handle CSV export of late coming report."""
        form = LateComingReportForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please fix form errors before exporting."))
            return self.post(request)
        
        try:
            report_data = self._generate_late_coming_report(form.cleaned_data)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="late_coming_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Employee ID', 'Employee Name', 'Department', 'Designation',
                'Date', 'Day', 'Late Minutes', 'Late Category', 'Shift',
                'Expected In Time', 'Actual In Time', 'Out Time', 'Working Hours',
                'Overtime Hours', 'Converted to Absent', 'Running Late Count'
            ])
            
            for record in report_data['late_coming_data']:
                writer.writerow([
                    record['employee_id'],
                    record['employee_name'],
                    record['department'],
                    record['designation'],
                    record['date'].strftime('%Y-%m-%d'),
                    record['day_name'],
                    record['late_minutes'],
                    record['late_category'].title(),
                    record['shift_name'],
                    record['expected_in_time'].strftime('%H:%M') if record['expected_in_time'] else '',
                    record['actual_in_time'].strftime('%Y-%m-%d %H:%M:%S') if record['actual_in_time'] else '',
                    record['out_time'].strftime('%Y-%m-%d %H:%M:%S') if record['out_time'] else '',
                    record['working_hours'],
                    record['overtime_hours'],
                    'Yes' if record['converted_from_late'] else 'No',
                    record['late_count_running'],
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting late coming report: {str(e)}")
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)
