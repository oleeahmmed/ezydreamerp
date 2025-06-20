import logging
from datetime import datetime, timedelta
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from ..models import ZKAttendanceLog, Employee, Holiday, LeaveApplication, Shift

logger = logging.getLogger(__name__)

# Form Definition
class AdvancedEmployeeAttendanceReportForm(forms.Form):
    """Advanced form for generating employee attendance report."""
    
    WEEKLY_HOLIDAY_CHOICES = [
        ('FRIDAY', _('Friday')),
        ('SATURDAY', _('Saturday')),
        ('SUNDAY', _('Sunday')),
        ('NONE', _('No Weekly Holiday')),
    ]

    start_date = forms.DateField(
        label=_("Start Date"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Leave blank to include records from 30 days ago.")
    )
    end_date = forms.DateField(
        label=_("End Date"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Leave blank to include today.")
    )
    employee_id = forms.CharField(
        label=_("Employee ID"),
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., E001'}),
        help_text=_("Enter the employee's unique ID.")
    )
    weekly_holiday = forms.ChoiceField(
        label=_("Weekly Holiday"),
        choices=WEEKLY_HOLIDAY_CHOICES,
        initial='FRIDAY',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Select the weekly holiday.")
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        employee_id = cleaned_data.get('employee_id')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_("Start date cannot be later than end date."))

        if employee_id:
            try:
                Employee.objects.get(employee_id=employee_id)
            except Employee.DoesNotExist:
                raise forms.ValidationError(_("Invalid Employee ID."))

        return cleaned_data

# View Definition
class EmployeeDetailedAttendanceReportView(LoginRequiredMixin, View):
    """View to generate a detailed attendance report for an employee."""
    template_name = 'report/hrm/employee_detailed_attendance_report.html'

    def get(self, request, *args, **kwargs):
        """Handle GET request to display the form."""
        form = AdvancedEmployeeAttendanceReportForm()
        context = self._get_context_data(form=form, report_generated=False)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Handle POST request to process the form and generate the report."""
        form = AdvancedEmployeeAttendanceReportForm(request.POST)
        context = self._get_context_data(form=form, report_generated=False)
        
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            employee_id = form.cleaned_data.get('employee_id')
            weekly_holiday = form.cleaned_data.get('weekly_holiday')
            
            try:
                employee = Employee.objects.get(employee_id=employee_id)
                report_data = self._generate_attendance_report(
                    employee, start_date, end_date, weekly_holiday
                )
                context.update({
                    'report_generated': True,
                    'attendance_data': report_data,
                    'employee': employee,
                    'start_date': start_date,
                    'end_date': end_date,
                })
                messages.success(request, _("Attendance report generated successfully for {}.").format(employee.get_full_name()))
            except Exception as e:
                logger.error(f"Error generating attendance report for employee {employee_id}: {str(e)}")
                messages.error(request, f"Error generating report: {str(e)}")
        
        return render(request, self.template_name, context)

    def _get_context_data(self, form, report_generated):
        """Return context data for the template."""
        return {
            'title': _("Employee Attendance Report"),
            'subtitle': _("Generate detailed attendance report for an employee"),
            'form': form,
            'report_generated': report_generated,
            'page_title': _("Attendance Report"),
        }

    def _generate_attendance_report(self, employee, start_date=None, end_date=None, 
                                  weekly_holiday='FRIDAY'):
        """Generate attendance report data."""
        MINIMUM_REQUIRED_HOURS = 8  # Configurable minimum hours for Present
        HALF_DAY_THRESHOLD = 4     # Configurable threshold for Half Day (hours)
        DEFAULT_GRACE_TIME = 15    # Default grace time in minutes if no shift
        DEFAULT_BREAK_TIME = 0     # Default break time in minutes if no shift

        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        # Fetch attendance logs for the date range
        attendance_logs = ZKAttendanceLog.objects.filter(
            user_id=employee.employee_id,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        ).order_by('timestamp')

        # Group logs by date
        attendance_dict = {}
        for log in attendance_logs:
            date_key = log.timestamp.date()
            if date_key not in attendance_dict:
                attendance_dict[date_key] = []
            attendance_dict[date_key].append(log)

        holidays = Holiday.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).select_related()

        leaves = LeaveApplication.objects.filter(
            employee=employee,
            status='APP',
            start_date__lte=end_date,
            end_date__gte=start_date
        ).select_related('leave_type')

        report_data = []
        current_date = start_date
        
        while current_date <= end_date:
            status = 'ABS'
            in_time = None
            out_time = None
            shift = None
            workplace = None
            remarks = ''
            working_hours = 0
            overtime_hours = 0

            # Check weekly holiday (default Friday)
            is_holiday = False
            weekday = current_date.weekday()
            if weekly_holiday == 'FRIDAY' and weekday == 4:
                is_holiday = True
                status = 'HOL'
                remarks = 'Friday (Weekly Holiday)'
            elif weekly_holiday == 'SATURDAY' and weekday == 5:
                is_holiday = True
                status = 'HOL'
                remarks = 'Saturday (Weekly Holiday)'
            elif weekly_holiday == 'SUNDAY' and weekday == 6:
                is_holiday = True
                status = 'HOL'
                remarks = 'Sunday (Weekly Holiday)'

            # Check public holidays
            holiday = next((h for h in holidays if h.date == current_date), None)
            if holiday:
                is_holiday = True
                status = 'HOL'
                remarks = holiday.name

            # Check for leaves
            if not is_holiday:
                for leave in leaves:
                    if leave.start_date <= current_date <= leave.end_date:
                        status = 'LEA'
                        remarks = f'{leave.leave_type.name} Leave'
                        break

            # Get shift from Employee.default_shift
            shift = employee.default_shift
            if not shift:
                remarks = 'No Shift Assigned'

            # Process attendance logs
            if current_date in attendance_dict:
                logs = attendance_dict[current_date]
                # First record as in_time, last record as out_time
                in_time = logs[0].timestamp
                out_time = logs[-1].timestamp
                
                if status not in ['HOL', 'LEA']:
                    # Calculate working hours
                    if in_time and out_time:
                        duration = out_time - in_time
                        working_hours = round(duration.total_seconds() / 3600, 2)

                    # Check for Half Day
                    if working_hours <= HALF_DAY_THRESHOLD:
                        status = 'HAL'
                        remarks = 'Half Day'
                    else:
                        # Check for Present
                        if shift:
                            try:
                                shift_duration_hours = float(shift.duration.split('h')[0]) + float(shift.duration.split('h')[1].split('m')[0]) / 60
                            except (ValueError, IndexError):
                                shift_duration_hours = MINIMUM_REQUIRED_HOURS
                            if working_hours >= min(MINIMUM_REQUIRED_HOURS, shift_duration_hours):
                                status = 'PRE'
                            else:
                                status = 'PRE'  # Still present but might have early out
                        else:
                            if working_hours >= MINIMUM_REQUIRED_HOURS:
                                status = 'PRE'
                            else:
                                status = 'PRE'  # Still present but might have early out
                                remarks = 'No Shift Assigned' if not remarks else remarks

                        # Check for Late
                        grace_time = shift.grace_time if shift else DEFAULT_GRACE_TIME
                        if shift and in_time:
                            expected_start = timezone.datetime.combine(current_date, shift.start_time)
                            expected_start = timezone.make_aware(expected_start, timezone.get_default_timezone())
                            if in_time > expected_start + timedelta(minutes=grace_time):
                                status = 'LAT'
                                remarks = 'Late Arrival' if not remarks else f'{remarks}, Late Arrival'

                        # Check for Early Out
                        break_time = shift.break_time if shift else DEFAULT_BREAK_TIME
                        if shift and out_time:
                            expected_end = timezone.datetime.combine(current_date, shift.end_time)
                            expected_end = timezone.make_aware(expected_end, timezone.get_default_timezone())
                            expected_end -= timedelta(minutes=break_time)
                            if out_time < expected_end:
                                remarks = 'Early Departure' if not remarks else f'{remarks}, Early Departure'

                        # Check for Overtime
                        if shift and out_time:
                            if out_time > expected_end:
                                overtime_duration = out_time - expected_end
                                overtime_hours = round(overtime_duration.total_seconds() / 3600, 2)
                                remarks = f'Overtime {overtime_hours}h' if not remarks else f'{remarks}, Overtime {overtime_hours}h'

            report_data.append({
                'date': current_date,
                'status': status,
                'in_time': in_time.strftime('%H:%M:%S') if in_time else '-',
                'out_time': out_time.strftime('%H:%M:%S') if out_time else '-',
                'working_hours': working_hours,
                'shift': shift.name if shift else '-',
                'workplace': '-',
                'remarks': remarks,
            })

            current_date += timedelta(days=1)

        return report_data