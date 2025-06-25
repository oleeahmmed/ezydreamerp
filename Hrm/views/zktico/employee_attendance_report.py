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

from Hrm.models import (
    ZKAttendanceLog, Employee, Holiday, LeaveApplication, 
    RosterDay, RosterAssignment, Shift, ShortLeaveApplication, Roster,
    OvertimeRecord
)

logger = logging.getLogger(__name__)

class AttendanceReportConfig:
    """
    উপস্থিতি রিপোর্ট কনফিগারেশন ক্লাস
    সব কাস্টমাইজেশন অপশন এখানে
    """
    
    def __init__(self, **custom_config):
        # ডিফল্ট কনফিগারেশন
        self.config = {
            # === সময় সংক্রান্ত সেটিংস ===
            'time_settings': {
                'default_grace_minutes': 15,           # ডিফল্ট গ্রেস টাইম (মিনিট)
                'overtime_grace_minutes': 15,          # ওভারটাইম গ্রেস টাইম (মিনিট)
                'break_time_minutes': 60,              # বিরতির সময় (মিনিট)
                'half_day_threshold_percent': 50,      # অর্ধদিনের শতকরা হার
                'minimum_work_hours': 1,               # ন্যূনতম কাজের ঘন্টা
                'maximum_daily_hours': 12,             # সর্বোচ্চ দৈনিক ঘন্টা
                'expected_work_hours': 8,              # প্রত্যাশিত কাজের ঘন্টা
            },
            
            # === স্ট্যাটাস নিয়ম ===
            'status_rules': {
                'late_to_absent_threshold': 3,         # কত দিন দেরি = ১ দিন অনুপস্থিত
                'consecutive_absent_limit': 7,         # ধারাবাহিক অনুপস্থিতির সীমা
                'monthly_absent_limit': 5,             # মাসিক অনুপস্থিতির সীমা
                'apply_weekend_rule': True,            # সাপ্তাহান্তের নিয়ম প্রয়োগ
                'weekend_absent_as_absent': True,      # সাপ্তাহান্তে অনুপস্থিত = অনুপস্থিত
            },
            
            # === ছুটির নিয়ম ===
            'holiday_rules': {
                'holiday_between_absent_as_absent': True,  # ছুটির দিনের মাঝে অনুপস্থিত = অনুপস্থিত
                'public_holiday_priority': True,           # সরকারি ছুটির অগ্রাধিকার
                'weekly_holiday_override': False,          # সাপ্তাহিক ছুটি ওভাররাইড
            },
            
            # === ওভারটাইম নিয়ম ===
            'overtime_rules': {
                'max_daily_overtime': 12,               # দৈনিক সর্বোচ্চ ওভারটাইম (ঘন্টা)
                'max_weekly_overtime': 20,             # সাপ্তাহিক সর্বোচ্চ ওভারটাইম (ঘন্টা)
                'max_monthly_overtime': 80,            # মাসিক সর্বোচ্চ ওভারটাইম (ঘন্টা)
                'overtime_multiplier': 1.5,            # ওভারটাইম গুণক
                'weekend_overtime_multiplier': 2.0,    # সাপ্তাহান্তে ওভারটাইম গুণক
                'holiday_overtime_multiplier': 2.5,    # ছুটির দিনে ওভারটাইম গুণক
                'auto_approve_overtime': False,        # স্বয়ংক্রিয় ওভারটাইম অনুমোদন
            },
            
            # === ব্যবসায়িক নিয়ম ===
            'business_rules': {
                'enable_roster_priority': True,        # রোস্টার অগ্রাধিকার সক্রিয়
                'enable_shift_flexibility': True,      # শিফট নমনীয়তা সক্রিয়
                'enable_late_conversion': True,        # দেরি রূপান্তর সক্রিয়
                'enable_holiday_conversion': True,     # ছুটি রূপান্তর সক্রিয়
                'enable_consecutive_tracking': True,   # ধারাবাহিক ট্র্যাকিং সক্রিয়
                'enable_weekly_analysis': True,        # সাপ্তাহিক বিশ্লেষণ সক্রিয়
            },
            
            # === গণনার নিয়ম ===
            'calculation_rules': {
                'round_to_nearest_minute': True,       # নিকটতম মিনিটে রাউন্ড
                'consider_partial_hours': True,        # আংশিক ঘন্টা বিবেচনা
                'deduct_break_automatically': True,    # স্বয়ংক্রিয় বিরতি কাটা
                'include_travel_time': False,          # ভ্রমণের সময় অন্তর্ভুক্ত
                'use_shift_break_time': True,          # শিফটের বিরতি সময় ব্যবহার
            },
            
            # === রিপোর্ট সেটিংস ===
            'report_settings': {
                'enable_summary': True,                # সারসংক্ষেপ সক্রিয়
                'enable_overtime_import': True,        # ওভারটাইম ইমপোর্ট সক্রিয়
                'enable_export': True,                 # এক্সপোর্ট সক্রিয়
                'enable_caching': True,                # ক্যাশিং সক্রিয়
                'cache_duration_minutes': 60,          # ক্যাশ সময়কাল (মিনিট)
                'max_date_range_days': 365,            # সর্বোচ্চ তারিখ পরিসীমা (দিন)
            },
            
            # === কাস্টম সেটিংস ===
            'custom_settings': {
                'ramadan_adjustment': False,           # রমজান সমন্বয়
                'winter_adjustment': False,            # শীতকালীন সমন্বয়
                'probation_different_rule': False,     # প্রবেশনারি ভিন্ন নিয়ম
                'senior_staff_flexibility': False,     # সিনিয়র স্টাফ নমনীয়তা
                'department_specific_rules': False,    # বিভাগ নির্দিষ্ট নিয়ম
            }
        }
        
        # কাস্টম কনফিগারেশন আপডেট
        self._update_config(custom_config)
    
    def _update_config(self, custom_config):
        """কাস্টম কনফিগারেশন দিয়ে ডিফল্ট আপডেট করা"""
        for category, settings in custom_config.items():
            if category in self.config:
                if isinstance(settings, dict):
                    self.config[category].update(settings)
                else:
                    self.config[category] = settings
            else:
                self.config[category] = settings
    
    def get(self, category, key, default=None):
        """নির্দিষ্ট কনফিগারেশন মান পেতে"""
        return self.config.get(category, {}).get(key, default)
    
    def set(self, category, key, value):
        """কনফিগারেশন মান সেট করা"""
        if category not in self.config:
            self.config[category] = {}
        self.config[category][key] = value
    
    def is_enabled(self, category, key):
        """কোন ফিচার সক্রিয় কিনা চেক করা"""
        return self.get(category, key, False)
    
    def get_all_config(self):
        """সব কনফিগারেশন পেতে"""
        return self.config
    
    def export_config(self):
        """কনফিগারেশন JSON ফরম্যাটে এক্সপোর্ট"""
        return json.dumps(self.config, indent=2, ensure_ascii=False)
    
    def import_config(self, json_string):
        """JSON থেকে কনফিগারেশন ইমপোর্ট"""
        try:
            imported_config = json.loads(json_string)
            self._update_config(imported_config)
            return True
        except Exception as e:
            logger.error(f"কনফিগারেশন ইমপোর্টে ত্রুটি: {str(e)}")
            return False

