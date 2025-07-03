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

class OvertimeImportForm(forms.Form):
    """🔥 COMPLETE Enhanced form for overtime import with ALL unified processor options - EXACT field names."""
    
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
    
    # Basic Settings - EXACT field names from UnifiedAttendanceProcessor
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
    
    # 🔥 RULE 1: Minimum Working Hours Rule - EXACT field names
    enable_minimum_working_hours_rule = forms.BooleanField(
        label=_("Enable Minimum Working Hours Rule"),
        required=False,
        initial=False,
    )
    
    minimum_working_hours_threshold = forms.FloatField(
        label=_("Minimum Working Hours Threshold"),
        initial=4.0,
        min_value=1.0,
        max_value=12.0,
        required=False,
    )
    
    # 🔥 RULE 2: Working Hours Half Day Rule - EXACT field names
    enable_working_hours_half_day_rule = forms.BooleanField(
        label=_("Enable Working Hours Half Day Rule"),
        required=False,
        initial=False,
    )
    
    half_day_max_hours = forms.FloatField(
        label=_("Half Day Max Hours"),
        initial=4.0,
        min_value=2.0,
        max_value=6.0,
        required=False,
    )
    
    half_day_min_hours = forms.FloatField(
        label=_("Half Day Min Hours"),
        initial=2.0,
        min_value=1.0,
        max_value=4.0,
        required=False,
    )
    
    # 🔥 RULE 3: Both In-Out Required Rule - EXACT field names
    enable_both_in_out_required_rule = forms.BooleanField(
        label=_("Both Check-In & Check-Out Required"),
        required=False,
        initial=False,
    )
    
    # 🔥 RULE 4: Maximum Working Hours Rule - EXACT field names
    enable_maximum_working_hours_rule = forms.BooleanField(
        label=_("Enable Maximum Working Hours Rule"),
        required=False,
        initial=False,
    )
    
    maximum_working_hours_threshold = forms.FloatField(
        label=_("Maximum Working Hours Threshold"),
        initial=12.0,
        min_value=8.0,
        max_value=24.0,
        required=False,
    )
    
    # 🔥 RULE 5: Dynamic Shift Detection Override Rule - EXACT field names
    enable_dynamic_shift_detection = forms.BooleanField(
        label=_("Enable Dynamic Shift Detection"),
        required=False,
        initial=False,
    )
    
    dynamic_shift_tolerance_minutes = forms.IntegerField(
        label=_("Dynamic Shift Tolerance (Minutes)"),
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
    
    dynamic_shift_fallback_to_default = forms.BooleanField(
        label=_("Dynamic Shift Fallback to Default"),
        required=False,
        initial=True,
    )
    
    # 🔥 RULE 6: Grace Time per Shift Instead of Global - EXACT field names
    use_shift_grace_time = forms.BooleanField(
        label=_("Use Shift Grace Time"),
        required=False,
        initial=False,
    )
    
    # 🔥 RULE 7: Consecutive Absence to Flag as Termination Risk - EXACT field names
    enable_consecutive_absence_flagging = forms.BooleanField(
        label=_("Enable Consecutive Absence Flagging"),
        required=False,
        initial=False,
    )
    
    consecutive_absence_termination_risk_days = forms.IntegerField(
        label=_("Consecutive Absence Termination Risk Days"),
        initial=5,
        min_value=3,
        max_value=30,
        required=False,
    )
    
    # 🔥 RULE 8: Max Early Out Threshold - EXACT field names
    enable_max_early_out_flagging = forms.BooleanField(
        label=_("Enable Max Early Out Flagging"),
        required=False,
        initial=False,
    )
    
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
    
    # 🔥 Enhanced Overtime Configuration - EXACT field names
    overtime_calculation_method = forms.ChoiceField(
        label=_("Overtime Calculation Method"),
        choices=[
            ('shift_based', _('Shift Based')),
            ('hours_based', _('Hours Based')),
            ('attendance_based', _('Based on Attendance Records')),
        ],
        initial='attendance_based',
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
    
    # 🔥 Break Time Configuration - EXACT field names
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
    
    # Advanced Rules - EXACT field names
    late_to_absent_days = forms.IntegerField(
        label=_("Late to Absent Days"),
        initial=3,
        min_value=1,
        max_value=10,
        required=False,
    )
    
    holiday_before_after_absent = forms.BooleanField(
        label=_("Holiday Before/After Absent"),
        required=False,
        initial=True,
    )
    
    weekend_before_after_absent = forms.BooleanField(
        label=_("Weekend Before/After Absent"),
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
    
    # Employee Override Settings - EXACT field names
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
    
    # Weekend Configuration - EXACT field names
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
    
    # 🔥 Overtime Specific Settings - EXACT field names
    require_attendance_record = forms.BooleanField(
        label=_("Require Existing Attendance Record"),
        required=False,
        initial=True,
    )
    
    auto_calculate_from_attendance = forms.BooleanField(
        label=_("Auto Calculate from Attendance"),
        required=False,
        initial=True,
    )
    
    include_holiday_overtime = forms.BooleanField(
        label=_("Include Holiday Overtime"),
        required=False,
        initial=True,
    )
    
    include_weekend_overtime = forms.BooleanField(
        label=_("Include Weekend Overtime"),
        required=False,
        initial=True,
    )
    
    maximum_overtime_hours = forms.FloatField(
        label=_("Maximum Overtime Hours"),
        initial=12.0,
        min_value=1.0,
        max_value=24.0,
    )
    
    overtime_break_minutes = forms.IntegerField(
        label=_("Overtime Break Minutes"),
        initial=0,
        min_value=0,
        max_value=120,
    )

    set_approved_by_default = forms.BooleanField(
        label=_("Set Approved By Default"),
        required=False,
        initial=False,
    )
class OvertimeImportView(LoginRequiredMixin, View):
    """🔥 COMPLETE Overtime import view with ALL unified processor features - EXACT field matching."""
    template_name = 'report/hrm/overtime_import.html'
    
    def get(self, request, *args, **kwargs):
        """Handle GET request - show form."""
        form = OvertimeImportForm()
        
        # Set default date range to current month
        today = timezone.now().date()
        first_day = today.replace(day=1)
        form.fields['start_date'].initial = first_day
        form.fields['end_date'].initial = today
        
        context_data = self.get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        """Handle POST request - generate overtime data for preview."""
        form = OvertimeImportForm(request.POST)
        context_data = self.get_context_data(form)

        if form.is_valid():
            try:
                report_data = self.generate_overtime_data_for_import(form.cleaned_data)
                
                context_data.update({
                    'data_generated': True,
                    'overtime_records': report_data['overtime_records'],
                    'summary_stats': report_data['summary_stats'],
                    'form_data': form.cleaned_data,
                    'total_records': len(report_data['overtime_records']),
                    'start_date': form.cleaned_data['start_date'],
                    'end_date': form.cleaned_data['end_date'],
                })
                
                messages.success(request, _("🔥 COMPLETE Overtime data generated successfully for {} records with ALL unified processor features. Review and import.").format(
                    len(report_data['overtime_records'])))
                
            except Exception as e:
                logger.error(f"Error generating overtime data for import: {str(e)}")
                messages.error(request, _("Failed to generate data: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'shifts': Shift.objects.all().order_by('name'),
            'title': _("🔥 COMPLETE Overtime Import with ALL Enhanced Options"),
            'subtitle': _("Import overtime records with comprehensive processing rules, dynamic shift detection, and all unified processor features - EXACT field matching"),
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
    
    def generate_overtime_data_for_import(self, form_data):
        """🔥 Generate overtime data using COMPLETE unified processor with EXACT field matching."""
        start_date = form_data['start_date']
        end_date = form_data['end_date']
        
        employees = self.get_filtered_employees(form_data)
        
        overtime_records = []
        summary_stats = {
            'total_employees': len(employees),
            'total_records': 0,
            'approved_records': 0,
            'pending_records': 0,
            'rejected_records': 0,
            'existing_records': 0,
            'new_records': 0,
            'total_overtime_hours': 0.0,
            'holiday_overtime_records': 0,
            'weekend_overtime_records': 0,
            'regular_overtime_records': 0,
            'dynamic_shift_detections': 0,
            'roster_day_usage': 0,
            'roster_assignment_usage': 0,
            'default_shift_usage': 0,
            'no_shift_days': 0,
            'flagged_records': 0,
            'converted_records': 0,
            'minimum_hours_rule_applied': 0,
            'half_day_rule_applied': 0,
            'maximum_hours_rule_applied': 0,
            'consecutive_absence_flagged': 0,
            'early_out_flagged': 0,
            'termination_risk_flagged': 0,
        }
        
        # Process employees using COMPLETE unified processor with EXACT field matching
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_employee = {
                executor.submit(self.process_employee_overtime_complete, employee, start_date, end_date, form_data): employee 
                for employee in employees
            }
            
            for future in as_completed(future_to_employee):
                employee = future_to_employee[future]
                try:
                    employee_result = future.result()
                    
                    for overtime_record in employee_result['overtime_records']:
                        overtime_records.append(overtime_record)
                        
                        # Update summary stats with ALL features
                        summary_stats['total_overtime_hours'] += overtime_record['hours']
                        
                        if overtime_record['is_holiday']:
                            summary_stats['holiday_overtime_records'] += 1
                        elif overtime_record['is_weekend']:
                            summary_stats['weekend_overtime_records'] += 1
                        else:
                            summary_stats['regular_overtime_records'] += 1
                        
                        if overtime_record['status'] == 'APP':
                            summary_stats['approved_records'] += 1
                        elif overtime_record['status'] == 'PEN':
                            summary_stats['pending_records'] += 1
                        elif overtime_record['status'] == 'REJ':
                            summary_stats['rejected_records'] += 1
                        
                        if overtime_record['is_duplicate']:
                            summary_stats['existing_records'] += 1
                        
                        if overtime_record.get('dynamic_shift_used', False):
                            summary_stats['dynamic_shift_detections'] += 1
                        
                        if overtime_record.get('flagged', False):
                            summary_stats['flagged_records'] += 1
                        
                        if overtime_record.get('converted', False):
                            summary_stats['converted_records'] += 1
                        
                        # Enhanced rule tracking
                        if overtime_record.get('minimum_hours_rule_applied', False):
                            summary_stats['minimum_hours_rule_applied'] += 1
                        
                        if overtime_record.get('half_day_rule_applied', False):
                            summary_stats['half_day_rule_applied'] += 1
                        
                        if overtime_record.get('maximum_hours_rule_applied', False):
                            summary_stats['maximum_hours_rule_applied'] += 1
                        
                        if overtime_record.get('consecutive_absence_flagged', False):
                            summary_stats['consecutive_absence_flagged'] += 1
                        
                        if overtime_record.get('early_out_flagged', False):
                            summary_stats['early_out_flagged'] += 1
                        
                        if overtime_record.get('termination_risk_flagged', False):
                            summary_stats['termination_risk_flagged'] += 1
                    
                    # Update shift analysis stats
                    shift_analysis = employee_result.get('shift_analysis', {})
                    summary_stats['roster_day_usage'] += shift_analysis.get('roster_day_usage', 0)
                    summary_stats['roster_assignment_usage'] += shift_analysis.get('roster_assignment_usage', 0)
                    summary_stats['default_shift_usage'] += shift_analysis.get('default_shift_usage', 0)
                    summary_stats['no_shift_days'] += shift_analysis.get('no_shift_days', 0)
                        
                except Exception as e:
                    logger.error(f"Error processing employee {employee.employee_id}: {str(e)}")
                    continue
        
        summary_stats['total_records'] = len(overtime_records)
        summary_stats['new_records'] = summary_stats['total_records'] - summary_stats['existing_records']
        
        return {
            'overtime_records': overtime_records,
            'summary_stats': summary_stats,
        }
    
    def process_employee_overtime_complete(self, employee, start_date, end_date, form_data):
        """🔥 Process overtime using COMPLETE unified attendance processor with EXACT field matching."""
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
            
            # Initialize the COMPLETE unified processor with ALL options and EXACT field matching
            processor = UnifiedAttendanceProcessor(form_data)
            
            # Process attendance using unified processor with ALL features
            result = processor.process_employee_attendance(
                employee=employee,
                start_date=start_date,
                end_date=end_date,
                zk_logs=zk_logs,
                holidays=holidays,
                leave_applications=leave_applications,
                roster_data=roster_data
            )
            
            # Convert daily records to overtime records with ALL enhanced features
            overtime_records = []
            for daily_record in result['daily_records']:
                overtime_record = self.convert_daily_record_to_overtime(
                    employee, daily_record, form_data
                )
                if overtime_record:
                    overtime_records.append(overtime_record)
            
            return {
                'overtime_records': overtime_records,
                'shift_analysis': result.get('shift_analysis', {}),
                'summary_stats': result.get('summary_stats', {}),
                'flagged_records': result.get('flagged_records', []),
                'rule_applications': result.get('rule_applications', {}),
            }
            
        except Exception as e:
            logger.error(f"Error processing employee {employee.employee_id}: {str(e)}")
            return {
                'overtime_records': [],
                'shift_analysis': {},
                'summary_stats': {},
                'flagged_records': [],
                'rule_applications': {},
            }
    
    def convert_daily_record_to_overtime(self, employee, daily_record, form_data):
        """Convert daily attendance record to overtime record with ALL enhanced features and EXACT field matching."""
        date = daily_record['date']
        status = 'APP' if form_data.get('set_approved_by_default') else 'PEN'
        
        # Only process records with overtime
        overtime_hours = daily_record.get('overtime_hours', 0.0)
        if overtime_hours < (form_data['minimum_overtime_minutes'] / 60):
            return None
        
        # Check if record already exists
        existing_record = OvertimeRecord.objects.filter(
            employee=employee,
            date=date
        ).first()
        
        is_duplicate = existing_record is not None
        
        # Apply maximum limit
        if overtime_hours > form_data['maximum_overtime_hours']:
            overtime_hours = form_data['maximum_overtime_hours']
        
        # Deduct break time if configured
        if form_data.get('overtime_break_minutes', 0) > 0:
            break_hours = form_data['overtime_break_minutes'] / 60
            overtime_hours = max(0, overtime_hours - break_hours)
        
        if overtime_hours <= 0:
            return None
        
        # Determine start and end times from daily record
        if daily_record.get('in_time') and daily_record.get('out_time'):
            # Calculate overtime period based on shift or expected hours
            if daily_record.get('expected_end'):
                overtime_start = daily_record['expected_end'].time()
            else:
                # Fallback: use expected work hours
                expected_hours = employee.expected_work_hours or 8
                overtime_start_datetime = daily_record['in_time'] + timedelta(hours=expected_hours)
                overtime_start = overtime_start_datetime.time()
            
            overtime_end = daily_record['out_time'].time()
        else:
            # Default times if no attendance times
            overtime_start = datetime.strptime("18:00", "%H:%M").time()
            overtime_end = datetime.strptime("20:00", "%H:%M").time()
        
        # Build comprehensive reason with ALL processor info and EXACT field matching
        reason_parts = []
        
        if daily_record.get('dynamic_shift_used', False):
            confidence = daily_record.get('shift_match_confidence', 0)
            reason_parts.append(f"Dynamic shift detection (confidence: {confidence:.1%})")
        
        if daily_record.get('converted_from_late', False):
            reason_parts.append("Converted from late")
        
        if daily_record.get('minimum_hours_rule_applied', False):
            reason_parts.append("Minimum working hours rule applied")
        
        if daily_record.get('half_day_rule_applied', False):
            reason_parts.append("Half day rule applied")
        
        if daily_record.get('maximum_hours_rule_applied', False):
            reason_parts.append("Maximum working hours rule applied")
        
        if daily_record.get('both_in_out_required_rule_applied', False):
            reason_parts.append("Both in-out required rule applied")
        
        if daily_record.get('consecutive_absence_flagged', False):
            reason_parts.append("Consecutive absence flagged")
        
        if daily_record.get('early_out_flagged', False):
            reason_parts.append("Early out flagged")
        
        if daily_record.get('termination_risk_flagged', False):
            reason_parts.append("Termination risk flagged")
        
        if daily_record.get('excessive_working_hours_flag', False):
            reason_parts.append("Flagged for excessive hours")
        
        if daily_record.get('excessive_early_out_flag', False):
            reason_parts.append("Excessive early out flagged")
        
        # Base reason
        base_reason = f"🔥 COMPLETE Auto-calculated from attendance with ALL unified processor features (Working: {daily_record.get('working_hours', 0):.1f}h, OT: {overtime_hours:.1f}h)"
        
        if reason_parts:
            full_reason = f"{base_reason} | {' | '.join(reason_parts)}"
        else:
            full_reason = base_reason
        
        return {
            'employee_id': employee.employee_id,
            'employee_name': employee.get_full_name(),
            'date': date.strftime('%Y-%m-%d'),
            'start_time': overtime_start.strftime('%H:%M'),
            'end_time': overtime_end.strftime('%H:%M'),
            'hours': round(overtime_hours, 2),
            'reason': full_reason,
            'status': status, 
            'is_duplicate': is_duplicate,
            'is_holiday': daily_record.get('is_holiday', False),
            'is_weekend': daily_record.get('date').weekday() in [int(day) for day in form_data.get('weekend_days', [4])],
            'selected': not is_duplicate,  # Auto-select non-duplicates
            'attendance_id': None,
            'shift_name': daily_record.get('shift_name', 'No Shift'),
            'shift_source': daily_record.get('shift_source', 'None'),
            'dynamic_shift_used': daily_record.get('dynamic_shift_used', False),
            'shift_match_confidence': daily_record.get('shift_match_confidence', 0.0),
            'multiple_shifts_found': daily_record.get('multiple_shifts_found', []),
            'flagged': any([
                daily_record.get('termination_risk_flagged', False),
                daily_record.get('excessive_early_out_flag', False),
                daily_record.get('excessive_working_hours_flag', False),
                daily_record.get('consecutive_absence_flagged', False),
                daily_record.get('early_out_flagged', False),
            ]),
            'converted': any([
                daily_record.get('converted_from_late', False),
                daily_record.get('minimum_hours_rule_applied', False),
                daily_record.get('half_day_rule_applied', False),
                daily_record.get('maximum_hours_rule_applied', False),
                daily_record.get('both_in_out_required_rule_applied', False),
                daily_record.get('converted_to_half_day', False),
                daily_record.get('converted_from_incomplete_punch', False),
            ]),
            'working_hours': daily_record.get('working_hours', 0),
            'late_minutes': daily_record.get('late_minutes', 0),
            'early_out_minutes': daily_record.get('early_out_minutes', 0),
            'break_time_minutes': daily_record.get('break_time_minutes', 0),
            'net_working_hours': daily_record.get('net_working_hours', 0),
            'overtime_break_minutes': daily_record.get('overtime_break_minutes', 0),
            # Enhanced rule tracking with EXACT field names
            'minimum_hours_rule_applied': daily_record.get('minimum_hours_rule_applied', False),
            'half_day_rule_applied': daily_record.get('half_day_rule_applied', False),
            'maximum_hours_rule_applied': daily_record.get('maximum_hours_rule_applied', False),
            'both_in_out_required_rule_applied': daily_record.get('both_in_out_required_rule_applied', False),
            'consecutive_absence_flagged': daily_record.get('consecutive_absence_flagged', False),
            'early_out_flagged': daily_record.get('early_out_flagged', False),
            'termination_risk_flagged': daily_record.get('termination_risk_flagged', False),
        }


@method_decorator(csrf_exempt, name='dispatch')
class OvertimeImportSaveView(View):
    """🔥 COMPLETE Save view for overtime import data with enhanced validation and ALL features."""
    
    def post(self, request, *args, **kwargs):
        """Handle POST request to save selected overtime data with ALL enhanced features."""
        try:
            data = json.loads(request.body)
            overtime_data = data.get('overtime_data', [])
            
            if not overtime_data:
                return JsonResponse({
                    'success': False,
                    'error': _('No overtime data provided')
                }, status=400)
            
            saved_count = 0
            updated_count = 0
            skipped_count = 0
            errors = []
            saved_records = []
            
            # Enhanced statistics tracking
            feature_stats = {
                'dynamic_shift_records': 0,
                'flagged_records': 0,
                'converted_records': 0,
                'minimum_hours_rule_applied': 0,
                'half_day_rule_applied': 0,
                'maximum_hours_rule_applied': 0,
                'consecutive_absence_flagged': 0,
                'early_out_flagged': 0,
                'termination_risk_flagged': 0,
            }
            
            with transaction.atomic():
                for record in overtime_data:
                    try:
                        # Validate required fields
                        required_fields = ['employee_id', 'date', 'start_time', 'end_time', 'hours']
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
                        
                        # Parse times
                        try:
                            start_time = datetime.strptime(record['start_time'], '%H:%M').time()
                            end_time = datetime.strptime(record['end_time'], '%H:%M').time()
                        except ValueError:
                            errors.append(f"Invalid time format for employee {record['employee_id']}")
                            continue
                        
                        # Validate hours
                        try:
                            hours = Decimal(str(record['hours']))
                            if hours <= 0:
                                errors.append(f"Invalid hours for employee {record['employee_id']}: {hours}")
                                continue
                        except (ValueError, TypeError):
                            errors.append(f"Invalid hours format for employee {record['employee_id']}: {record['hours']}")
                            continue
                        
                        # Check for existing record
                        existing_record = OvertimeRecord.objects.filter(
                            employee=employee,
                            date=date
                        ).first()
                        
                        overtime_data_dict = {
                            'start_time': start_time,
                            'end_time': end_time,
                            'hours': hours,
                            'reason': record.get('reason', '🔥 COMPLETE Imported via overtime import with ALL unified processor features'),
                            'status': record.get('status', 'APP'),
                            'remarks': record.get('remarks'),
                        }
                        
                        if existing_record:
                            # Update existing record
                            for field, value in overtime_data_dict.items():
                                setattr(existing_record, field, value)
                            existing_record.save()
                            updated_count += 1
                        else:
                            # Create new record
                            overtime_data_dict.update({
                                'employee': employee,
                                'date': date,
                            })
                            OvertimeRecord.objects.create(**overtime_data_dict)
                            saved_count += 1
                        
                        # Track enhanced features
                        if record.get('dynamic_shift_used', False):
                            feature_stats['dynamic_shift_records'] += 1
                        
                        if record.get('flagged', False):
                            feature_stats['flagged_records'] += 1
                        
                        if record.get('converted', False):
                            feature_stats['converted_records'] += 1
                        
                        if record.get('minimum_hours_rule_applied', False):
                            feature_stats['minimum_hours_rule_applied'] += 1
                        
                        if record.get('half_day_rule_applied', False):
                            feature_stats['half_day_rule_applied'] += 1
                        
                        if record.get('maximum_hours_rule_applied', False):
                            feature_stats['maximum_hours_rule_applied'] += 1
                        
                        if record.get('consecutive_absence_flagged', False):
                            feature_stats['consecutive_absence_flagged'] += 1
                        
                        if record.get('early_out_flagged', False):
                            feature_stats['early_out_flagged'] += 1
                        
                        if record.get('termination_risk_flagged', False):
                            feature_stats['termination_risk_flagged'] += 1
                        
                        saved_records.append({
                            'employee_id': record['employee_id'],
                            'employee_name': employee.get_full_name(),
                            'date': record['date'],
                            'hours': float(hours),
                            'shift_source': record.get('shift_source', 'Unknown'),
                            'dynamic_shift_used': record.get('dynamic_shift_used', False),
                            'flagged': record.get('flagged', False),
                            'converted': record.get('converted', False),
                            'minimum_hours_rule_applied': record.get('minimum_hours_rule_applied', False),
                            'half_day_rule_applied': record.get('half_day_rule_applied', False),
                            'maximum_hours_rule_applied': record.get('maximum_hours_rule_applied', False),
                            'consecutive_absence_flagged': record.get('consecutive_absence_flagged', False),
                            'early_out_flagged': record.get('early_out_flagged', False),
                            'termination_risk_flagged': record.get('termination_risk_flagged', False),
                        })
                        
                    except Exception as e:
                        error_msg = f"Error saving record for employee {record.get('employee_id', 'unknown')}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue
            
            # Build enhanced success message
            success_message = f"🔥 COMPLETE Import completed with ALL features! {saved_count} records saved, {updated_count} updated."
            
            if feature_stats['dynamic_shift_records'] > 0:
                success_message += f" {feature_stats['dynamic_shift_records']} dynamic shifts detected."
            
            if feature_stats['flagged_records'] > 0:
                success_message += f" {feature_stats['flagged_records']} records flagged."
            
            if feature_stats['converted_records'] > 0:
                success_message += f" {feature_stats['converted_records']} records converted."
            
            response = {
                'success': saved_count > 0 or updated_count > 0,
                'saved_count': saved_count,
                'updated_count': updated_count,
                'skipped_count': skipped_count,
                'error_count': len(errors),
                'errors': errors,
                'saved_records': saved_records,
                'feature_stats': feature_stats,
                'message': success_message
            }
            
            logger.info(f"🔥 COMPLETE overtime import operation completed with ALL features: {response['message']}")
            return JsonResponse(response, status=200 if saved_count > 0 or updated_count > 0 else 400)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON data received")
            return JsonResponse({
                'success': False,
                'error': _("Invalid JSON data")
            }, status=400)
        except Exception as e:
            logger.error(f"Error saving overtime data: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
