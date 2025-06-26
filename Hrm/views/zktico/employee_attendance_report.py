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
from collections import defaultdict

from Hrm.models import (
    ZKAttendanceLog, Employee, Holiday, LeaveApplication, 
    RosterDay, RosterAssignment, Shift, ShortLeaveApplication, 
    OvertimeRecord
)
from .unified_attendance_processor import UnifiedAttendanceProcessor

logger = logging.getLogger(__name__)

class EmployeeDetailedAttendanceReportForm(forms.Form):
    """Enhanced form for generating detailed employee attendance report with modal options."""
    
    employee_id = forms.CharField(
        label=_("Employee ID"),
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'e.g., E001',
            'list': 'employee-list'
        }),
        help_text=_("Enter the employee's unique ID.")
    )
    
    start_date = forms.DateField(
        label=_("Start Date"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Defaults to 30 days ago if blank.")
    )
    
    end_date = forms.DateField(
        label=_("End Date"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Defaults to today if blank.")
    )
    
    # Weekend Configuration
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
    
    # Modal Configuration Options
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
    
    # Advanced Options
    include_summary = forms.BooleanField(
        label=_("Include Summary"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include detailed attendance summary statistics.")
    )
    
    show_roster_details = forms.BooleanField(
        label=_("Show Roster Details"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Show detailed roster assignment information.")
    )
    
    enable_overtime_import = forms.BooleanField(
        label=_("Enable Overtime Import"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Allow importing calculated overtime as overtime records.")
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        employee_id = cleaned_data.get('employee_id')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_("Start date cannot be after end date."))

        if start_date and end_date and (end_date - start_date).days > 365:
            raise forms.ValidationError(_("Date range cannot exceed 365 days."))

        if employee_id:
            try:
                Employee.objects.get(employee_id=employee_id)
            except Employee.DoesNotExist:
                raise forms.ValidationError(_("Employee ID does not exist."))

        return cleaned_data

class EmployeeDetailedAttendanceReportView(LoginRequiredMixin, View):
    """Unified view using shared attendance processing logic."""
    template_name = 'report/hrm/employee_detailed_attendance_report.html'

    def get(self, request, *args, **kwargs):
        form = EmployeeDetailedAttendanceReportForm()
        employees = Employee.objects.filter(is_active=True).values('employee_id', 'first_name', 'last_name')
        
        return render(request, self.template_name, {
            'form': form,
            'employees': employees,
            'report_generated': False,
            'page_title': _("Employee Detailed Attendance Report"),
        })

    def post(self, request, *args, **kwargs):
        # Handle AJAX overtime import request
        if request.headers.get('Content-Type') == 'application/json':
            return self._handle_overtime_import(request)
        
        form = EmployeeDetailedAttendanceReportForm(request.POST)
        employees = Employee.objects.filter(is_active=True).values('employee_id', 'first_name', 'last_name')
        
        context = {
            'form': form,
            'employees': employees,
            'report_generated': False,
            'page_title': _("Employee Detailed Attendance Report"),
        }

        if form.is_valid():
            employee_id = form.cleaned_data['employee_id']
            start_date = form.cleaned_data['start_date'] or (timezone.now().date() - timedelta(days=30))
            end_date = form.cleaned_data['end_date'] or timezone.now().date()
            
            try:
                employee = Employee.objects.select_related(
                    'default_shift', 'department', 'designation'
                ).get(employee_id=employee_id)
                
                # Use unified processor
                processor = UnifiedAttendanceProcessor(form.cleaned_data)
                
                # Get required data
                zk_logs = self._get_zk_attendance_logs(employee, start_date, end_date)
                holidays = self._get_holidays(start_date, end_date)
                leaves = self._get_leaves(employee, start_date, end_date)
                roster_data = self._get_roster_data(employee, start_date, end_date)
                
                # Process attendance with unified logic
                result = processor.process_employee_attendance(
                    employee, start_date, end_date, zk_logs, holidays, leaves, roster_data
                )
                
                context.update({
                    'report_generated': True,
                    'employee': employee,
                    'attendance_data': result['daily_records'],
                    'summary_data': result['summary_stats'] if form.cleaned_data['include_summary'] else None,
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_days': (end_date - start_date).days + 1,
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, _("Detailed attendance report generated for {} from {} to {}.").format(
                    employee.get_full_name(), start_date.strftime('%d %b %Y'), end_date.strftime('%d %b %Y')))
                
            except Employee.DoesNotExist:
                messages.error(request, _("Employee with ID {} not found.").format(employee_id))
            except Exception as e:
                logger.error(f"Error generating detailed report for {employee_id}: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context)

    def _handle_overtime_import(self, request):
        """Handle AJAX request for importing overtime records."""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'import_overtime':
                overtime_records = data.get('overtime_records', [])
                return self._import_overtime_records(overtime_records, request.user)
            else:
                return JsonResponse({'success': False, 'message': 'Invalid action'})
                
        except Exception as e:
            logger.error(f"Error in overtime import: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})

    def _import_overtime_records(self, overtime_records, user):
        """Import overtime records from attendance data."""
        imported_count = 0
        skipped_count = 0
        error_count = 0
        duplicate_details = []
        
        try:
            with transaction.atomic():
                for record_data in overtime_records:
                    try:
                        employee = Employee.objects.get(employee_id=record_data['employee_id'])
                        date = datetime.strptime(record_data['date'], '%Y-%m-%d').date()
                        overtime_hours = float(record_data['overtime_hours'])
                        
                        # Skip if no overtime hours
                        if overtime_hours <= 0:
                            skipped_count += 1
                            continue
                        
                        # Check for existing overtime record
                        existing_record = OvertimeRecord.objects.filter(
                            employee=employee,
                            date=date
                        ).first()
                        
                        if existing_record:
                            skipped_count += 1
                            duplicate_details.append({
                                'employee_id': employee.employee_id,
                                'date': date.strftime('%Y-%m-%d'),
                                'existing_hours': float(existing_record.hours),
                                'new_hours': overtime_hours
                            })
                            continue
                        
                        # Calculate start and end times
                        shift_end_time = record_data.get('shift_end_time')
                        if shift_end_time:
                            shift_end = datetime.strptime(shift_end_time, '%H:%M:%S').time()
                            start_time = shift_end
                            
                            start_datetime = datetime.combine(date, start_time)
                            end_datetime = start_datetime + timedelta(hours=overtime_hours)
                            end_time = end_datetime.time()
                            
                            if end_datetime.date() > date:
                                end_time = time(23, 59, 59)
                        else:
                            start_time = time(18, 0, 0)
                            end_datetime = datetime.combine(date, start_time) + timedelta(hours=overtime_hours)
                            end_time = end_datetime.time()
                        
                        # Create overtime record
                        OvertimeRecord.objects.create(
                            employee=employee,
                            date=date,
                            start_time=start_time,
                            end_time=end_time,
                            hours=overtime_hours,
                            reason=f"Imported from detailed attendance report - {record_data.get('reason', 'Overtime work')}",
                            status='PEN',
                            remarks=f"Auto-imported on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        imported_count += 1
                        
                    except Employee.DoesNotExist:
                        error_count += 1
                        logger.error(f"Employee not found: {record_data.get('employee_id')}")
                        continue
                    except Exception as e:
                        logger.error(f"Error importing overtime record: {str(e)}")
                        error_count += 1
                        continue
                        
        except Exception as e:
            logger.error(f"Transaction error in overtime import: {str(e)}")
            return JsonResponse({
                'success': False, 
                'message': f'Transaction failed: {str(e)}'
            })
        
        message = f'Overtime import completed. Imported: {imported_count}, Skipped: {skipped_count}, Errors: {error_count}'
        if duplicate_details:
            message += f'\n\nDuplicate records skipped:\n'
            for dup in duplicate_details[:5]:
                message += f"- {dup['employee_id']} on {dup['date']} (existing: {dup['existing_hours']}h, new: {dup['new_hours']}h)\n"
            if len(duplicate_details) > 5:
                message += f"... and {len(duplicate_details) - 5} more duplicates"
        
        return JsonResponse({
            'success': True,
            'message': message,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': error_count,
            'duplicates': duplicate_details
        })

    # Helper methods
    def _get_zk_attendance_logs(self, employee, start_date, end_date):
        """Get ZK attendance logs for the employee."""
        return ZKAttendanceLog.objects.filter(
            user_id=employee.employee_id,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        ).select_related('device').order_by('timestamp')

    def _get_holidays(self, start_date, end_date):
        """Get holidays in the date range."""
        return Holiday.objects.filter(
            date__gte=start_date, 
            date__lte=end_date
        ).order_by('date')

    def _get_leaves(self, employee, start_date, end_date):
        """Get approved leaves for the employee."""
        return LeaveApplication.objects.filter(
            employee=employee,
            status='APP',
            start_date__lte=end_date,
            end_date__gte=start_date
        ).select_related('leave_type').order_by('start_date')

    def _get_roster_data(self, employee, start_date, end_date):
        """Get roster assignments and roster days for the employee."""
        roster_data = {'assignments': {}, 'days': {}}
        
        try:
            # Get roster assignments
            roster_assignments = RosterAssignment.objects.filter(
                employee=employee,
                roster__start_date__lte=end_date,
                roster__end_date__gte=start_date
            ).select_related('roster', 'shift', 'employee')
            
            # Get roster days
            roster_days = RosterDay.objects.filter(
                roster_assignment__employee=employee,
                date__gte=start_date,
                date__lte=end_date
            ).select_related('shift', 'roster_assignment__roster', 'roster_assignment__shift')
            
            # Organize roster assignments by date range
            for assignment in roster_assignments:
                current_date = max(assignment.roster.start_date, start_date)
                end_assignment_date = min(assignment.roster.end_date, end_date)
                
                while current_date <= end_assignment_date:
                    roster_data['assignments'][current_date] = assignment
                    current_date += timedelta(days=1)
            
            # Organize roster days
            for roster_day in roster_days:
                roster_data['days'][roster_day.date] = roster_day
                
        except Exception as e:
            logger.warning(f"Could not fetch roster data: {str(e)}")
        
        return roster_data