class EmployeeAttendanceReportForm(forms.Form):
    """Form for generating employee attendance report with configuration options."""
    WEEKLY_HOLIDAY_CHOICES = [
        ('FRIDAY', _('Friday')),
        ('SATURDAY', _('Saturday')),
        ('SUNDAY', _('Sunday')),
        ('NONE', _('No Weekly Holiday')),
    ]

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
    weekly_holiday = forms.ChoiceField(
        label=_("Weekly Holiday"),
        choices=WEEKLY_HOLIDAY_CHOICES,
        initial='FRIDAY',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Select the weekly holiday.")
    )
    late_absent_threshold = forms.IntegerField(
        label=_("Late to Absent Conversion"),
        initial=3,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '3',
            'min': '1',
            'max': '10'
        }),
        help_text=_("Number of late days that convert to 1 absent day")
    )
    include_summary = forms.BooleanField(
        label=_("Include Summary"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include attendance summary statistics.")
    )
    
    # === কনফিগারেশন অপশন ===
    grace_minutes = forms.IntegerField(
        label=_("Grace Time (Minutes)"),
        initial=15,
        min_value=0,
        max_value=60,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '15'
        }),
        help_text=_("Grace time for late arrival in minutes.")
    )
    
    overtime_grace_minutes = forms.IntegerField(
        label=_("Overtime Grace (Minutes)"),
        initial=15,
        min_value=0,
        max_value=60,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '15'
        }),
        help_text=_("Grace time for overtime calculation in minutes.")
    )
    
    enable_holiday_conversion = forms.BooleanField(
        label=_("Holiday Conversion Rule"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Convert holidays between absences to absent.")
    )
    
    max_daily_overtime = forms.FloatField(
        label=_("Max Daily Overtime (Hours)"),
        initial=4.0,
        min_value=0,
        max_value=12,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '4.0',
            'step': '0.5'
        }),
        help_text=_("Maximum overtime hours per day.")
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        employee_id = cleaned_data.get('employee_id')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_("Start date cannot be after end date."))

        if employee_id:
            try:
                Employee.objects.get(employee_id=employee_id)
            except Employee.DoesNotExist:
                raise forms.ValidationError(_("Employee ID does not exist."))

        return cleaned_data

