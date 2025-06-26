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
from django.http import JsonResponse
from django.db import transaction
import json

from Hrm.models import *
from .unified_attendance_processor import UnifiedAttendanceProcessor

logger = logging.getLogger(__name__)

class AttendanceImportForm(forms.Form):
    """Form for importing attendance data from ZK logs using UnifiedAttendanceProcessor."""
    
    # Date Range
    start_date = forms.DateField(
        label=_("Start Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the start date for attendance import processing.")
    )
    end_date = forms.DateField(
        label=_("End Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Select the end date for attendance import processing.")
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
    
    # Import Options
    update_existing_records = forms.BooleanField(
        label=_("Update Existing Records"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Update existing attendance records if they already exist.")
    )
    
    import_only_complete = forms.BooleanField(
        label=_("Import Only Complete Records"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Only import records that have both check-in and check-out times.")
    )
    
    # UnifiedAttendanceProcessor Settings
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
    
    # Advanced Rules
    late_to_absent_days = forms.IntegerField(
        label=_("Late to Absent Conversion (Days)"),
        initial=3,
        min_value=1,
        max_value=10,
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

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(_("Start date cannot be after end date."))
            
            # Check date range is not too large
            if (end_date - start_date).days > 90:
                raise forms.ValidationError(_("Date range cannot exceed 90 days for import processing."))
        
        return cleaned_data

class AttendanceImportView(LoginRequiredMixin, View):
    """View for importing attendance data from ZK logs using UnifiedAttendanceProcessor."""
    template_name = 'report/hrm/attendance_import.html'
    
    def get(self, request, *args, **kwargs):
        form = AttendanceImportForm()
        
        # Set default dates to last 7 days
        today = timezone.now().date()
        form.fields['end_date'].initial = today
        form.fields['start_date'].initial = today - timedelta(days=7)
        
        context_data = self._get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        # Handle AJAX import request
        if request.headers.get('Content-Type') == 'application/json':
            return self._handle_attendance_import(request)
        
        form = AttendanceImportForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                import_data = self._generate_attendance_import_data(form.cleaned_data)
                
                context_data.update({
                    'import_generated': True,
                    'attendance_data': import_data['attendance_data'],
                    'summary_data': import_data['summary_data'],
                    'form_data': form.cleaned_data,
                    'total_records': len(import_data['attendance_data']),
                })
                
                messages.success(request, _("Attendance import data generated successfully. {} records ready for import.").format(
                    len(import_data['attendance_data'])))
                
            except Exception as e:
                logger.error(f"Error generating attendance import data: {str(e)}")
                messages.error(request, _("Failed to generate import data: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'page_title': _("Attendance Import from ZK Logs"),
            'import_generated': False,
        }
    
    def _generate_attendance_import_data(self, form_data):
        """Generate attendance import data using UnifiedAttendanceProcessor."""
        start_date = form_data['start_date']
        end_date = form_data['end_date']
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        
        # Get holidays for the period
        holidays = Holiday.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Get ZK attendance logs for the period and employees
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
        
        attendance_data = []
        summary_data = {
            'total_employees': len(employees),
            'total_days_processed': (end_date - start_date).days + 1,
            'total_records': 0,
            'complete_records': 0,
            'incomplete_records': 0,
            'present_records': 0,
            'late_records': 0,
            'half_day_records': 0,
            'overtime_records': 0,
            'existing_records': 0,
            'new_records': 0,
        }
        
        for employee in employees:
            employee_logs = zk_logs.filter(user_id=employee.employee_id)
            employee_roster_data = roster_data.get(employee.id, {})
            
            # Get leave applications for this employee and period
            leave_applications = LeaveApplication.objects.filter(
                employee=employee,
                status='APP',
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            # Process attendance for this employee for the entire period
            attendance_result = processor.process_employee_attendance(
                employee, start_date, end_date, employee_logs,
                holidays, leave_applications, employee_roster_data
            )
            
            # Process daily records for import
            for daily_record in attendance_result.get('daily_records', []):
                # Skip holidays, weekends, and leaves for import
                if daily_record['status'] in ['HOL', 'LEA']:
                    continue
                
                # Check if record already exists
                existing_record = Attendance.objects.filter(
                    employee=employee,
                    date=daily_record['date']
                ).first()
                
                if existing_record:
                    summary_data['existing_records'] += 1
                else:
                    summary_data['new_records'] += 1
                
                # Create import record
                import_record = {
                    'employee': employee,
                    'employee_id': employee.employee_id,
                    'employee_name': employee.get_full_name(),
                    'department': employee.department.name if employee.department else 'N/A',
                    'designation': employee.designation.name if employee.designation else 'N/A',
                    'date': daily_record['date'],
                    'day_name': daily_record['day_name'],
                    'status': daily_record['status'],
                    'status_display': self._get_status_display(daily_record['status']),
                    'check_in': daily_record['in_time'],
                    'check_out': daily_record['out_time'],
                    'working_hours': daily_record['working_hours'],
                    'late_minutes': daily_record['late_minutes'],
                    'early_out_minutes': daily_record['early_out_minutes'],
                    'overtime_minutes': int(daily_record['overtime_hours'] * 60) if daily_record['overtime_hours'] else 0,
                    'shift_name': daily_record['shift_name'],
                    'roster_day_id': None,  # Will be set if roster day exists
                    'is_manual': False,
                    'remarks': f"Imported from ZK logs using UnifiedAttendanceProcessor on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    'existing_record': existing_record is not None,
                    'ready_for_import': True,
                    'expected_work_hours': employee.expected_work_hours,
                    'overtime_grace_minutes': employee.overtime_grace_minutes,
                }
                
                # Check if complete record
                if import_record['check_in'] and import_record['check_out']:
                    summary_data['complete_records'] += 1
                else:
                    summary_data['incomplete_records'] += 1
                
                # Update status counts
                if daily_record['status'] == 'PRE':
                    summary_data['present_records'] += 1
                elif daily_record['status'] == 'LAT':
                    summary_data['late_records'] += 1
                elif daily_record['status'] == 'HAL':
                    summary_data['half_day_records'] += 1
                
                if daily_record['overtime_hours'] > 0:
                    summary_data['overtime_records'] += 1
                
                # Skip incomplete records if option is set
                if form_data.get('import_only_complete', True) and not import_record['check_out']:
                    import_record['ready_for_import'] = False
                    import_record['remarks'] += " (Skipped: Incomplete record)"
                
                attendance_data.append(import_record)
                summary_data['total_records'] += 1
        
        return {
            'attendance_data': attendance_data,
            'summary_data': summary_data,
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
        """Import attendance records to Attendance model."""
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
                        
                        # Get roster day if exists
                        roster_day = None
                        try:
                            roster_day = RosterDay.objects.filter(
                                roster_assignment__employee=employee,
                                date=date
                            ).first()
                        except:
                            pass
                        
                        # Prepare attendance data
                        attendance_data = {
                            'employee': employee,
                            'date': date,
                            'status': record_data.get('status', 'PRE'),
                            'roster_day': roster_day,
                            'check_in': datetime.fromisoformat(record_data['check_in'].replace('Z', '+00:00')) if record_data.get('check_in') else None,
                            'check_out': datetime.fromisoformat(record_data['check_out'].replace('Z', '+00:00')) if record_data.get('check_out') else None,
                            'late_minutes': record_data.get('late_minutes', 0),
                            'early_out_minutes': record_data.get('early_out_minutes', 0),
                            'overtime_minutes': record_data.get('overtime_minutes', 0),
                            'is_manual': False,
                            'remarks': f"Imported from ZK logs using UnifiedAttendanceProcessor on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} by {user.username}. Employee Settings: {employee.expected_work_hours}h work, {employee.overtime_grace_minutes}m OT grace.",
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
        
        message = f'Attendance import completed using UnifiedAttendanceProcessor. Imported: {imported_count}, Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'imported': imported_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': error_count,
            'error_details': error_details[:10],  # Limit error details
        })
