from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from Hrm.models import Attendance, Employee, Department, Designation, Shift, RosterDay, OvertimeRecord, Holiday
from Hrm.forms.attendance_report_forms import (
    DailyAttendanceReportForm, MonthlyAttendanceSummaryForm, MissingAttendanceReportForm,
    LateArrivalReportForm, EarlyDepartureReportForm, AbsentReportForm, OvertimeReportForm,
    DailyAttendanceWithOvertimeForm, ShiftWiseAttendanceReportForm, RosterVsActualAttendanceForm,
    WeekendHolidayAttendanceForm
)
from config.views import GenericFilterView

class DailyAttendanceReportView(GenericFilterView):
    model = Attendance
    template_name = 'attendance/reports/daily_attendance_report.html'
    context_object_name = 'attendances'
    paginate_by = 10
    filter_form_class = DailyAttendanceReportForm
    permission_required = 'Hrm.view_attendance'

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        if filters.get('department'):
            queryset = queryset.filter(employee__department=filters['department'])
        if filters.get('designation'):
            queryset = queryset.filter(employee__designation=filters['designation'])
        if filters.get('shift'):
            queryset = queryset.filter(roster_day__shift=filters['shift'])
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = 'Daily Attendance Report'
        context['report_subtitle'] = 'Daily attendance status of employees'
        return context

class MonthlyAttendanceSummaryView(GenericFilterView):
    model = Attendance
    template_name = 'attendance/reports/monthly_attendance_summary.html'
    context_object_name = ' summaries'
    paginate_by = 10
    filter_form_class = MonthlyAttendanceSummaryForm
    permission_required = 'Hrm.view_attendance'

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        year = filters.get('year')
        month = filters.get('month')
        employee = filters.get('employee')
        
        queryset = queryset.values('employee__id', 'employee__first_name', 'employee__last_name').annotate(
            total_working_days=Count('id'),
            present_days=Count('id', filter=Q(status='PRE')),
            absent_days=Count('id', filter=Q(status='ABS')),
            late_days=Count('id', filter=Q(status='LAT')),
            leave_days=Count('id', filter=Q(status='LEA')),
            holiday_days=Count('id', filter=Q(status='HOL')),
            weekend_days=Count('id', filter=Q(status='WEE')),
            half_days=Count('id', filter=Q(status='HAL'))
        )
        
        if year:
            queryset = queryset.filter(date__year=year)
        if month:
            queryset = queryset.filter(date__month=month)
        if employee:
            queryset = queryset.filter(employee=employee)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = 'Monthly Attendance Summary'
        context['report_subtitle'] = 'Summary of employee attendance for a month'
        return context

class MissingAttendanceReportView(GenericFilterView):
    model = Attendance
    template_name = 'attendance/reports/missing_attendance_report.html'
    context_object_name = 'attendances'
    paginate_by = 10
    filter_form_class = MissingAttendanceReportForm
    permission_required = 'Hrm.view_attendance'

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        queryset = queryset.filter(Q(check_in__isnull=True) | Q(check_out__isnull=True))
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = 'Missing Attendance Report'
        context['report_subtitle'] = 'Employees with missing check-in or check-out'
        return context

class LateArrivalReportView(GenericFilterView):
    model = Attendance
    template_name = 'attendance/reports/late_arrival_report.html'
    context_object_name = 'attendances'
    paginate_by = 10
    filter_form_class = LateArrivalReportForm
    permission_required = 'Hrm.view_attendance'

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        queryset = queryset.filter(late_minutes__gt=0, roster_day__shift__grace_time__lt=F('late_minutes'))
        if filters.get('shift'):
            queryset = queryset.filter(roster_day__shift=filters['shift'])
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = 'Late Arrival Report'
        context['report_subtitle'] = 'Employees who arrived late beyond grace time'
        return context

class EarlyDepartureReportView(GenericFilterView):
    model = Attendance
    template_name = 'attendance/reports/early_departure_report.html'
    context_object_name = 'attendances'
    paginate_by = 10
    filter_form_class = EarlyDepartureReportForm
    permission_required = 'Hrm.view_attendance'

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        queryset = queryset.filter(early_out_minutes__gt=0)
        if filters.get('shift'):
            queryset = queryset.filter(roster_day__shift=filters['shift'])
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = 'Early Departure Report'
        context['report_subtitle'] = 'Employees who left before shift end'
        return context

class AbsentReportView(GenericFilterView):
    model = Attendance
    template_name = 'attendance/reports/absent_report.html'
    context_object_name = 'attendances'
    paginate_by = 10
    filter_form_class = AbsentReportForm
    permission_required = 'Hrm.view_attendance'

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        queryset = queryset.filter(status='ABS')
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = 'Absent Report'
        context['report_subtitle'] = 'Employees who were absent on specific dates'
        return context

class OvertimeReportView(GenericFilterView):
    model = OvertimeRecord
    template_name = 'attendance/reports/overtime_report.html'
    context_object_name = 'overtimes'
    paginate_by = 10
    filter_form_class = OvertimeReportForm
    permission_required = 'Hrm.view_attendance'

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        queryset = queryset.filter(status='APP')
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
        if filters.get('department'):
            queryset = queryset.filter(employee__department=filters['department'])
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = 'Overtime Report'
        context['report_subtitle'] = 'Approved overtime hours and amounts'
        return context

class DailyAttendanceWithOvertimeView(GenericFilterView):
    model = Attendance
    template_name = 'attendance/reports/daily_attendance_with_overtime.html'
    context_object_name = 'attendances'
    paginate_by = 10
    filter_form_class = DailyAttendanceWithOvertimeForm
    permission_required = 'Hrm.view_attendance'

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = 'Daily Attendance with Overtime'
        context['report_subtitle'] = 'Daily attendance with overtime details'
        return context
class ShiftWiseAttendanceReportView(GenericFilterView):
    model = Attendance
    template_name = 'attendance/reports/shift_wise_attendance_report.html'
    context_object_name = 'attendances'
    paginate_by = 10
    filter_form_class = ShiftWiseAttendanceReportForm
    permission_required = 'Hrm.view_attendance'

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        if filters.get('shift'):
            queryset = queryset.filter(roster_day__shift=filters['shift'])
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = 'Shift-wise Attendance Report'
        context['report_subtitle'] = 'Attendance details by shift'
        return context

class RosterVsActualAttendanceView(GenericFilterView):
    model = Attendance
    template_name = 'attendance/reports/roster_vs_actual_attendance.html'
    context_object_name = 'attendances'
    paginate_by = 10
    filter_form_class = RosterVsActualAttendanceForm
    permission_required = 'Hrm.view_attendance'

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        queryset = queryset.select_related('roster_day__shift')
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = 'Roster vs Actual Attendance'
        context['report_subtitle'] = 'Comparison of rostered vs actual attendance'
        return context

class WeekendHolidayAttendanceView(GenericFilterView):
    model = Attendance
    template_name = 'attendance/reports/weekend_holiday_attendance.html'
    context_object_name = 'attendances'
    paginate_by = 10
    filter_form_class = WeekendHolidayAttendanceForm
    permission_required = 'Hrm.view_attendance'

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        queryset = queryset.filter(status__in=['PRE', 'LAT', 'HAL'])
        holiday_dates = Holiday.objects.filter(date__gte=filters.get('date_from'), date__lte=filters.get('date_to')).values_list('date', flat=True)
        queryset = queryset.filter(Q(date__week_day__in=[1, 7]) | Q(date__in=holiday_dates))
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_title'] = 'Weekend and Holiday Attendance'
        context['report_subtitle'] = 'Employees who worked on weekends or holidays'
        return context