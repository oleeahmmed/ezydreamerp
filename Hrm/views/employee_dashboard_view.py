from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch, Sum, Count
from django.utils import timezone
import datetime
from ..models import (
    Employee, LeaveBalance, LeaveApplication, ShortLeaveApplication,
    Attendance, OvertimeRecord, EmployeeSalary, EmployeeBonus,
    EmployeeAdvance, EmployeeProvidentFund, EmployeeLetter
)

class EmployeeDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'employee/employee_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the employee profile for the logged-in user
        employee = get_object_or_404(Employee, user=self.request.user)
        
        # Current date and time
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        
        # Get leave balances for the current year
        leave_balances = employee.leave_balances.filter(
            year=current_year
        ).select_related('leave_type')

        # Precompute percentage without using template filters
        leave_balances_with_percentage = []
        for balance in leave_balances:
            try:
                percentage = (balance.available_days / balance.total_days) * 100 if balance.total_days else 0
            except ZeroDivisionError:
                percentage = 0
            leave_balances_with_percentage.append({
                'name': balance.leave_type.name,
                'available_days': balance.available_days,
                'total_days': balance.total_days,
                'used_days': balance.used_days,
                'pending_days': balance.pending_days,
                'percentage': round(percentage, 0),
            })
        
        # Get recent leave applications
        recent_leave_applications = employee.leave_applications.filter(
            start_date__year=current_year
        ).select_related('leave_type', 'approved_by').order_by('-start_date')[:5]
        
        # Get recent short leave applications
        recent_short_leaves = employee.short_leave_applications.filter(
            date__year=current_year
        ).select_related('approved_by').order_by('-date')[:5]
        
        # Get attendance records for the current month
        current_month_attendance = employee.attendances.filter(
            date__year=current_year,
            date__month=current_month
        ).order_by('-date')
        
        # Calculate attendance statistics
        attendance_stats = {
            'present': current_month_attendance.filter(status='PRE').count(),
            'absent': current_month_attendance.filter(status='ABS').count(),
            'late': current_month_attendance.filter(status='LAT').count(),
            'leave': current_month_attendance.filter(status='LEA').count(),
            'half_day': current_month_attendance.filter(status='HAL').count(),
            'total_working_days': current_month_attendance.exclude(
                status__in=['HOL', 'WEE']
            ).count(),
        }
        
        # Get recent overtime records
        recent_overtime = employee.overtime_records.filter(
            date__year=current_year
        ).select_related('approved_by').order_by('-date')[:5]
        
        # Get salary information
        recent_salaries = employee.salaries.select_related('salary_month').order_by(
            '-salary_month__year', '-salary_month__month'
        )[:3]
        
        # Get recent bonuses
        recent_bonuses = employee.bonuses.select_related('bonus_month__bonus_setup').order_by(
            '-bonus_month__year', '-bonus_month__month'
        )[:3]
        
        # Get active advances
        active_advances = employee.advances.filter(
            status__in=['APP', 'PAI']
        ).select_related('advance_setup', 'approved_by')
        
        # Get provident fund information if exists
        try:
            pf_info = employee.provident_fund
            pf_transactions = pf_info.transactions.order_by('-transaction_date')[:5]
        except:
            pf_info = None
            pf_transactions = []
        
        # Get recent letters
        recent_letters = employee.letters.select_related('template', 'issued_by').order_by('-issue_date')[:5]
        
        # Add all data to context
        context.update({
            'employee': employee,
            'leave_balances': leave_balances_with_percentage,
            'recent_leave_applications': recent_leave_applications,
            'recent_short_leaves': recent_short_leaves,
            'current_month_attendance': current_month_attendance,
            'attendance_stats': attendance_stats,
            'recent_overtime': recent_overtime,
            'recent_salaries': recent_salaries,
            'recent_bonuses': recent_bonuses,
            'active_advances': active_advances,
            'pf_info': pf_info,
            'pf_transactions': pf_transactions,
            'recent_letters': recent_letters,
            'current_year': current_year,
            'current_month': current_month,
            'current_month_name': now.strftime('%B'),
        })
        
        return context