class EmployeeDetailedAttendanceReportView(LoginRequiredMixin, View):
    """Advanced view to generate a detailed attendance report with configuration options."""
    template_name = 'report/hrm/employee_detailed_attendance_report.html'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ডিফল্ট কনফিগারেশন ইনিশিয়ালাইজ
        self.config = AttendanceReportConfig()

    def get(self, request, *args, **kwargs):
        form = EmployeeAttendanceReportForm()
        employees = Employee.objects.filter(is_active=True).values('employee_id', 'first_name', 'last_name')
        
        return render(request, self.template_name, {
            'form': form,
            'employees': employees,
            'report_generated': False,
            'page_title': _("Employee Attendance Report"),
            'config_options': self.config.get_all_config(),
        })

    def post(self, request, *args, **kwargs):
        # Handle AJAX overtime import request
        if request.headers.get('Content-Type') == 'application/json':
            return self._handle_overtime_import(request)
        
        form = EmployeeAttendanceReportForm(request.POST)
        employees = Employee.objects.filter(is_active=True).values('employee_id', 'first_name', 'last_name')
        
        context = {
            'form': form,
            'employees': employees,
            'report_generated': False,
            'page_title': _("Employee Attendance Report"),
            'config_options': self.config.get_all_config(),
        }

        if form.is_valid():
            # ফর্ম থেকে কনফিগারেশন আপডেট
            self._update_config_from_form(form.cleaned_data)
            
            employee_id = form.cleaned_data['employee_id']
            start_date = form.cleaned_data['start_date'] or (timezone.now().date() - timedelta(days=30))
            end_date = form.cleaned_data['end_date'] or timezone.now().date()
            weekly_holiday = form.cleaned_data['weekly_holiday']
            late_absent_threshold = form.cleaned_data['late_absent_threshold']
            include_summary = form.cleaned_data['include_summary']

            try:
                employee = Employee.objects.select_related(
                    'default_shift', 'department', 'designation'
                ).get(employee_id=employee_id)
                
                report_data = self._generate_advanced_report(
                    employee, start_date, end_date, weekly_holiday, late_absent_threshold
                )
                summary_data = self._generate_summary(report_data, employee, late_absent_threshold) if include_summary else None
                
                context.update({
                    'report_generated': True,
                    'employee': employee,
                    'attendance_data': report_data,
                    'summary_data': summary_data,
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_days': (end_date - start_date).days + 1,
                    'late_absent_threshold': late_absent_threshold,
                    'applied_config': self.config.get_all_config(),
                })
                messages.success(request, _("Report generated for {} with custom configuration.").format(employee.get_full_name()))
            except Employee.DoesNotExist:
                messages.error(request, _("Employee with ID {} not found.").format(employee_id))
            except Exception as e:
                logger.error(f"Error generating report for {employee_id}: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context)
    
    def _update_config_from_form(self, form_data):
        """ফর্ম ডেটা থেকে কনফিগারেশন আপডেট করা"""
        # সময় সেটিংস আপডেট
        if form_data.get('grace_minutes') is not None:
            self.config.set('time_settings', 'default_grace_minutes', form_data['grace_minutes'])
        
        if form_data.get('overtime_grace_minutes') is not None:
            self.config.set('time_settings', 'overtime_grace_minutes', form_data['overtime_grace_minutes'])
        
        # ব্যবসায়িক নিয়ম আপডেট
        if form_data.get('enable_holiday_conversion') is not None:
            self.config.set('business_rules', 'enable_holiday_conversion', form_data['enable_holiday_conversion'])
        
        # ওভারটাইম নিয়ম আপডেট
        if form_data.get('max_daily_overtime') is not None:
            self.config.set('overtime_rules', 'max_daily_overtime', form_data['max_daily_overtime'])
        
        # স্ট্যাটাস নিয়ম আপডেট
        self.config.set('status_rules', 'late_to_absent_threshold', form_data['late_absent_threshold'])

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
        """Import overtime records from attendance data with configuration."""
        if not self.config.is_enabled('report_settings', 'enable_overtime_import'):
            return JsonResponse({
                'success': False,
                'message': 'Overtime import is disabled in configuration'
            })
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        duplicate_details = []
        
        max_daily_overtime = self.config.get('overtime_rules', 'max_daily_overtime', 4)
        auto_approve = self.config.get('overtime_rules', 'auto_approve_overtime', False)
        
        try:
            with transaction.atomic():
                for record_data in overtime_records:
                    try:
                        employee = Employee.objects.get(employee_id=record_data['employee_id'])
                        date = datetime.strptime(record_data['date'], '%Y-%m-%d').date()
                        overtime_hours = float(record_data['overtime_hours'])
                        
                        # কনফিগারেশন অনুযায়ী ওভারটাইম সীমা প্রয়োগ
                        if overtime_hours > max_daily_overtime:
                            overtime_hours = max_daily_overtime
                        
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
                        
                        # Calculate start and end times based on shift and overtime
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
                        
                        # Create overtime record with configuration
                        OvertimeRecord.objects.create(
                            employee=employee,
                            date=date,
                            start_time=start_time,
                            end_time=end_time,
                            hours=overtime_hours,
                            reason=f"Imported from attendance report - {record_data.get('reason', 'Overtime work')}",
                            status='APP' if auto_approve else 'PEN',
                            remarks=f"Auto-imported with config on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
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
        
        message = f'Overtime import completed with configuration. Imported: {imported_count}, Skipped: {skipped_count}, Errors: {error_count}'
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
            'duplicates': duplicate_details,
            'config_applied': {
                'max_daily_overtime': max_daily_overtime,
                'auto_approve': auto_approve
            }
        })

    def _generate_advanced_report(self, employee, start_date, end_date, weekly_holiday, late_absent_threshold):
        """Generate comprehensive attendance report with configuration-based logic."""
        
        # Fetch all necessary data with optimized queries
        attendance_logs = self._get_optimized_attendance_logs(employee, start_date, end_date)
        holidays = self._get_holidays(start_date, end_date)
        leaves = self._get_leaves(employee, start_date, end_date)
        short_leaves = self._get_short_leaves(employee, start_date, end_date)
        roster_days = self._get_roster_days(employee, start_date, end_date)
        roster_assignments = self._get_roster_assignments(employee, start_date, end_date)

        # Organize data by date for efficient lookup
        log_dict = self._organize_logs_by_date(attendance_logs)
        holiday_dict = {h.date: h.name for h in holidays}
        leave_dict = self._organize_leaves_by_date(leaves)
        short_leave_dict = self._organize_short_leaves_by_date(short_leaves)
        roster_day_dict = {rd.date: rd for rd in roster_days}
        roster_assignment_dict = self._organize_roster_assignments_by_date(roster_assignments)

        # Generate daily attendance records
        report_data = []
        current_date = start_date

        while current_date <= end_date:
            daily_record = self._process_advanced_daily_attendance(
                current_date, employee, log_dict, holiday_dict, 
                leave_dict, short_leave_dict, roster_day_dict, 
                roster_assignment_dict, weekly_holiday
            )
            report_data.append(daily_record)
            current_date += timedelta(days=1)

        # Apply business rules based on configuration
        if self.config.is_enabled('business_rules', 'enable_holiday_conversion'):
            self._apply_holiday_absence_rule(report_data)
        
        if self.config.is_enabled('business_rules', 'enable_late_conversion'):
            self._apply_late_to_absent_conversion(report_data, late_absent_threshold)
        
        if self.config.is_enabled('business_rules', 'enable_consecutive_tracking'):
            self._apply_advanced_business_rules(report_data, employee)

        return report_data

    # [Keep all your existing helper methods but modify them to use self.config]
    
    def _get_optimized_attendance_logs(self, employee, start_date, end_date):
        """Get ZK attendance logs with optimized query."""
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

    def _get_short_leaves(self, employee, start_date, end_date):
        """Get approved short leaves for the employee."""
        return ShortLeaveApplication.objects.filter(
            employee=employee,
            status='APP',
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

    def _get_roster_days(self, employee, start_date, end_date):
        """Get specific roster days for the employee with optimized query."""
        return RosterDay.objects.filter(
            roster_assignment__employee=employee,
            date__gte=start_date,
            date__lte=end_date
        ).select_related(
            'shift', 'roster_assignment__roster', 'roster_assignment__shift'
        ).order_by('date')

    def _get_roster_assignments(self, employee, start_date, end_date):
        """Get roster assignments for the employee that overlap with the date range."""
        return RosterAssignment.objects.filter(
            employee=employee,
            roster__start_date__lte=end_date,
            roster__end_date__gte=start_date
        ).select_related('roster', 'shift', 'employee').order_by('roster__start_date')

    def _organize_logs_by_date(self, logs):
        """Organize attendance logs by date with first and last time tracking."""
        log_dict = {}
        for log in logs:
            date = log.timestamp.date()
            if date not in log_dict:
                log_dict[date] = []
            log_dict[date].append(log)
        
        # Sort logs by timestamp for each date
        for date in log_dict:
            log_dict[date] = sorted(log_dict[date], key=lambda x: x.timestamp)
        
        return log_dict

    def _organize_leaves_by_date(self, leaves):
        """Organize leaves by date range."""
        leave_dict = {}
        for leave in leaves:
            current_date = leave.start_date
            while current_date <= leave.end_date:
                leave_dict[current_date] = leave
                current_date += timedelta(days=1)
        return leave_dict

    def _organize_short_leaves_by_date(self, short_leaves):
        """Organize short leaves by date."""
        return {sl.date: sl for sl in short_leaves}

    def _organize_roster_assignments_by_date(self, roster_assignments):
        """Organize roster assignments by date range."""
        assignment_dict = {}
        for assignment in roster_assignments:
            current_date = assignment.roster.start_date
            while current_date <= assignment.roster.end_date:
                assignment_dict[current_date] = assignment
                current_date += timedelta(days=1)
        return assignment_dict

    def _get_advanced_shift_info_for_date(self, date, employee, roster_day_dict, roster_assignment_dict):
        """Advanced shift logic with configuration-based priority."""
        
        if not self.config.is_enabled('business_rules', 'enable_roster_priority'):
            # যদি রোস্টার অগ্রাধিকার নিষ্ক্রিয় থাকে, শুধু ডিফল্ট শিফট ব্যবহার করুন
            if employee.default_shift:
                return {
                    'shift': employee.default_shift,
                    'shift_source': 'Default',
                    'start_time': employee.default_shift.start_time,
                    'end_time': employee.default_shift.end_time,
                    'is_roster_time': False,
                    'roster_info': "Employee Default Shift (Roster Priority Disabled)",
                }
        
        # Priority 1: Check RosterDay for specific date
        if date in roster_day_dict:
            roster_day = roster_day_dict[date]
            if roster_day.shift:
                return {
                    'shift': roster_day.shift,
                    'shift_source': 'RosterDay',
                    'start_time': roster_day.shift.start_time,
                    'end_time': roster_day.shift.end_time,
                    'is_roster_time': True,
                    'roster_info': f"Roster Day: {roster_day.roster_assignment.roster.name}",
                }
        
        # Priority 2: Check RosterAssignment for date range
        if date in roster_assignment_dict:
            roster_assignment = roster_assignment_dict[date]
            
            if roster_assignment.shift:
                return {
                    'shift': roster_assignment.shift,
                    'shift_source': 'RosterAssignment',
                    'start_time': roster_assignment.shift.start_time,
                    'end_time': roster_assignment.shift.end_time,
                    'is_roster_time': True,
                    'roster_info': f"Roster Assignment: {roster_assignment.roster.name}",
                }
            elif employee.default_shift:
                return {
                    'shift': employee.default_shift,
                    'shift_source': 'RosterAssignment',
                    'start_time': employee.default_shift.start_time,
                    'end_time': employee.default_shift.end_time,
                    'is_roster_time': False,
                    'roster_info': f"Roster Assignment (Default Shift): {roster_assignment.roster.name}",
                }
        
        # Priority 3: Use employee's default shift
        if employee.default_shift:
            return {
                'shift': employee.default_shift,
                'shift_source': 'Default',
                'start_time': employee.default_shift.start_time,
                'end_time': employee.default_shift.end_time,
                'is_roster_time': False,
                'roster_info': "Employee Default Shift",
            }
        
        # No shift found
        return {
            'shift': None,
            'shift_source': 'None',
            'start_time': None,
            'end_time': None,
            'is_roster_time': False,
            'roster_info': "No Shift Assigned",
        }

    def _process_advanced_daily_attendance(self, date, employee, log_dict, holiday_dict, 
                                         leave_dict, short_leave_dict, roster_day_dict, 
                                         roster_assignment_dict, weekly_holiday):
        """Process attendance for a single day with configuration-based logic."""
        
        # Initialize daily record with configuration defaults
        expected_hours = self.config.get('time_settings', 'expected_work_hours', 8)
        overtime_grace = self.config.get('time_settings', 'overtime_grace_minutes', 15)
        
        record = {
            'date': date,
            'day_name': date.strftime('%A'),
            'status': 'ABS',
            'original_status': 'ABS',
            'in_time': None,
            'out_time': None,
            'working_hours': 0.0,
            'late_minutes': 0,
            'early_out_minutes': 0,
            'overtime_hours': 0.0,
            'shift': None,
            'shift_source': 'None',
            'is_roster_day': False,
            'is_holiday': False,
            'is_leave': False,
            'is_short_leave': False,
            'holiday_name': None,
            'expected_hours': expected_hours,
            'overtime_grace_minutes': overtime_grace,
            'converted_from_late': False,
        }

        # Check public holidays first (highest priority)
        if date in holiday_dict and self.config.get('holiday_rules', 'public_holiday_priority', True):
            record['status'] = 'HOL'
            record['original_status'] = 'HOL'
            record['is_holiday'] = True
            record['holiday_name'] = f"Public Holiday: {holiday_dict[date]}"

        # Check leaves (don't override public holidays)
        if date in leave_dict and record['status'] not in ['HOL']:
            leave = leave_dict[date]
            record['status'] = 'LEA'
            record['original_status'] = 'LEA'
            record['is_leave'] = True
            record['leave_type'] = leave.leave_type.name

        # Check short leaves
        if date in short_leave_dict and record['status'] not in ['HOL', 'LEA']:
            short_leave = short_leave_dict[date]
            record['is_short_leave'] = True
            record['short_leave_duration'] = short_leave.duration_hours

        # Get advanced shift information with configuration
        shift_info = self._get_advanced_shift_info_for_date(date, employee, roster_day_dict, roster_assignment_dict)
        record.update({
            'shift': shift_info['shift'],
            'shift_source': shift_info['shift_source'],
            'shift_start_time': shift_info['start_time'],
            'shift_end_time': shift_info['end_time'],
            'is_roster_time': shift_info['is_roster_time'],
            'roster_info': shift_info['roster_info'],
        })
        
        # Mark as roster day if shift comes from roster
        if shift_info['shift_source'] in ['RosterDay', 'RosterAssignment']:
            record['is_roster_day'] = True

        # Check weekly holiday with configuration
        if self.config.get('status_rules', 'apply_weekend_rule', True):
            weekday = date.weekday()
            is_weekly_holiday = self._is_weekly_holiday(weekday, weekly_holiday)
            
            if is_weekly_holiday and record['status'] == 'ABS':
                if not self.config.get('holiday_rules', 'weekly_holiday_override', False) or record['status'] != 'HOL':
                    record['status'] = 'HOL'
                    record['original_status'] = 'HOL'
                    record['is_holiday'] = True
                    record['holiday_name'] = f'{weekly_holiday.title()} (Weekly Holiday)'

        # Process attendance logs if not on holiday or leave
        if record['status'] not in ['HOL', 'LEA'] and date in log_dict:
            self._process_advanced_attendance_logs(record, log_dict[date], employee)

        # Finalize record
        record['shift_name'] = record['shift'].name if record['shift'] else 'No Shift Assigned'

        return record

    def _is_weekly_holiday(self, weekday, weekly_holiday):
        """Check if the day is a weekly holiday."""
        holiday_map = {
            'FRIDAY': 4,    # Friday
            'SATURDAY': 5,  # Saturday
            'SUNDAY': 6,    # Sunday
        }
        return weekly_holiday in holiday_map and weekday == holiday_map[weekly_holiday]

    def _process_advanced_attendance_logs(self, record, day_logs, employee):
        """Process attendance logs with configuration-based logic."""
        if not day_logs:
            return

        sorted_logs = sorted(day_logs, key=lambda x: x.timestamp)
        first_log = sorted_logs[0]
        last_log = sorted_logs[-1]

        record['in_time'] = first_log.timestamp
        record['total_logs'] = len(sorted_logs)
        
        if len(sorted_logs) > 1:
            record['out_time'] = last_log.timestamp
        else:
            record['out_time'] = None

        # Calculate metrics using configuration
        if record['shift'] and self.config.is_enabled('business_rules', 'enable_shift_flexibility'):
            self._calculate_advanced_attendance_metrics(record, employee)
        else:
            # Basic calculation without shift
            record['status'] = 'PRE'
            record['original_status'] = 'PRE'
            if record['out_time']:
                duration = record['out_time'] - record['in_time']
                working_hours = duration.total_seconds() / 3600
                
                # Apply break time from configuration
                if self.config.get('calculation_rules', 'deduct_break_automatically', True):
                    break_hours = self.config.get('time_settings', 'break_time_minutes', 60) / 60
                    working_hours = max(0, working_hours - break_hours)
                
                record['working_hours'] = round(working_hours, 2)

    def _calculate_advanced_attendance_metrics(self, record, employee):
        """Calculate attendance metrics using configuration."""
        shift = record['shift']
        date = record['date']
        in_time = record['in_time']
        out_time = record['out_time']

        shift_start_time = record['shift_start_time']
        shift_end_time = record['shift_end_time']

        if not shift_start_time or not shift_end_time:
            record['status'] = 'PRE'
            record['original_status'] = 'PRE'
            return

        # Create expected shift datetime objects
        expected_start = timezone.datetime.combine(date, shift_start_time)
        expected_start = timezone.make_aware(expected_start, timezone.get_default_timezone())
        
        expected_end = timezone.datetime.combine(date, shift_end_time)
        expected_end = timezone.make_aware(expected_end, timezone.get_default_timezone())

        # Handle overnight shifts
        if shift_end_time < shift_start_time:
            expected_end += timedelta(days=1)

        # Get grace time from configuration
        grace_minutes = self.config.get('time_settings', 'default_grace_minutes', 15)
        late_threshold = expected_start + timedelta(minutes=grace_minutes)

        # Check for late arrival
        if in_time > late_threshold:
            late_duration = in_time - expected_start
            record['late_minutes'] = round(late_duration.total_seconds() / 60)
            record['status'] = 'LAT'
            record['original_status'] = 'LAT'
        else:
            record['status'] = 'PRE'
            record['original_status'] = 'PRE'

        # Calculate working hours with configuration
        if out_time:
            total_duration = out_time - in_time
            total_hours = total_duration.total_seconds() / 3600
            
            # Apply break time based on configuration
            if self.config.get('calculation_rules', 'use_shift_break_time', True):
                break_hours = (getattr(shift, 'break_time', 60) or 60) / 60
            else:
                break_hours = self.config.get('time_settings', 'break_time_minutes', 60) / 60
            
            working_hours = total_hours - break_hours
            record['working_hours'] = max(0, round(working_hours, 2))
        else:
            record['working_hours'] = 0

        # Check for early departure
        if out_time and out_time < expected_end:
            early_duration = expected_end - out_time
            record['early_out_minutes'] = round(early_duration.total_seconds() / 60)

        # Calculate overtime using configuration
        if out_time:
            overtime_grace = self.config.get('time_settings', 'overtime_grace_minutes', 15)
            overtime_threshold = expected_end + timedelta(minutes=overtime_grace)
            
            if out_time > overtime_threshold:
                overtime_duration = out_time - overtime_threshold
                overtime_hours = overtime_duration.total_seconds() / 3600
                
                # Apply maximum daily overtime from configuration
                max_daily_overtime = self.config.get('overtime_rules', 'max_daily_overtime', 4)
                record['overtime_hours'] = min(round(overtime_hours, 2), max_daily_overtime)

        # Determine final status based on configuration
        expected_hours = self.config.get('time_settings', 'expected_work_hours', 8)
        half_day_threshold_percent = self.config.get('time_settings', 'half_day_threshold_percent', 50)
        half_day_threshold = expected_hours * (half_day_threshold_percent / 100)
        
        if record['working_hours'] > 0:
            if record['working_hours'] < half_day_threshold:
                record['status'] = 'HAL'
                if record['original_status'] not in ['HAL']:
                    record['original_status'] = 'HAL'

        # Handle short leave impact
        if record.get('is_short_leave'):
            short_leave_hours = record.get('short_leave_duration', 0)
            record['working_hours'] = max(0, record['working_hours'] - short_leave_hours)

    def _apply_late_to_absent_conversion(self, report_data, late_absent_threshold):
        """Apply late-to-absent conversion rule with configuration."""
        if not self.config.is_enabled('business_rules', 'enable_late_conversion'):
            return
        
        # Use configuration threshold if available
        threshold = self.config.get('status_rules', 'late_to_absent_threshold', late_absent_threshold)
        
        late_count = 0
        converted_absents = 0
        
        for record in report_data:
            if record['original_status'] == 'LAT':
                late_count += 1
                
                if late_count >= threshold:
                    record['status'] = 'ABS'
                    record['converted_from_late'] = True
                    converted_absents += 1
                    late_count = 0
            
            record['late_count_running'] = late_count
            record['converted_absents_total'] = converted_absents

    def _apply_holiday_absence_rule(self, report_data):
        """Apply holiday absence rule with configuration."""
        if not self.config.get('holiday_rules', 'holiday_between_absent_as_absent', True):
            return
        
        for i in range(len(report_data)):
            record = report_data[i]
            
            if record['status'] == 'HOL' and record['is_holiday']:
                prev_day_absent = False
                if i > 0:
                    prev_record = report_data[i - 1]
                    prev_day_absent = prev_record['status'] == 'ABS'
                
                next_day_absent = False
                if i < len(report_data) - 1:
                    next_record = report_data[i + 1]
                    next_day_absent = next_record['status'] == 'ABS'
                
                if prev_day_absent and next_day_absent:
                    record['status'] = 'ABS'
                    record['is_holiday'] = False
                    record['holiday_name'] = None
                    record['conversion_reason'] = 'Holiday between absences converted to absent'

    def _apply_advanced_business_rules(self, report_data, employee):
        """Apply additional business rules based on configuration."""
        
        # Rule 1: Consecutive absences tracking
        if self.config.is_enabled('business_rules', 'enable_consecutive_tracking'):
            consecutive_absences = 0
            consecutive_limit = self.config.get('status_rules', 'consecutive_absent_limit', 7)
            
            for record in report_data:
                if record['status'] == 'ABS':
                    consecutive_absences += 1
                    record['consecutive_absences'] = consecutive_absences
                    
                    if consecutive_absences > consecutive_limit:
                        record['consecutive_violation'] = f'Exceeds consecutive limit ({consecutive_limit} days)'
                else:
                    consecutive_absences = 0
                    record['consecutive_absences'] = 0

        # Rule 2: Weekly attendance pattern analysis
        if self.config.is_enabled('business_rules', 'enable_weekly_analysis'):
            self._analyze_weekly_patterns(report_data)

        # Rule 3: Overtime validation with configuration
        self._validate_overtime_rules(report_data, employee)

    def _analyze_weekly_patterns(self, report_data):
        """Analyze weekly attendance patterns with configuration."""
        for i, record in enumerate(report_data):
            week_start = i // 7 * 7
            week_end = min(week_start + 7, len(report_data))
            week_data = report_data[week_start:week_end]
            
            week_present = sum(1 for r in week_data if r['status'] in ['PRE', 'LAT'])
            week_absent = sum(1 for r in week_data if r['status'] == 'ABS')
            
            record['week_present_days'] = week_present
            record['week_absent_days'] = week_absent

    def _validate_overtime_rules(self, report_data, employee):
        """Validate overtime according to configuration rules."""
        max_daily_overtime = self.config.get('overtime_rules', 'max_daily_overtime', 4)
        max_weekly_overtime = self.config.get('overtime_rules', 'max_weekly_overtime', 20)
        
        weekly_overtime = 0
        for i, record in enumerate(report_data):
            # Daily overtime validation
            if record['overtime_hours'] > max_daily_overtime:
                record['overtime_violation'] = f"Exceeds daily limit ({max_daily_overtime}h)"
                record['overtime_hours'] = max_daily_overtime
            
            # Weekly overtime tracking
            if i % 7 == 0:
                weekly_overtime = 0
            
            weekly_overtime += record['overtime_hours']
            
            if weekly_overtime > max_weekly_overtime:
                excess = weekly_overtime - max_weekly_overtime
                record['overtime_hours'] = max(0, record['overtime_hours'] - excess)
                record['overtime_violation'] = f"Exceeds weekly limit ({max_weekly_overtime}h)"

    def _generate_summary(self, report_data, employee, late_absent_threshold):
        """Generate comprehensive attendance summary with configuration."""
        summary = {
            'total_days': len(report_data),
            'present_days': 0,
            'absent_days': 0,
            'late_days': 0,
            'leave_days': 0,
            'holiday_days': 0,
            'half_days': 0,
            'total_working_hours': 0.0,
            'total_late_minutes': 0,
            'total_overtime_hours': 0.0,
            'attendance_percentage': 0.0,
            'expected_total_hours': 0.0,
            'average_daily_hours': 0.0,
            'punctuality_percentage': 0.0,
            'max_consecutive_absences': 0,
            'total_roster_days': 0,
            'overtime_days': 0,
            'late_absent_threshold': self.config.get('status_rules', 'late_to_absent_threshold', late_absent_threshold),
            'converted_absents': 0,
            'original_late_days': 0,
            'config_applied': self.config.get_all_config(),
        }

        expected_daily_hours = self.config.get('time_settings', 'expected_work_hours', 8)
        max_consecutive = 0
        current_consecutive = 0

        for record in report_data:
            status = record['status']
            original_status = record.get('original_status', status)
            
            if original_status == 'LAT':
                summary['original_late_days'] += 1
            
            if record.get('converted_from_late', False):
                summary['converted_absents'] += 1
            
            if status == 'PRE':
                summary['present_days'] += 1
            elif status == 'ABS':
                summary['absent_days'] += 1
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            elif status == 'LAT':
                summary['late_days'] += 1
                summary['present_days'] += 1
                current_consecutive = 0
            elif status == 'LEA':
                summary['leave_days'] += 1
                current_consecutive = 0
            elif status == 'HOL':
                summary['holiday_days'] += 1
                current_consecutive = 0
            elif status == 'HAL':
                summary['half_days'] += 1
                current_consecutive = 0
            else:
                current_consecutive = 0

            summary['total_working_hours'] += record['working_hours']
            summary['total_late_minutes'] += record['late_minutes']
            summary['total_overtime_hours'] += record['overtime_hours']
            
            if record['is_roster_day']:
                summary['total_roster_days'] += 1
            if record['overtime_hours'] > 0:
                summary['overtime_days'] += 1

        summary['max_consecutive_absences'] = max_consecutive

        # Calculate percentages and averages
        working_days = summary['total_days'] - summary['holiday_days'] - summary['leave_days']
        summary['expected_total_hours'] = working_days * expected_daily_hours

        if working_days > 0:
            attended_days = summary['present_days'] + summary['late_days'] + (summary['half_days'] * 0.5)
            summary['attendance_percentage'] = round((attended_days / working_days) * 100, 2)
            
            punctual_days = summary['present_days']
            summary['punctuality_percentage'] = round((punctual_days / working_days) * 100, 2)

        total_attended_days = summary['present_days'] + summary['late_days'] + summary['half_days']
        if total_attended_days > 0:
            summary['average_daily_hours'] = round(summary['total_working_hours'] / total_attended_days, 2)

        return summary

# Configuration API View for AJAX updates
class AttendanceReportConfigAPIView(LoginRequiredMixin, View):
    """API view for managing attendance report configuration."""
    
    def get(self, request):
        """Get current configuration."""
        config = AttendanceReportConfig()
        return JsonResponse({
            'success': True,
            'config': config.get_all_config()
        })
    
    def post(self, request):
        """Update configuration."""
        try:
            data = json.loads(request.body)
            config = AttendanceReportConfig()
            
            # Update configuration
            for category, settings in data.get('config', {}).items():
                if isinstance(settings, dict):
                    for key, value in settings.items():
                        config.set(category, key, value)
                else:
                    config.config[category] = settings
            
            return JsonResponse({
                'success': True,
                'message': 'Configuration updated successfully',
                'config': config.get_all_config()
            })
            
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Configuration update failed: {str(e)}'
            })