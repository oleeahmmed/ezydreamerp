import logging
from datetime import timedelta, datetime, time
from django.utils import timezone
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class UnifiedAttendanceProcessor:
    """
    🔥 Enhanced Unified Attendance Processing System with New Rules
    
    New Features:
    ✅ Minimum Working Hours Rule (Intime + Outtime Duration)
    ✅ Half Day Rule Based on Working Hours
    ✅ In-time and Out-time Both Must Rule
    ✅ Maximum Allowable Working Hours Rule
    ✅ Dynamic Shift Detection Override Rule
    ✅ Grace Time per Shift Instead of Global
    ✅ Consecutive Absence to Flag as Termination Risk
    ✅ Max Early Out Threshold
    """
    
    def __init__(self, form_data):
        """Initialize with comprehensive form configuration data including new rules."""
        # Basic Configuration with None handling
        self.weekend_days = [int(day) for day in form_data.get('weekend_days', [4])]
        self.grace_minutes = form_data.get('grace_minutes') or 15
        self.early_out_threshold = form_data.get('early_out_threshold_minutes') or 30
        self.overtime_start_after = form_data.get('overtime_start_after_minutes') or 15
        self.minimum_overtime_minutes = form_data.get('minimum_overtime_minutes') or 60
        
        # 🔥 NEW RULE 1: Minimum Working Hours Rule
        self.minimum_working_hours_for_present = form_data.get('minimum_working_hours_for_present') or 4
        self.enable_minimum_working_hours_rule = form_data.get('enable_minimum_working_hours_rule', False)
        
        # 🔥 NEW RULE 2: Half Day Rule Based on Working Hours
        self.half_day_minimum_hours = form_data.get('half_day_minimum_hours') or 4
        self.half_day_maximum_hours = form_data.get('half_day_maximum_hours') or 6
        self.enable_working_hours_half_day_rule = form_data.get('enable_working_hours_half_day_rule', False)
        
        # 🔥 NEW RULE 3: In-time and Out-time Both Must Rule
        self.require_both_in_and_out = form_data.get('require_both_in_and_out', False)
        
        # 🔥 NEW RULE 4: Maximum Allowable Working Hours Rule
        self.maximum_allowable_working_hours = form_data.get('maximum_allowable_working_hours') or 16
        self.enable_maximum_working_hours_rule = form_data.get('enable_maximum_working_hours_rule', False)
        
        # 🔥 NEW RULE 5: Dynamic Shift Detection Override Rule
        self.dynamic_shift_fallback_to_default = form_data.get('dynamic_shift_fallback_to_default', True)
        self.dynamic_shift_fallback_shift_id = form_data.get('dynamic_shift_fallback_shift_id')
        
        # 🔥 NEW RULE 6: Grace Time per Shift Instead of Global
        self.use_shift_grace_time = form_data.get('use_shift_grace_time', False)
        
        # 🔥 NEW RULE 7: Consecutive Absence to Flag as Termination Risk
        self.consecutive_absence_termination_risk_days = form_data.get('consecutive_absence_termination_risk_days') or 5
        self.enable_consecutive_absence_flagging = form_data.get('enable_consecutive_absence_flagging', False)
        
        # 🔥 NEW RULE 8: Max Early Out Threshold
        self.max_early_out_threshold_minutes = form_data.get('max_early_out_threshold_minutes') or 120
        self.max_early_out_occurrences = form_data.get('max_early_out_occurrences') or 3
        self.enable_max_early_out_flagging = form_data.get('enable_max_early_out_flagging', False)
        
        # 🔥 Enhanced Shift Detection Configuration
        self.enable_dynamic_shift_detection = form_data.get('enable_dynamic_shift_detection', False)
        self.dynamic_shift_tolerance_minutes = form_data.get('dynamic_shift_tolerance_minutes') or 30
        self.multiple_shift_priority = form_data.get('multiple_shift_priority', 'least_break')
        
        # 🔥 Advanced Overtime Configuration
        self.overtime_calculation_method = form_data.get('overtime_calculation_method', 'shift_based')
        self.holiday_overtime_full_day = form_data.get('holiday_overtime_full_day', True)
        self.weekend_overtime_full_day = form_data.get('weekend_overtime_full_day', True)
        self.late_affects_overtime = form_data.get('late_affects_overtime', False)
        self.separate_ot_break_time = form_data.get('separate_ot_break_time') or 0
        
        # 🔥 Break Time Configuration
        self.use_shift_break_time = form_data.get('use_shift_break_time', True)
        self.default_break_minutes = form_data.get('default_break_minutes') or 60
        self.break_deduction_method = form_data.get('break_deduction_method', 'fixed')
        
        # Advanced Rules
        self.late_to_absent_days = form_data.get('late_to_absent_days') or 3
        self.holiday_before_after_absent = form_data.get('holiday_before_after_absent', True)
        self.weekend_before_after_absent = form_data.get('weekend_before_after_absent', True)
        self.require_holiday_presence = form_data.get('require_holiday_presence', False)
        self.include_holiday_analysis = form_data.get('include_holiday_analysis', True)
        self.holiday_buffer_days = form_data.get('holiday_buffer_days', 1)
        
        # Employee Override Settings
        self.use_employee_specific_grace = form_data.get('use_employee_specific_grace', True)
        self.use_employee_specific_overtime = form_data.get('use_employee_specific_overtime', True)
        self.use_employee_expected_hours = form_data.get('use_employee_expected_hours', True)
        
        # Cache for performance
        self._shift_cache = {}
        self._employee_cache = {}
    
    def get_config_summary(self):
        """Get current configuration summary for display including new rules."""
        return {
            'basic_settings': {
                'grace_minutes': self.grace_minutes,
                'early_out_threshold': self.early_out_threshold,
                'overtime_start_after': self.overtime_start_after,
                'minimum_overtime_minutes': self.minimum_overtime_minutes,
            },
            'new_rules': {
                'minimum_working_hours_for_present': self.minimum_working_hours_for_present,
                'enable_minimum_working_hours_rule': self.enable_minimum_working_hours_rule,
                'half_day_minimum_hours': self.half_day_minimum_hours,
                'half_day_maximum_hours': self.half_day_maximum_hours,
                'enable_working_hours_half_day_rule': self.enable_working_hours_half_day_rule,
                'require_both_in_and_out': self.require_both_in_and_out,
                'maximum_allowable_working_hours': self.maximum_allowable_working_hours,
                'enable_maximum_working_hours_rule': self.enable_maximum_working_hours_rule,
                'use_shift_grace_time': self.use_shift_grace_time,
                'consecutive_absence_termination_risk_days': self.consecutive_absence_termination_risk_days,
                'enable_consecutive_absence_flagging': self.enable_consecutive_absence_flagging,
                'max_early_out_threshold_minutes': self.max_early_out_threshold_minutes,
                'max_early_out_occurrences': self.max_early_out_occurrences,
                'enable_max_early_out_flagging': self.enable_max_early_out_flagging,
            },
            'shift_detection': {
                'dynamic_enabled': self.enable_dynamic_shift_detection,
                'tolerance_minutes': self.dynamic_shift_tolerance_minutes,
                'multiple_shift_priority': self.multiple_shift_priority,
                'fallback_to_default': self.dynamic_shift_fallback_to_default,
            },
            'overtime_rules': {
                'calculation_method': self.overtime_calculation_method,
                'holiday_full_day': self.holiday_overtime_full_day,
                'weekend_full_day': self.weekend_overtime_full_day,
                'late_affects_ot': self.late_affects_overtime,
                'separate_ot_break': self.separate_ot_break_time,
            },
            'break_time': {
                'use_shift_break': self.use_shift_break_time,
                'default_break_minutes': self.default_break_minutes,
                'deduction_method': self.break_deduction_method,
            },
            'advanced_rules': {
                'late_to_absent_days': self.late_to_absent_days,
                'holiday_before_after_absent': self.holiday_before_after_absent,
                'weekend_before_after_absent': self.weekend_before_after_absent,
            },
            'weekend_days': self.weekend_days,
        }
    
    def process_employee_attendance(self, employee, start_date, end_date, zk_logs, 
                                  holidays, leave_applications, roster_data):
        """
        🔥 Enhanced attendance processing with new rules and dynamic shift detection.
        Returns both daily records and comprehensive summary statistics.
        """
        
        # Organize leave applications by date
        leave_dates = self._organize_leave_dates(leave_applications, start_date, end_date)
        
        # Process each day
        daily_records = []
        shift_analysis = {
            'roster_day_usage': 0,
            'roster_assignment_usage': 0,
            'default_shift_usage': 0,
            'dynamic_detection_usage': 0,
            'no_shift_days': 0,
            'multiple_shift_matches': 0,
            'fallback_usage': 0,
        }
        
        current_date = start_date
        late_count = 0
        converted_absents = 0
        consecutive_absences = 0
        max_consecutive_absences = 0
        early_out_count = 0
        flagged_records = []
        
        while current_date <= end_date:
            daily_record = self._process_single_day_attendance(
                current_date, employee, zk_logs, holidays, leave_dates, 
                roster_data, shift_analysis
            )
            
            # 🔥 NEW RULE: Apply minimum working hours rule
            if self.enable_minimum_working_hours_rule:
                daily_record = self._apply_minimum_working_hours_rule(daily_record)
            
            # 🔥 NEW RULE: Apply working hours based half day rule
            if self.enable_working_hours_half_day_rule:
                daily_record = self._apply_working_hours_half_day_rule(daily_record)
            
            # 🔥 NEW RULE: Apply both in and out time requirement
            if self.require_both_in_and_out:
                daily_record = self._apply_both_in_out_rule(daily_record)
            
            # 🔥 NEW RULE: Apply maximum working hours rule
            if self.enable_maximum_working_hours_rule:
                daily_record = self._apply_maximum_working_hours_rule(daily_record)
            
            # Apply late to absent conversion
            if daily_record['original_status'] == 'LAT':
                late_count += 1
                if late_count >= self.late_to_absent_days:
                    daily_record['status'] = 'ABS'
                    daily_record['converted_from_late'] = True
                    daily_record['conversion_reason'] = f'Converted to absent after {self.late_to_absent_days} consecutive late days'
                    converted_absents += 1
                    late_count = 0
            elif daily_record['status'] not in ['HOL', 'LEA']:
                late_count = 0
            
            # 🔥 NEW RULE: Track consecutive absences for termination risk
            if daily_record['status'] == 'ABS':
                consecutive_absences += 1
                max_consecutive_absences = max(max_consecutive_absences, consecutive_absences)
            else:
                consecutive_absences = 0
            
            # 🔥 NEW RULE: Track early out occurrences
            if daily_record['early_out_minutes'] > self.max_early_out_threshold_minutes:
                early_out_count += 1
                daily_record['excessive_early_out'] = True
            
            # Flag termination risk
            if (self.enable_consecutive_absence_flagging and 
                consecutive_absences >= self.consecutive_absence_termination_risk_days):
                daily_record['termination_risk_flag'] = True
                flagged_records.append({
                    'date': current_date,
                    'type': 'termination_risk',
                    'consecutive_days': consecutive_absences
                })
            
            # Flag excessive early outs
            if (self.enable_max_early_out_flagging and 
                early_out_count >= self.max_early_out_occurrences):
                daily_record['excessive_early_out_flag'] = True
                flagged_records.append({
                    'date': current_date,
                    'type': 'excessive_early_out',
                    'count': early_out_count
                })
            
            daily_record['late_count_running'] = late_count
            daily_record['converted_absents_total'] = converted_absents
            daily_record['consecutive_absences'] = consecutive_absences
            daily_record['early_out_count'] = early_out_count
            
            daily_records.append(daily_record)
            current_date += timedelta(days=1)
        
        # Apply holiday and weekend rules
        if self.holiday_before_after_absent:
            self._apply_holiday_absence_rule(daily_records, holidays)
        
        if self.weekend_before_after_absent:
            self._apply_weekend_absence_rule(daily_records)
        
        # Generate comprehensive summary statistics
        summary_stats = self._generate_comprehensive_summary(
            daily_records, employee, start_date, end_date, shift_analysis, 
            max_consecutive_absences, flagged_records
        )
        
        return {
            'daily_records': daily_records,
            'summary_stats': summary_stats,
            'shift_analysis': shift_analysis,
            'flagged_records': flagged_records,
            'config_applied': self.get_config_summary(),
        }
    
    def _apply_minimum_working_hours_rule(self, record):
        """🔥 NEW RULE 1: Apply minimum working hours rule."""
        if (record['status'] in ['PRE', 'LAT'] and 
            record['working_hours'] < self.minimum_working_hours_for_present):
            record['original_status'] = record['status']
            record['status'] = 'ABS'
            record['converted_from_minimum_hours'] = True
            record['conversion_reason'] = f'Working hours ({record["working_hours"]}h) less than minimum required ({self.minimum_working_hours_for_present}h)'
        return record
    
    def _apply_working_hours_half_day_rule(self, record):
        """🔥 NEW RULE 2: Apply working hours based half day rule."""
        if (record['status'] in ['PRE', 'LAT'] and 
            self.half_day_minimum_hours <= record['working_hours'] < self.half_day_maximum_hours):
            record['original_status'] = record['status']
            record['status'] = 'HAL'
            record['converted_to_half_day'] = True
            record['conversion_reason'] = f'Working hours ({record["working_hours"]}h) qualifies for half day'
        return record
    
    def _apply_both_in_out_rule(self, record):
        """🔥 NEW RULE 3: Apply both in-time and out-time requirement."""
        if (record['status'] in ['PRE', 'LAT'] and 
            (not record['in_time'] or not record['out_time'])):
            record['original_status'] = record['status']
            record['status'] = 'ABS'
            record['converted_from_incomplete_punch'] = True
            record['conversion_reason'] = 'Both check-in and check-out required'
        return record
    
    def _apply_maximum_working_hours_rule(self, record):
        """🔥 NEW RULE 4: Apply maximum working hours rule."""
        if record['working_hours'] > self.maximum_allowable_working_hours:
            record['excessive_working_hours_flag'] = True
            record['flag_reason'] = f'Working hours ({record["working_hours"]}h) exceeds maximum allowed ({self.maximum_allowable_working_hours}h)'
            # Log this as potentially erroneous data
            logger.warning(f"Excessive working hours detected: {record['working_hours']}h for employee on {record['date']}")
        return record
    
    def _process_single_day_attendance(self, date, employee, zk_logs, holidays, leave_dates, roster_data, shift_analysis):
        """🔥 Enhanced single day processing with new rules and dynamic shift detection."""
        
        # Initialize daily record
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
            'shift_name': 'No Shift',
            'shift_source': 'None',
            'shift_start_time': None,
            'shift_end_time': None,
            'is_roster_day': False,
            'is_holiday': False,
            'is_leave': False,
            'holiday_name': None,
            'roster_info': None,
            'total_logs': 0,
            'expected_hours': employee.expected_work_hours,
            'converted_from_late': False,
            'dynamic_shift_used': False,
            'shift_match_confidence': 0.0,
            'multiple_shifts_found': [],
            'break_time_minutes': 0,
            'net_working_hours': 0.0,
            'overtime_break_minutes': 0,
            # 🔥 NEW FIELDS for new rules
            'converted_from_minimum_hours': False,
            'converted_to_half_day': False,
            'converted_from_incomplete_punch': False,
            'excessive_working_hours_flag': False,
            'termination_risk_flag': False,
            'excessive_early_out_flag': False,
            'excessive_early_out': False,
            'flag_reason': None,
            'conversion_reason': None,
        }
        
        # Check holidays first (highest priority)
        holiday_dict = {h.date: h.name for h in holidays}
        if date in holiday_dict:
            record.update({
                'status': 'HOL',
                'original_status': 'HOL',
                'is_holiday': True,
                'holiday_name': holiday_dict[date]
            })
            shift_analysis['no_shift_days'] += 1
            
            # Process holiday attendance if present
            daily_zk_logs = zk_logs.filter(timestamp__date=date)
            if daily_zk_logs.exists():
                self._process_holiday_attendance(record, daily_zk_logs, employee)
            
            return record
        
        # Check leaves
        if date in leave_dates:
            record.update({
                'status': 'LEA',
                'original_status': 'LEA',
                'is_leave': True
            })
            shift_analysis['no_shift_days'] += 1
            return record
        
        # Check weekends
        if date.weekday() in self.weekend_days:
            record.update({
                'status': 'HOL',
                'original_status': 'HOL',
                'is_holiday': True,
                'holiday_name': f'{date.strftime("%A")} (Weekend)'
            })
            shift_analysis['no_shift_days'] += 1
            
            # Process weekend attendance if present
            daily_zk_logs = zk_logs.filter(timestamp__date=date)
            if daily_zk_logs.exists():
                self._process_weekend_attendance(record, daily_zk_logs, employee)
            
            return record
        
        # Process ZK logs for this date
        daily_zk_logs = zk_logs.filter(timestamp__date=date)
        record['total_logs'] = daily_zk_logs.count()
        
        if not daily_zk_logs.exists():
            # No attendance logs - determine shift for absence analysis
            shift_info = self._get_shift_for_date(date, employee, roster_data, None, shift_analysis)
            record.update(shift_info)
            return record
        
        # Process attendance logs
        sorted_logs = sorted(daily_zk_logs, key=lambda x: x.timestamp)
        first_log = sorted_logs[0]
        last_log = sorted_logs[-1] if len(sorted_logs) > 1 else first_log
        
        record.update({
            'in_time': first_log.timestamp,
            'out_time': last_log.timestamp if len(sorted_logs) > 1 else None
        })
        
        # 🔥 DYNAMIC SHIFT DETECTION vs PRIORITY-BASED DETECTION
        if self.enable_dynamic_shift_detection:
            shift_info = self._detect_shift_dynamically(date, employee, record, shift_analysis)
            record['dynamic_shift_used'] = True
        else:
            shift_info = self._get_shift_for_date(date, employee, roster_data, record, shift_analysis)
        
        record.update(shift_info)
        
        # Calculate enhanced attendance metrics
        if record['shift'] and record['shift_start_time'] and record['shift_end_time']:
            self._calculate_enhanced_attendance_metrics(record, employee)
        else:
            # Basic calculation without shift
            self._calculate_basic_attendance_metrics(record, employee)
        
        return record
    
    def _detect_shift_dynamically(self, date, employee, attendance_record, shift_analysis):
        """🔥 Dynamic shift detection with fallback options."""
        
        if not attendance_record['in_time']:
            return self._get_fallback_shift_info(date, employee, "No check-in time for dynamic detection")
        
        # Import Shift model
        try:
            from Hrm.models import Shift
        except ImportError:
            return self._get_fallback_shift_info(date, employee, "Shift model not available")
        
        # Get all available shifts
        all_shifts = Shift.objects.all()
        if not all_shifts.exists():
            return self._get_fallback_shift_info(date, employee, "No shifts configured in system")
        
        # Find matching shifts
        matching_shifts = []
        in_time = attendance_record['in_time'].time()
        out_time = attendance_record['out_time'].time() if attendance_record['out_time'] else None
        
        for shift in all_shifts:
            match_score = self._calculate_shift_match_score(shift, in_time, out_time)
            
            if match_score > 0:
                matching_shifts.append({
                    'shift': shift,
                    'score': match_score,
                    'confidence': min(match_score / 100, 1.0)
                })
        
        # Sort by score (highest first)
        matching_shifts.sort(key=lambda x: x['score'], reverse=True)
        
        if not matching_shifts:
            shift_analysis['no_shift_days'] += 1
            return self._get_fallback_shift_info(date, employee, "No shifts match the attendance pattern")
        
        if len(matching_shifts) > 1:
            shift_analysis['multiple_shift_matches'] += 1
            # Apply priority logic for multiple matches
            best_shift = self._select_best_shift_from_matches(matching_shifts)
        else:
            best_shift = matching_shifts[0]
        
        shift_analysis['dynamic_detection_usage'] += 1
        
        return self._build_shift_info(
            shift=best_shift['shift'],
            source='DynamicDetection',
            roster_info=f"Dynamic Detection (Confidence: {best_shift['confidence']:.1%})",
            date=date,
            is_roster_day=False,
            additional_data={
                'shift_match_confidence': best_shift['confidence'],
                'multiple_shifts_found': [m['shift'].name for m in matching_shifts],
                'dynamic_shift_used': True,
            }
        )
    
    def _get_fallback_shift_info(self, date, employee, reason):
        """🔥 NEW RULE 5: Get fallback shift when dynamic detection fails."""
        if self.dynamic_shift_fallback_to_default and employee.default_shift:
            return self._build_shift_info(
                shift=employee.default_shift,
                source='FallbackDefault',
                roster_info=f"Fallback to Default: {reason}",
                date=date,
                is_roster_day=False
            )
        elif self.dynamic_shift_fallback_shift_id:
            try:
                from Hrm.models import Shift
                fallback_shift = Shift.objects.get(id=self.dynamic_shift_fallback_shift_id)
                return self._build_shift_info(
                    shift=fallback_shift,
                    source='FallbackFixed',
                    roster_info=f"Fallback to Fixed Shift: {reason}",
                    date=date,
                    is_roster_day=False
                )
            except:
                pass
        
        return self._get_no_shift_info(reason)
    
    def _calculate_enhanced_attendance_metrics(self, record, employee):
        """🔥 Enhanced attendance metrics calculation with new rules."""
        
        shift = record['shift']
        in_time = record['in_time']
        out_time = record['out_time']
        expected_start = record['expected_start']
        expected_end = record['expected_end']
        
        # 🔥 NEW RULE 6: Get shift-specific or global grace time
        if self.use_shift_grace_time and hasattr(shift, 'grace_time') and shift.grace_time:
            grace_minutes = shift.grace_time
        else:
            grace_minutes = self._get_employee_setting(employee, 'overtime_grace_minutes', self.grace_minutes)
        
        overtime_start_after = self._get_employee_setting(employee, 'overtime_grace_minutes', self.overtime_start_after)
        expected_hours = self._get_employee_setting(employee, 'expected_work_hours', 8)
        
        # Check for late arrival
        if expected_start and grace_minutes is not None:
            late_threshold = expected_start + timedelta(minutes=grace_minutes)
            if in_time > late_threshold:
                late_duration = in_time - expected_start
                record['late_minutes'] = round(late_duration.total_seconds() / 60)
                record['status'] = 'LAT'
                record['original_status'] = 'LAT'
            else:
                record['status'] = 'PRE'
                record['original_status'] = 'PRE'
        else:
            record['status'] = 'PRE'
            record['original_status'] = 'PRE'
        
        # Calculate working hours with enhanced break handling
        if out_time:
            total_duration = out_time - in_time
            total_hours = total_duration.total_seconds() / 3600
            
            # 🔥 Enhanced Break Time Calculation
            break_minutes = self._calculate_break_time(record, total_hours)
            record['break_time_minutes'] = break_minutes
            
            working_hours = total_hours - (break_minutes / 60)
            record['working_hours'] = max(0, round(working_hours, 2))
            record['net_working_hours'] = record['working_hours']
        else:
            record['working_hours'] = 0
            record['net_working_hours'] = 0
            record['break_time_minutes'] = 0
        
        # Check for early departure
        if out_time and expected_end:
            early_threshold = expected_end - timedelta(minutes=self.early_out_threshold)
            if out_time < early_threshold:
                early_duration = expected_end - out_time
                record['early_out_minutes'] = round(early_duration.total_seconds() / 60)
        
        # 🔥 Enhanced Overtime Calculation
        if out_time:
            overtime_info = self._calculate_enhanced_overtime(record, employee, expected_start, expected_end)
            record.update(overtime_info)
        
        # Determine final status based on working hours (will be overridden by new rules if enabled)
        half_day_threshold = expected_hours * 0.5
        if record['working_hours'] > 0 and record['working_hours'] < half_day_threshold:
            record['status'] = 'HAL'
            if record['original_status'] not in ['HAL']:
                record['original_status'] = 'HAL'
    
    def _calculate_shift_match_score(self, shift, in_time, out_time=None):
        """Calculate how well attendance times match a shift."""
        
        score = 0
        tolerance_minutes = self.dynamic_shift_tolerance_minutes
        tolerance = timedelta(minutes=tolerance_minutes)
        
        # Convert times to datetime for calculation
        base_date = datetime.now().date()
        shift_start = datetime.combine(base_date, shift.start_time)
        shift_end = datetime.combine(base_date, shift.end_time)
        
        # Handle overnight shifts
        if shift.end_time < shift.start_time:
            shift_end += timedelta(days=1)
        
        actual_start = datetime.combine(base_date, in_time)
        
        # Check in time match
        start_diff = abs((actual_start - shift_start).total_seconds())
        if start_diff <= tolerance.total_seconds():
            # Perfect match gets 50 points, decreasing with difference
            score += max(0, 50 - (start_diff / 60))  # Reduce by 1 point per minute
        
        # Check out time match (if available)
        if out_time:
            actual_end = datetime.combine(base_date, out_time)
            if out_time < in_time:  # Overnight attendance
                actual_end += timedelta(days=1)
            
            end_diff = abs((actual_end - shift_end).total_seconds())
            if end_diff <= tolerance.total_seconds():
                score += max(0, 50 - (end_diff / 60))
        else:
            # No out time, give partial score if in time matches
            score += 25 if score > 0 else 0
        
        return score
    
    def _select_best_shift_from_matches(self, matching_shifts):
        """🔥 Select the best shift when multiple matches are found."""
        
        if self.multiple_shift_priority == 'least_break':
            # Select shift with least break time
            return min(matching_shifts, key=lambda x: getattr(x['shift'], 'break_time', 60))
        elif self.multiple_shift_priority == 'shortest_duration':
            # Select shift with shortest duration
            return min(matching_shifts, key=lambda x: getattr(x['shift'], 'duration_minutes', 480))
        elif self.multiple_shift_priority == 'alphabetical':
            # Select alphabetically first shift name
            return min(matching_shifts, key=lambda x: x['shift'].name)
        else:
            # Default: highest score
            return matching_shifts[0]
    
    def _get_shift_for_date(self, date, employee, roster_data, attendance_record=None, shift_analysis=None):
        """🔥 Get shift with priority logic: RosterDay > RosterAssignment > Default."""
        
        # Priority 1: Check RosterDay for specific date
        if 'days' in roster_data and date in roster_data['days']:
            roster_day = roster_data['days'][date]
            if roster_day.shift:
                if shift_analysis:
                    shift_analysis['roster_day_usage'] += 1
                
                return self._build_shift_info(
                    shift=roster_day.shift,
                    source='RosterDay',
                    roster_info=f"Roster Day: {roster_day.roster_assignment.roster.name}",
                    date=date,
                    is_roster_day=True
                )
        
        # Priority 2: Check RosterAssignment for date range
        if 'assignments' in roster_data and date in roster_data['assignments']:
            roster_assignment = roster_data['assignments'][date]
            
            if roster_assignment.shift:
                if shift_analysis:
                    shift_analysis['roster_assignment_usage'] += 1
                
                return self._build_shift_info(
                    shift=roster_assignment.shift,
                    source='RosterAssignment',
                    roster_info=f"Roster Assignment: {roster_assignment.roster.name}",
                    date=date,
                    is_roster_day=True
                )
            elif employee.default_shift:
                if shift_analysis:
                    shift_analysis['default_shift_usage'] += 1
                
                return self._build_shift_info(
                    shift=employee.default_shift,
                    source='RosterAssignment',
                    roster_info=f"Roster Assignment (Default Shift): {roster_assignment.roster.name}",
                    date=date,
                    is_roster_day=True
                )
        
        # Priority 3: Use employee's default shift
        if employee.default_shift:
            if shift_analysis:
                shift_analysis['default_shift_usage'] += 1
            
            return self._build_shift_info(
                shift=employee.default_shift,
                source='Default',
                roster_info="Employee Default Shift",
                date=date,
                is_roster_day=False
            )
        
        # No shift found
        if shift_analysis:
            shift_analysis['no_shift_days'] += 1
        
        return self._get_no_shift_info("No Shift Assigned")
    
    def _build_shift_info(self, shift, source, roster_info, date, is_roster_day=False, additional_data=None):
        """Build comprehensive shift information dictionary."""
        
        try:
            expected_start = timezone.datetime.combine(date, shift.start_time)
            expected_start = timezone.make_aware(expected_start, timezone.get_default_timezone())
            
            expected_end = timezone.datetime.combine(date, shift.end_time)
            expected_end = timezone.make_aware(expected_end, timezone.get_default_timezone())
            
            # Handle overnight shifts
            if shift.end_time < shift.start_time:
                expected_end += timedelta(days=1)
            
            result = {
                'shift': shift,
                'shift_name': shift.name,
                'shift_source': source,
                'shift_start_time': shift.start_time,
                'shift_end_time': shift.end_time,
                'expected_start': expected_start,
                'expected_end': expected_end,
                'roster_info': roster_info,
                'is_roster_day': is_roster_day,
                'shift_break_time': getattr(shift, 'break_time', self.default_break_minutes),
            }
            
            if additional_data:
                result.update(additional_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error building shift info: {str(e)}")
            return self._get_no_shift_info(f"Error processing shift: {str(e)}")
    
    def _get_no_shift_info(self, reason="No shift available"):
        """Get default no-shift information."""
        return {
            'shift': None,
            'shift_name': 'No Shift',
            'shift_source': 'None',
            'shift_start_time': None,
            'shift_end_time': None,
            'expected_start': None,
            'expected_end': None,
            'roster_info': reason,
            'is_roster_day': False,
            'shift_break_time': self.default_break_minutes,
            'shift_match_confidence': 0.0,
            'multiple_shifts_found': [],
            'dynamic_shift_used': False
        }
    
    def _calculate_break_time(self, record, total_hours):
        """🔥 Calculate break time based on configuration."""
        
        if self.use_shift_break_time and record['shift']:
            base_break = getattr(record['shift'], 'break_time', self.default_break_minutes)
        else:
            base_break = self.default_break_minutes
        
        if self.break_deduction_method == 'proportional':
            # Proportional break based on working hours
            if total_hours <= 4:
                return base_break * 0.5
            elif total_hours <= 6:
                return base_break * 0.75
            else:
                return base_break
        else:
            # Fixed break time
            return base_break
    
    def _calculate_enhanced_overtime(self, record, employee, expected_start, expected_end):
        """🔥 Enhanced overtime calculation with multiple methods and break handling."""
        
        overtime_info = {
            'overtime_hours': 0.0,
            'overtime_break_minutes': 0,
            'overtime_calculation_method': self.overtime_calculation_method,
        }
        
        out_time = record['out_time']
        in_time = record['in_time']
        
        # Determine overtime start point based on method
        if self.overtime_calculation_method == 'shift_based':
            # Overtime starts after shift end + grace period
            if expected_end:
                overtime_start = expected_end + timedelta(minutes=self.overtime_start_after)
            else:
                return overtime_info
        else:
            # Overtime starts after expected work hours + grace period
            overtime_start = in_time + timedelta(hours=employee.expected_work_hours) + timedelta(minutes=self.overtime_start_after)
        
        # Handle late arrival affecting overtime
        if self.late_affects_overtime and record['late_minutes'] > 0:
            # Adjust overtime start if employee was late
            overtime_start += timedelta(minutes=record['late_minutes'])
        
        # Calculate overtime duration
        if out_time > overtime_start:
            overtime_duration = out_time - overtime_start
            overtime_minutes = overtime_duration.total_seconds() / 60
            
            # Deduct separate OT break time if configured
            if self.separate_ot_break_time > 0:
                overtime_minutes -= self.separate_ot_break_time
                overtime_info['overtime_break_minutes'] = self.separate_ot_break_time
            
            # Apply minimum overtime threshold
            if overtime_minutes >= self.minimum_overtime_minutes:
                overtime_info['overtime_hours'] = round(overtime_minutes / 60, 2)
        
        return overtime_info
    
    def _process_holiday_attendance(self, record, daily_logs, employee):
        """🔥 Process attendance on holidays with special overtime rules."""
        
        sorted_logs = sorted(daily_logs, key=lambda x: x.timestamp)
        first_log = sorted_logs[0]
        last_log = sorted_logs[-1] if len(sorted_logs) > 1 else first_log
        
        record.update({
            'in_time': first_log.timestamp,
            'out_time': last_log.timestamp if len(sorted_logs) > 1 else None,
            'status': 'HOL',  # Keep holiday status but mark as worked
        })
        
        if record['out_time'] and self.holiday_overtime_full_day:
            # On holidays, entire working time is considered overtime
            total_duration = record['out_time'] - record['in_time']
            total_hours = total_duration.total_seconds() / 3600
            
            # Deduct break time
            break_minutes = self.default_break_minutes
            working_hours = total_hours - (break_minutes / 60)
            
            record.update({
                'working_hours': max(0, round(working_hours, 2)),
                'overtime_hours': max(0, round(working_hours, 2)),
                'break_time_minutes': break_minutes,
                'holiday_overtime': True,
            })
    
    def _process_weekend_attendance(self, record, daily_logs, employee):
        """🔥 Process attendance on weekends with special overtime rules."""
        
        sorted_logs = sorted(daily_logs, key=lambda x: x.timestamp)
        first_log = sorted_logs[0]
        last_log = sorted_logs[-1] if len(sorted_logs) > 1 else first_log
        
        record.update({
            'in_time': first_log.timestamp,
            'out_time': last_log.timestamp if len(sorted_logs) > 1 else None,
            'status': 'HOL',  # Keep weekend status but mark as worked
        })
        
        if record['out_time'] and self.weekend_overtime_full_day:
            # On weekends, entire working time is considered overtime
            total_duration = record['out_time'] - record['in_time']
            total_hours = total_duration.total_seconds() / 3600
            
            # Deduct break time
            break_minutes = self.default_break_minutes
            working_hours = total_hours - (break_minutes / 60)
            
            record.update({
                'working_hours': max(0, round(working_hours, 2)),
                'overtime_hours': max(0, round(working_hours, 2)),
                'break_time_minutes': break_minutes,
                'weekend_overtime': True,
            })
    
    def _calculate_basic_attendance_metrics(self, record, employee):
        """Basic calculation without shift information."""
        
        record['status'] = 'PRE'
        record['original_status'] = 'PRE'
        
        if record['out_time']:
            duration = record['out_time'] - record['in_time']
            working_hours = duration.total_seconds() / 3600
            
            # Deduct default break time
            break_minutes = self.default_break_minutes
            working_hours = max(0, working_hours - (break_minutes / 60))
            
            record.update({
                'working_hours': round(working_hours, 2),
                'break_time_minutes': break_minutes,
                'net_working_hours': round(working_hours, 2),
            })
    
    def _get_employee_setting(self, employee, employee_attr, default_value):
        """Get employee-specific setting or fall back to default."""
        
        if hasattr(employee, employee_attr):
            employee_value = getattr(employee, employee_attr, None)
            if employee_value is not None:
                return employee_value
        
        return default_value
    
    def _organize_leave_dates(self, leave_applications, start_date, end_date):
        """Organize leave applications by date."""
        leave_dates = set()
        for leave_app in leave_applications:
            if leave_app.status == 'APP':  # Approved leaves only
                current_leave_date = leave_app.start_date
                while current_leave_date <= leave_app.end_date:
                    if start_date <= current_leave_date <= end_date:
                        leave_dates.add(current_leave_date)
                    current_leave_date += timedelta(days=1)
        return leave_dates
    
    def _apply_holiday_absence_rule(self, daily_records, holidays):
        """Apply holiday absence rule: if absent before and after holiday, mark holiday as absent."""
        holiday_dates = {h.date for h in holidays}
        
        for i, record in enumerate(daily_records):
            if record['date'] in holiday_dates and record['is_holiday']:
                prev_day_absent = False
                if i > 0:
                    prev_record = daily_records[i - 1]
                    prev_day_absent = prev_record['status'] == 'ABS'
                
                next_day_absent = False
                if i < len(daily_records) - 1:
                    next_record = daily_records[i + 1]
                    next_day_absent = next_record['status'] == 'ABS'
                
                if prev_day_absent and next_day_absent:
                    record['status'] = 'ABS'
                    record['is_holiday'] = False
                    record['holiday_name'] = None
                    record['conversion_reason'] = 'Holiday between absences converted to absent'
    
    def _apply_weekend_absence_rule(self, daily_records):
        """Apply weekend absence rule similar to holiday rule."""
        for i, record in enumerate(daily_records):
            if (record['date'].weekday() in self.weekend_days and 
                record['is_holiday'] and 'Weekend' in record.get('holiday_name', '')):
                
                prev_day_absent = False
                if i > 0:
                    prev_record = daily_records[i - 1]
                    prev_day_absent = prev_record['status'] == 'ABS'
                
                next_day_absent = False
                if i < len(daily_records) - 1:
                    next_record = daily_records[i + 1]
                    next_day_absent = next_record['status'] == 'ABS'
                
                if prev_day_absent and next_day_absent:
                    record['status'] = 'ABS'
                    record['is_holiday'] = False
                    record['holiday_name'] = None
                    record['conversion_reason'] = 'Weekend between absences converted to absent'
    
    def _generate_comprehensive_summary(self, daily_records, employee, start_date, end_date, shift_analysis, max_consecutive_absences, flagged_records):
        """🔥 Generate comprehensive attendance summary with enhanced metrics including new rules."""
        
        summary = {
            # Basic counts
            'total_days': len(daily_records),
            'present_days': 0,
            'absent_days': 0,
            'late_days': 0,
            'leave_days': 0,
            'holiday_days': 0,
            'half_days': 0,
            
            # Time metrics
            'total_working_hours': 0.0,
            'total_net_working_hours': 0.0,
            'total_late_minutes': 0,
            'total_overtime_hours': 0.0,
            'total_break_minutes': 0,
            'total_early_out_minutes': 0,
            'expected_total_hours': 0.0,
            'average_daily_hours': 0.0,
            
            # Enhanced metrics
            'holiday_overtime_hours': 0.0,
            'weekend_overtime_hours': 0.0,
            'regular_overtime_hours': 0.0,
            'total_overtime_break_minutes': 0,
            
            # Percentages
            'attendance_percentage': 0.0,
            'punctuality_percentage': 0.0,
            
            # Advanced metrics
            'max_consecutive_absences': max_consecutive_absences,
            'total_roster_days': 0,
            'overtime_days': 0,
            'early_out_days': 0,
            'converted_absents': 0,
            'original_late_days': 0,
            
            # 🔥 NEW METRICS for new rules
            'converted_from_minimum_hours': 0,
            'converted_to_half_day': 0,
            'converted_from_incomplete_punch': 0,
            'excessive_working_hours_days': 0,
            'termination_risk_flagged': len([f for f in flagged_records if f['type'] == 'termination_risk']),
            'excessive_early_out_flagged': len([f for f in flagged_records if f['type'] == 'excessive_early_out']),
            'total_flagged_records': len(flagged_records),
            
            # Shift analysis
            'shift_source_breakdown': {
                'RosterDay': shift_analysis.get('roster_day_usage', 0),
                'RosterAssignment': shift_analysis.get('roster_assignment_usage', 0),
                'Default': shift_analysis.get('default_shift_usage', 0),
                'DynamicDetection': shift_analysis.get('dynamic_detection_usage', 0),
                'FallbackDefault': shift_analysis.get('fallback_usage', 0),
                'None': shift_analysis.get('no_shift_days', 0),
            },
            
            # Dynamic detection metrics
            'dynamic_detection_stats': {
                'total_dynamic_detections': shift_analysis.get('dynamic_detection_usage', 0),
                'multiple_matches_count': shift_analysis.get('multiple_shift_matches', 0),
                'fallback_usage': shift_analysis.get('fallback_usage', 0),
                'average_confidence': 0.0,
            },
        }
        
        # Process daily records for statistics
        dynamic_confidences = []
        
        for record in daily_records:
            status = record['status']
            original_status = record.get('original_status', status)
            
            # Count by status
            if status == 'PRE':
                summary['present_days'] += 1
            elif status == 'ABS':
                summary['absent_days'] += 1
            elif status == 'LAT':
                summary['late_days'] += 1
                summary['present_days'] += 1
            elif status == 'LEA':
                summary['leave_days'] += 1
            elif status == 'HOL':
                summary['holiday_days'] += 1
            elif status == 'HAL':
                summary['half_days'] += 1
            
            # Track original late days
            if original_status == 'LAT':
                summary['original_late_days'] += 1
            
            # 🔥 NEW RULE TRACKING
            if record.get('converted_from_late', False):
                summary['converted_absents'] += 1
            if record.get('converted_from_minimum_hours', False):
                summary['converted_from_minimum_hours'] += 1
            if record.get('converted_to_half_day', False):
                summary['converted_to_half_day'] += 1
            if record.get('converted_from_incomplete_punch', False):
                summary['converted_from_incomplete_punch'] += 1
            if record.get('excessive_working_hours_flag', False):
                summary['excessive_working_hours_days'] += 1
            
            # Accumulate time metrics
            summary['total_working_hours'] += record['working_hours']
            summary['total_net_working_hours'] += record.get('net_working_hours', record['working_hours'])
            summary['total_late_minutes'] += record['late_minutes']
            summary['total_overtime_hours'] += record['overtime_hours']
            summary['total_break_minutes'] += record.get('break_time_minutes', 0)
            summary['total_early_out_minutes'] += record['early_out_minutes']
            summary['total_overtime_break_minutes'] += record.get('overtime_break_minutes', 0)
            
            # Categorize overtime
            if record.get('holiday_overtime', False):
                summary['holiday_overtime_hours'] += record['overtime_hours']
            elif record.get('weekend_overtime', False):
                summary['weekend_overtime_hours'] += record['overtime_hours']
            else:
                summary['regular_overtime_hours'] += record['overtime_hours']
            
            # Count special days
            if record['is_roster_day']:
                summary['total_roster_days'] += 1
            if record['overtime_hours'] > 0:
                summary['overtime_days'] += 1
            if record['early_out_minutes'] > 0:
                summary['early_out_days'] += 1
            
            # Dynamic detection stats
            if record.get('dynamic_shift_used', False):
                confidence = record.get('shift_match_confidence', 0.0)
                if confidence > 0:
                    dynamic_confidences.append(confidence)
        
        # Calculate derived metrics
        working_days = summary['total_days'] - summary['holiday_days'] - summary['leave_days']
        summary['expected_total_hours'] = working_days * employee.expected_work_hours
        
        if working_days > 0:
            attended_days = summary['present_days'] + summary['late_days'] + (summary['half_days'] * 0.5)
            summary['attendance_percentage'] = round((attended_days / working_days) * 100, 2)
            
            punctual_days = summary['present_days']
            summary['punctuality_percentage'] = round((punctual_days / working_days) * 100, 2)
        
        total_attended_days = summary['present_days'] + summary['late_days'] + summary['half_days']
        if total_attended_days > 0:
            summary['average_daily_hours'] = round(summary['total_working_hours'] / total_attended_days, 2)
        
        # Dynamic detection averages
        if dynamic_confidences:
            summary['dynamic_detection_stats']['average_confidence'] = round(
                sum(dynamic_confidences) / len(dynamic_confidences), 3
            )
        
        return summary
