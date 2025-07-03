import logging
from datetime import timedelta, datetime
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
import json
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from concurrent.futures import ThreadPoolExecutor, as_completed

from Hrm.models import *
from .unified_attendance_processor import UnifiedAttendanceProcessor

logger = logging.getLogger(__name__)

class AttendanceImportForm(forms.Form):
    """🔥 COMPLETELY FIXED - Enhanced form with EXACT field names matching UnifiedAttendanceProcessor."""
    
    # Date Range Selection
    start_date = forms.DateField(
        label=_("Start Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    
    end_date = forms.DateField(
        label=_("End Date"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
    )
    
    designations = forms.ModelMultipleChoiceField(
        queryset=Designation.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
    )
    
    employee_ids = forms.CharField(
        label=_("Specific Employee IDs"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'EMP001, EMP002, EMP003'
        }),
    )
    
    # Basic Configuration - EXACT MATCH with UnifiedAttendanceProcessor
    grace_minutes = forms.IntegerField(
        label=_("Grace Minutes"),
        initial=15,
        min_value=0,
        max_value=120,
    )
    
    early_out_threshold_minutes = forms.IntegerField(
        label=_("Early Out Threshold (Minutes)"),
        initial=30,
        min_value=0,
        max_value=240,
    )
    
    overtime_start_after_minutes = forms.IntegerField(
        label=_("Overtime Start After (Minutes)"),
        initial=15,
        min_value=0,
        max_value=120,
    )
    
    minimum_overtime_minutes = forms.IntegerField(
        label=_("Minimum Overtime (Minutes)"),
        initial=60,
        min_value=0,
        max_value=480,
    )
    
    # 🔥 NEW RULE 1: Minimum Working Hours Rule - FIXED FIELD NAME
    minimum_working_hours_for_present = forms.FloatField(
        label=_("Minimum Working Hours For Present"),
        initial=4.0,
        min_value=1.0,
        max_value=12.0,
        required=False,
    )
    
    enable_minimum_working_hours_rule = forms.BooleanField(
        label=_("Enable Minimum Working Hours Rule"),
        required=False,
        initial=False,
    )
    
    # 🔥 NEW RULE 2: Half Day Rule - FIXED FIELD NAMES
    half_day_minimum_hours = forms.FloatField(
        label=_("Half Day Minimum Hours"),
        initial=2.0,
        min_value=1.0,
        max_value=4.0,
        required=False,
    )
    
    half_day_maximum_hours = forms.FloatField(
        label=_("Half Day Maximum Hours"),
        initial=4.0,
        min_value=2.0,
        max_value=6.0,
        required=False,
    )
    
    enable_working_hours_half_day_rule = forms.BooleanField(
        label=_("Enable Working Hours Half Day Rule"),
        required=False,
        initial=False,
    )
    
    # 🔥 NEW RULE 3: Both In/Out Required - FIXED FIELD NAME
    require_both_in_and_out = forms.BooleanField(
        label=_("Both Check-In & Check-Out Required"),
        required=False,
        initial=False,
    )
    
    # 🔥 NEW RULE 4: Maximum Working Hours - FIXED FIELD NAME
    maximum_allowable_working_hours = forms.FloatField(
        label=_("Maximum Allowable Working Hours"),
        initial=12.0,
        min_value=8.0,
        max_value=24.0,
        required=False,
    )
    
    enable_maximum_working_hours_rule = forms.BooleanField(
        label=_("Enable Maximum Working Hours Rule"),
        required=False,
        initial=False,
    )
    
    # 🔥 NEW RULE 5: Dynamic Shift Detection - ADDED MISSING FIELDS
    dynamic_shift_fallback_to_default = forms.BooleanField(
        label=_("Dynamic Shift Fallback to Default"),
        required=False,
        initial=True,
    )
    
    dynamic_shift_fallback_shift_id = forms.IntegerField(
        label=_("Dynamic Shift Fallback Shift ID"),
        required=False,
        min_value=1,
    )
    
    # 🔥 NEW RULE 6: Grace Time per Shift - ADDED MISSING FIELD
    use_shift_grace_time = forms.BooleanField(
        label=_("Use Shift Grace Time"),
        required=False,
        initial=False,
    )
    
    # 🔥 NEW RULE 7: Consecutive Absence - ADDED MISSING FIELDS
    consecutive_absence_termination_risk_days = forms.IntegerField(
        label=_("Consecutive Absence Termination Risk Days"),
        initial=5,
        min_value=1,
        max_value=30,
        required=False,
    )
    
    enable_consecutive_absence_flagging = forms.BooleanField(
        label=_("Enable Consecutive Absence Flagging"),
        required=False,
        initial=False,
    )
    
    # 🔥 NEW RULE 8: Max Early Out - ADDED MISSING FIELDS
    max_early_out_threshold_minutes = forms.IntegerField(
        label=_("Max Early Out Threshold Minutes"),
        initial=120,
        min_value=30,
        max_value=480,
        required=False,
    )
    
    max_early_out_occurrences = forms.IntegerField(
        label=_("Max Early Out Occurrences"),
        initial=3,
        min_value=1,
        max_value=10,
        required=False,
    )
    
    enable_max_early_out_flagging = forms.BooleanField(
        label=_("Enable Max Early Out Flagging"),
        required=False,
        initial=False,
    )
    
    # 🔥 Enhanced Shift Detection - ADDED MISSING FIELDS
    enable_dynamic_shift_detection = forms.BooleanField(
        label=_("Enable Dynamic Shift Detection"),
        required=False,
        initial=False,
    )
    
    dynamic_shift_tolerance_minutes = forms.IntegerField(
        label=_("Dynamic Shift Tolerance Minutes"),
        initial=30,
        min_value=5,
        max_value=120,
        required=False,
    )
    
    multiple_shift_priority = forms.ChoiceField(
        label=_("Multiple Shift Priority"),
        choices=[
            ('least_break', _('Least Break Time')),
            ('shortest_duration', _('Shortest Duration')),
            ('alphabetical', _('Alphabetical')),
            ('highest_score', _('Highest Score')),
        ],
        initial='least_break',
        required=False,
    )
    
    # 🔥 Advanced Overtime Configuration - ADDED MISSING FIELDS
    overtime_calculation_method = forms.ChoiceField(
        label=_("Overtime Calculation Method"),
        choices=[
            ('shift_based', _('Shift Based')),
            ('hours_based', _('Hours Based')),
        ],
        initial='shift_based',
        required=False,
    )
    
    holiday_overtime_full_day = forms.BooleanField(
        label=_("Holiday Overtime Full Day"),
        required=False,
        initial=True,
    )
    
    weekend_overtime_full_day = forms.BooleanField(
        label=_("Weekend Overtime Full Day"),
        required=False,
        initial=True,
    )
    
    late_affects_overtime = forms.BooleanField(
        label=_("Late Affects Overtime"),
        required=False,
        initial=False,
    )
    
    separate_ot_break_time = forms.IntegerField(
        label=_("Separate OT Break Time (Minutes)"),
        initial=0,
        min_value=0,
        max_value=120,
        required=False,
    )
    
    # 🔥 Break Time Configuration - ADDED MISSING FIELDS
    use_shift_break_time = forms.BooleanField(
        label=_("Use Shift Break Time"),
        required=False,
        initial=True,
    )
    
    default_break_minutes = forms.IntegerField(
        label=_("Default Break Minutes"),
        initial=60,
        min_value=0,
        max_value=180,
        required=False,
    )
    
    break_deduction_method = forms.ChoiceField(
        label=_("Break Deduction Method"),
        choices=[
            ('fixed', _('Fixed')),
            ('proportional', _('Proportional')),
        ],
        initial='fixed',
        required=False,
    )
    
    # 🔥 Advanced Rules - ADDED MISSING FIELDS
    late_to_absent_days = forms.IntegerField(
        label=_("Late to Absent Days"),
        initial=3,
        min_value=1,
        max_value=10,
        required=False,
    )
    
    holiday_before_after_absent = forms.BooleanField(
        label=_("Holiday Before After Absent"),
        required=False,
        initial=True,
    )
    
    weekend_before_after_absent = forms.BooleanField(
        label=_("Weekend Before After Absent"),
        required=False,
        initial=True,
    )
    
    require_holiday_presence = forms.BooleanField(
        label=_("Require Holiday Presence"),
        required=False,
        initial=False,
    )
    
    include_holiday_analysis = forms.BooleanField(
        label=_("Include Holiday Analysis"),
        required=False,
        initial=True,
    )
    
    holiday_buffer_days = forms.IntegerField(
        label=_("Holiday Buffer Days"),
        initial=1,
        min_value=0,
        max_value=5,
        required=False,
    )
    
    # 🔥 Employee Override Settings - ADDED MISSING FIELDS
    use_employee_specific_grace = forms.BooleanField(
        label=_("Use Employee Specific Grace"),
        required=False,
        initial=True,
    )
    
    use_employee_specific_overtime = forms.BooleanField(
        label=_("Use Employee Specific Overtime"),
        required=False,
        initial=True,
    )
    
    use_employee_expected_hours = forms.BooleanField(
        label=_("Use Employee Expected Hours"),
        required=False,
        initial=True,
    )
    
    # Weekend Configuration
    weekend_days = forms.MultipleChoiceField(
        label=_("Weekend Days"),
        choices=[
            (0, _("Monday")),
            (1, _("Tuesday")),
            (2, _("Wednesday")),
            (3, _("Thursday")),
            (4, _("Friday")),
            (5, _("Saturday")),
            (6, _("Sunday")),
        ],
        initial=[4],  # Friday
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )


class AttendanceImportView(LoginRequiredMixin, View):
    """Fast attendance import view following ZK device sync pattern."""
    template_name = 'report/hrm/attendance_import.html'
    
    def get(self, request, *args, **kwargs):
        """Handle GET request - show form."""
        form = AttendanceImportForm()
        
        # Set default date range to current month
        today = timezone.now().date()
        first_day = today.replace(day=1)
        form.fields['start_date'].initial = first_day
        form.fields['end_date'].initial = today
        
        context_data = self.get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        """Handle POST request - generate attendance data for preview."""
        form = AttendanceImportForm(request.POST)
        context_data = self.get_context_data(form)

        if form.is_valid():
            try:
                report_data = self.generate_attendance_data_for_import(form.cleaned_data)
                
                context_data.update({
                    'data_generated': True,
                    'attendance_records': report_data['attendance_records'],
                    'summary_stats': report_data['summary_stats'],
                    'form_data': form.cleaned_data,
                    'total_records': len(report_data['attendance_records']),
                    'start_date': form.cleaned_data['start_date'],
                    'end_date': form.cleaned_data['end_date'],
                })
                
                messages.success(request, _("Attendance data generated successfully for {} records. Review and import.").format(
                    len(report_data['attendance_records'])))
                
            except Exception as e:
                logger.error(f"Error generating attendance data for import: {str(e)}")
                messages.error(request, _("Failed to generate data: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'shifts': Shift.objects.all().order_by('name'),
            'title': _("🔥 Attendance Import with ALL Enhanced Options"),
            'subtitle': _("Import attendance records with comprehensive processing rules and duplicate validation"),
            'data_generated': False,
        }
    
    def get_filtered_employees(self, form_data):
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
    
    def get_roster_data_for_employee(self, employee, start_date, end_date):
        """Get roster data for an employee within date range."""
        roster_data = {
            'days': {},
            'assignments': {}
        }
        
        # Get roster days
        roster_days = RosterDay.objects.filter(
            roster_assignment__employee=employee,
            date__range=[start_date, end_date]
        ).select_related('shift', 'roster_assignment__roster')
        
        for roster_day in roster_days:
            roster_data['days'][roster_day.date] = roster_day
        
        # Get roster assignments
        roster_assignments = RosterAssignment.objects.filter(
            employee=employee,
            roster__start_date__lte=end_date,
            roster__end_date__gte=start_date
        ).select_related('roster', 'shift')
        
        for assignment in roster_assignments:
            current_date = max(assignment.roster.start_date, start_date)
            end_assignment_date = min(assignment.roster.end_date, end_date)
            
            while current_date <= end_assignment_date:
                if current_date not in roster_data['days']:
                    roster_data['assignments'][current_date] = assignment
                current_date += timedelta(days=1)
        
        return roster_data
    
    def process_employee_attendance(self, employee, start_date, end_date, form_data):
        """Process attendance for a single employee using UnifiedAttendanceProcessor."""
        try:
            # Get ZK logs for this employee
            zk_logs = ZKAttendanceLog.objects.filter(
                user_id=employee.employee_id,
                timestamp__date__range=[start_date, end_date]
            ).order_by('timestamp')
            
            # Get leave applications
            leave_applications = LeaveApplication.objects.filter(
                employee=employee,
                status='APP',
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            # Get holidays
            holidays = Holiday.objects.filter(date__range=[start_date, end_date])
            
            # Get roster data
            roster_data = self.get_roster_data_for_employee(employee, start_date, end_date)
            
            # Initialize the unified processor
            processor = UnifiedAttendanceProcessor(form_data)
            
            # Process attendance using unified processor
            result = processor.process_employee_attendance(
                employee=employee,
                start_date=start_date,
                end_date=end_date,
                zk_logs=zk_logs,
                holidays=holidays,
                leave_applications=leave_applications,
                roster_data=roster_data
            )
            
            return result['daily_records']
            
        except Exception as e:
            logger.error(f"Error processing employee {employee.employee_id}: {str(e)}")
            return []
    
    def generate_attendance_data_for_import(self, form_data):
        """Generate attendance data for import preview using parallel processing."""
        start_date = form_data['start_date']
        end_date = form_data['end_date']
        
        employees = self.get_filtered_employees(form_data)
        
        attendance_records = []
        summary_stats = {
            'total_employees': len(employees),
            'total_records': 0,
            'present_records': 0,
            'absent_records': 0,
            'late_records': 0,
            'half_day_records': 0,
            'leave_records': 0,
            'holiday_records': 0,
            'existing_records': 0,
            'new_records': 0,
        }
        
        # Process employees in parallel for better performance
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_employee = {
                executor.submit(self.process_employee_attendance, employee, start_date, end_date, form_data): employee 
                for employee in employees
            }
            
            for future in as_completed(future_to_employee):
                employee = future_to_employee[future]
                try:
                    daily_records = future.result()
                    
                    # Convert daily records to attendance records
                    for daily_record in daily_records:
                        attendance_record = self.convert_daily_record_to_attendance(
                            employee, daily_record, summary_stats
                        )
                        if attendance_record:
                            attendance_records.append(attendance_record)
                            
                except Exception as e:
                    logger.error(f"Error processing employee {employee.employee_id}: {str(e)}")
                    continue
        
        summary_stats['total_records'] = len(attendance_records)
        summary_stats['new_records'] = summary_stats['total_records'] - summary_stats['existing_records']
        
        return {
            'attendance_records': attendance_records,
            'summary_stats': summary_stats,
        }
    
    def convert_daily_record_to_attendance(self, employee, daily_record, summary_stats):
        """Convert daily record to attendance record format."""
        date = daily_record['date']
        
        # Check if record already exists
        existing_record = Attendance.objects.filter(
            employee=employee,
            date=date
        ).first()
        
        if existing_record:
            summary_stats['existing_records'] += 1
            is_duplicate = True
        else:
            is_duplicate = False
        
        # Count by status
        status = daily_record['status']
        if status == 'PRE':
            summary_stats['present_records'] += 1
        elif status == 'ABS':
            summary_stats['absent_records'] += 1
        elif status == 'LAT':
            summary_stats['late_records'] += 1
        elif status == 'LEA':
            summary_stats['leave_records'] += 1
        elif status == 'HOL':
            summary_stats['holiday_records'] += 1
        elif status == 'HAL':
            summary_stats['half_day_records'] += 1
        
        # Create attendance record data
        attendance_record = {
            'employee_id': employee.employee_id,
            'employee_name': employee.get_full_name(),
            'date': date.strftime('%Y-%m-%d'),
            'status': status,
            'check_in': daily_record.get('in_time').strftime('%Y-%m-%d %H:%M:%S') if daily_record.get('in_time') else None,
            'check_out': daily_record.get('out_time').strftime('%Y-%m-%d %H:%M:%S') if daily_record.get('out_time') else None,
            'working_hours': daily_record.get('working_hours', 0.0),
            'late_minutes': daily_record.get('late_minutes', 0),
            'early_out_minutes': daily_record.get('early_out_minutes', 0),
            'overtime_minutes': int(daily_record.get('overtime_hours', 0) * 60),
            'is_duplicate': is_duplicate,
            'remarks': daily_record.get('remarks'),
            'shift_name': daily_record.get('shift_name', 'No Shift'),
            'selected': not is_duplicate,  # Auto-select non-duplicates
        }
        
        return attendance_record


@method_decorator(csrf_exempt, name='dispatch')
class AttendanceImportSaveView(View):
    """Fast save view for attendance import data."""
    
    def post(self, request, *args, **kwargs):
        """Handle POST request to save selected attendance data."""
        try:
            data = json.loads(request.body)
            attendance_data = data.get('attendance_data', [])
            
            if not attendance_data:
                return JsonResponse({
                    'success': False,
                    'error': _('No attendance data provided')
                }, status=400)
            
            saved_count = 0
            updated_count = 0
            skipped_count = 0
            errors = []
            saved_records = []
            
            with transaction.atomic():
                for record in attendance_data:
                    try:
                        # Validate required fields
                        required_fields = ['employee_id', 'date', 'status']
                        if not all(field in record for field in required_fields):
                            errors.append(f"Missing required fields in record: {record}")
                            continue
                        
                        # Get employee
                        try:
                            employee = Employee.objects.get(employee_id=record['employee_id'])
                        except Employee.DoesNotExist:
                            errors.append(f"Employee with ID {record['employee_id']} not found")
                            continue
                        
                        # Parse date
                        try:
                            date = datetime.strptime(record['date'], '%Y-%m-%d').date()
                        except ValueError:
                            errors.append(f"Invalid date format for employee {record['employee_id']}: {record['date']}")
                            continue
                        
                        # Parse timestamps
                        check_in = None
                        check_out = None
                        
                        if record.get('check_in'):
                            try:
                                check_in = datetime.strptime(record['check_in'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                pass
                        
                        if record.get('check_out'):
                            try:
                                check_out = datetime.strptime(record['check_out'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                pass
                        
                        # Check for existing record
                        existing_record = Attendance.objects.filter(
                            employee=employee,
                            date=date
                        ).first()
                        
                        attendance_data_dict = {
                            'status': record['status'],
                            'check_in': check_in,
                            'check_out': check_out,
                            'late_minutes': record.get('late_minutes', 0),
                            'early_out_minutes': record.get('early_out_minutes', 0),
                            'overtime_minutes': record.get('overtime_minutes', 0),
                            'remarks': record.get('remarks'),
                            'is_manual': True,
                        }
                        
                        if existing_record:
                            # Update existing record
                            for field, value in attendance_data_dict.items():
                                setattr(existing_record, field, value)
                            existing_record.save()
                            updated_count += 1
                        else:
                            # Create new record
                            attendance_data_dict.update({
                                'employee': employee,
                                'date': date,
                            })
                            Attendance.objects.create(**attendance_data_dict)
                            saved_count += 1
                        
                        saved_records.append({
                            'employee_id': record['employee_id'],
                            'employee_name': employee.get_full_name(),
                            'date': record['date'],
                            'status': record['status'],
                        })
                        
                    except Exception as e:
                        error_msg = f"Error saving record for employee {record.get('employee_id', 'unknown')}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue
            
            response = {
                'success': saved_count > 0 or updated_count > 0,
                'saved_count': saved_count,
                'updated_count': updated_count,
                'skipped_count': skipped_count,
                'error_count': len(errors),
                'errors': errors,
                'saved_records': saved_records,
                'message': _("%d records saved, %d updated, %d errors occurred") % (saved_count, updated_count, len(errors))
            }
            
            logger.info(f"Import operation completed: {response['message']}")
            return JsonResponse(response, status=200 if saved_count > 0 or updated_count > 0 else 400)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON data received")
            return JsonResponse({
                'success': False,
                'error': _("Invalid JSON data")
            }, status=400)
        except Exception as e:
            logger.error(f"Error saving attendance data: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
