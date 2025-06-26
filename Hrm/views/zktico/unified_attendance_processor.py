import logging
from datetime import timedelta, datetime, time
from django.utils import timezone
from collections import defaultdict

logger = logging.getLogger(__name__)

class UnifiedAttendanceProcessor:
    """
    Unified attendance processing logic to ensure consistent results 
    between detailed employee reports and summary reports.
    """
    
    def __init__(self, form_data):
        """Initialize with form configuration data."""
        self.weekend_days = [int(day) for day in form_data.get('weekend_days', [4])]
        self.grace_minutes = form_data.get('grace_minutes', 15)
        self.early_out_threshold = form_data.get('early_out_threshold_minutes', 30)
        self.overtime_start_after = form_data.get('overtime_start_after_minutes', 15)
        self.minimum_overtime_minutes = form_data.get('minimum_overtime_minutes', 60)
        self.late_to_absent_days = form_data.get('late_to_absent_days', 3)
        self.holiday_before_after_absent = form_data.get('holiday_before_after_absent', True)
        self.weekend_before_after_absent = form_data.get('weekend_before_after_absent', True)
        self.require_holiday_presence = form_data.get('require_holiday_presence', False)
        self.include_holiday_analysis = form_data.get('include_holiday_analysis', True)
        self.holiday_buffer_days = form_data.get('holiday_buffer_days', 1)
    
    def process_employee_attendance(self, employee, start_date, end_date, zk_logs, 
                                  holidays, leave_applications, roster_data):
        """
        Process attendance for a single employee with unified logic.
        Returns both daily records and summary statistics.
        """
        
        # Organize leave applications by date
        leave_dates = self._organize_leave_dates(leave_applications, start_date, end_date)
        
        # Process each day
        daily_records = []
        current_date = start_date
        late_count = 0
        converted_absents = 0
        
        while current_date <= end_date:
            daily_record = self._process_single_day_attendance(
                current_date, employee, zk_logs, holidays, leave_dates, roster_data
            )
            
            # Apply late to absent conversion
            if daily_record['original_status'] == 'LAT':
                late_count += 1
                if late_count >= self.late_to_absent_days:
                    daily_record['status'] = 'ABS'
                    daily_record['converted_from_late'] = True
                    converted_absents += 1
                    late_count = 0
            elif daily_record['status'] not in ['HOL', 'LEA']:
                late_count = 0
            
            daily_record['late_count_running'] = late_count
            daily_record['converted_absents_total'] = converted_absents
            
            daily_records.append(daily_record)
            current_date += timedelta(days=1)
        
        # Apply holiday and weekend rules
        if self.holiday_before_after_absent:
            self._apply_holiday_absence_rule(daily_records, holidays)
        
        if self.weekend_before_after_absent:
            self._apply_weekend_absence_rule(daily_records)
        
        # Generate summary statistics
        summary_stats = self._generate_summary_statistics(daily_records, employee, start_date, end_date)
        
        return {
            'daily_records': daily_records,
            'summary_stats': summary_stats
        }
    
    def _process_single_day_attendance(self, date, employee, zk_logs, holidays, leave_dates, roster_data):
        """Process attendance for a single day with unified logic."""
        
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
            'is_short_leave': False,
            'holiday_name': None,
            'roster_info': None,
            'total_logs': 0,
            'expected_hours': employee.expected_work_hours,
            'converted_from_late': False,
        }
        
        # Check holidays first (highest priority)
        holiday_dict = {h.date: h.name for h in holidays}
        if date in holiday_dict:
            record['status'] = 'HOL'
            record['original_status'] = 'HOL'
            record['is_holiday'] = True
            record['holiday_name'] = holiday_dict[date]
            return record
        
        # Check leaves
        if date in leave_dates:
            record['status'] = 'LEA'
            record['original_status'] = 'LEA'
            record['is_leave'] = True
            return record
        
        # Check weekends
        if date.weekday() in self.weekend_days:
            record['status'] = 'HOL'
            record['original_status'] = 'HOL'
            record['is_holiday'] = True
            record['holiday_name'] = f'{date.strftime("%A")} (Weekend)'
            return record
        
        # Get shift information with priority logic
        shift_info = self._get_shift_for_date(date, employee, roster_data)
        record.update({
            'shift': shift_info['shift'],
            'shift_name': shift_info['shift'].name if shift_info['shift'] else 'No Shift',
            'shift_source': shift_info['source'],
            'shift_start_time': shift_info['start_time'],
            'shift_end_time': shift_info['end_time'],
            'roster_info': shift_info.get('roster_info', 'No roster assignment'),
        })
        
        if shift_info['source'] in ['RosterDay', 'RosterAssignment']:
            record['is_roster_day'] = True
        
        # Process ZK logs for this date
        daily_zk_logs = zk_logs.filter(timestamp__date=date)
        if daily_zk_logs.exists():
            self._process_zk_logs_for_day(record, daily_zk_logs, employee, shift_info)
        
        return record
    
    def _process_zk_logs_for_day(self, record, daily_logs, employee, shift_info):
        """Process ZK logs for a specific day with unified logic."""
        if not daily_logs.exists():
            return
        
        sorted_logs = sorted(daily_logs, key=lambda x: x.timestamp)
        first_log = sorted_logs[0]
        last_log = sorted_logs[-1]
        
        record['in_time'] = first_log.timestamp
        record['total_logs'] = len(sorted_logs)
        
        if len(sorted_logs) > 1:
            record['out_time'] = last_log.timestamp
        else:
            record['out_time'] = None
        
        # Calculate attendance metrics with unified logic
        if record['shift'] and record['shift_start_time'] and record['shift_end_time']:
            self._calculate_unified_attendance_metrics(record, employee, shift_info)
        else:
            # Basic calculation without shift
            record['status'] = 'PRE'
            record['original_status'] = 'PRE'
            if record['out_time']:
                duration = record['out_time'] - record['in_time']
                working_hours = duration.total_seconds() / 3600
                # Deduct break time (assume 1 hour)
                working_hours = max(0, working_hours - 1)
                record['working_hours'] = round(working_hours, 2)
    
    def _calculate_unified_attendance_metrics(self, record, employee, shift_info):
        """Calculate detailed attendance metrics with unified logic."""
        shift = record['shift']
        date = record['date']
        in_time = record['in_time']
        out_time = record['out_time']
        
        shift_start_time = record['shift_start_time']
        shift_end_time = record['shift_end_time']
        
        # Use employee-specific grace minutes if available, otherwise use form setting
        grace_minutes = self.grace_minutes
        if employee.overtime_grace_minutes is not None:
            grace_minutes = employee.overtime_grace_minutes
        
        # Use employee-specific overtime settings if available
        overtime_start_after = self.overtime_start_after
        if employee.overtime_grace_minutes is not None:
            overtime_start_after = employee.overtime_grace_minutes
        
        # Create expected shift datetime objects
        expected_start = timezone.datetime.combine(date, shift_start_time)
        expected_start = timezone.make_aware(expected_start, timezone.get_default_timezone())
        
        expected_end = timezone.datetime.combine(date, shift_end_time)
        expected_end = timezone.make_aware(expected_end, timezone.get_default_timezone())
        
        # Handle overnight shifts
        if shift_end_time < shift_start_time:
            expected_end += timedelta(days=1)
        
        # Check for late arrival
        late_threshold = expected_start + timedelta(minutes=grace_minutes)
        if in_time > late_threshold:
            late_duration = in_time - expected_start
            record['late_minutes'] = round(late_duration.total_seconds() / 60)
            record['status'] = 'LAT'
            record['original_status'] = 'LAT'
        else:
            record['status'] = 'PRE'
            record['original_status'] = 'PRE'
        
        # Calculate working hours
        if out_time:
            total_duration = out_time - in_time
            total_hours = total_duration.total_seconds() / 3600
            
            # Deduct break time (use shift break time or default 1 hour)
            break_hours = (getattr(shift, 'break_time', 60) or 60) / 60
            working_hours = total_hours - break_hours
            record['working_hours'] = max(0, round(working_hours, 2))
        else:
            record['working_hours'] = 0
        
        # Check for early departure
        if out_time:
            early_threshold = expected_end - timedelta(minutes=self.early_out_threshold)
            if out_time < early_threshold:
                early_duration = expected_end - out_time
                record['early_out_minutes'] = round(early_duration.total_seconds() / 60)
        
        # Calculate overtime
        if out_time:
            # Use employee's expected work hours to determine overtime start
            expected_work_end = expected_start + timedelta(hours=employee.expected_work_hours)
            overtime_threshold = expected_work_end + timedelta(minutes=overtime_start_after)
            
            if out_time > overtime_threshold:
                overtime_duration = out_time - overtime_threshold
                overtime_minutes = overtime_duration.total_seconds() / 60
                
                # Apply minimum overtime threshold
                if overtime_minutes >= self.minimum_overtime_minutes:
                    record['overtime_hours'] = round(overtime_minutes / 60, 2)
        
        # Determine final status based on working hours
        half_day_threshold = employee.expected_work_hours / 2
        if record['working_hours'] > 0:
            if record['working_hours'] < half_day_threshold:
                record['status'] = 'HAL'
                if record['original_status'] not in ['HAL']:
                    record['original_status'] = 'HAL'
    
    def _get_shift_for_date(self, date, employee, roster_data):
        """Get shift information with priority logic: RosterDay > RosterAssignment > Default."""
        
        # Priority 1: Check RosterDay for specific date
        if 'days' in roster_data and date in roster_data['days']:
            roster_day = roster_data['days'][date]
            if roster_day.shift:
                return {
                    'shift': roster_day.shift,
                    'source': 'RosterDay',
                    'start_time': roster_day.shift.start_time,
                    'end_time': roster_day.shift.end_time,
                    'roster_info': f"Roster Day: {roster_day.roster_assignment.roster.name}",
                }
        
        # Priority 2: Check RosterAssignment for date range
        if 'assignments' in roster_data and date in roster_data['assignments']:
            roster_assignment = roster_data['assignments'][date]
            if roster_assignment.shift:
                return {
                    'shift': roster_assignment.shift,
                    'source': 'RosterAssignment',
                    'start_time': roster_assignment.shift.start_time,
                    'end_time': roster_assignment.shift.end_time,
                    'roster_info': f"Roster Assignment: {roster_assignment.roster.name}",
                }
            elif employee.default_shift:
                return {
                    'shift': employee.default_shift,
                    'source': 'RosterAssignment',
                    'start_time': employee.default_shift.start_time,
                    'end_time': employee.default_shift.end_time,
                    'roster_info': f"Roster Assignment (Default Shift): {roster_assignment.roster.name}",
                }
        
        # Priority 3: Use employee's default shift
        if employee.default_shift:
            return {
                'shift': employee.default_shift,
                'source': 'Default',
                'start_time': employee.default_shift.start_time,
                'end_time': employee.default_shift.end_time,
                'roster_info': "Employee Default Shift",
            }
        
        # No shift found
        return {
            'shift': None,
            'source': 'None',
            'start_time': None,
            'end_time': None,
            'roster_info': "No Shift Assigned",
        }
    
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
    
    def _generate_summary_statistics(self, daily_records, employee, start_date, end_date):
        """Generate comprehensive attendance summary with unified logic."""
        summary = {
            'total_days': len(daily_records),
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
            'late_absent_threshold': self.late_to_absent_days,
            'converted_absents': 0,
            'original_late_days': 0,
            'total_early_out_minutes': 0,
            'early_out_days': 0,
        }
        
        max_consecutive = 0
        current_consecutive = 0
        
        for record in daily_records:
            status = record['status']
            original_status = record.get('original_status', status)
            
            if original_status == 'LAT':
                summary['original_late_days'] += 1
            
            if record.get('converted_from_late', False):
                summary['converted_absents'] += 1
            
            if status == 'PRE':
                summary['present_days'] += 1
                current_consecutive = 0
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
            summary['total_early_out_minutes'] += record['early_out_minutes']
            
            if record['is_roster_day']:
                summary['total_roster_days'] += 1
            if record['overtime_hours'] > 0:
                summary['overtime_days'] += 1
            if record['early_out_minutes'] > 0:
                summary['early_out_days'] += 1
        
        summary['max_consecutive_absences'] = max_consecutive
        
        # Calculate percentages and averages
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
        
        return summary
