import logging
from datetime import timedelta, datetime
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.db.models import Q, Sum, Avg
from django.http import JsonResponse, HttpResponse
import json
import csv
import calendar

from Hrm.models import *
from .unified_attendance_processor import UnifiedAttendanceProcessor

logger = logging.getLogger(__name__)

class PayslipReportForm(forms.Form):
    """Form for generating payslip reports."""
    
    # Month and Year Selection
    year = forms.IntegerField(
        label=_("Year"),
        min_value=2020,
        max_value=2030,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Select the year for payslip generation.")
    )
    
    month = forms.ChoiceField(
        label=_("Month"),
        choices=[
            (1, _('January')), (2, _('February')), (3, _('March')),
            (4, _('April')), (5, _('May')), (6, _('June')),
            (7, _('July')), (8, _('August')), (9, _('September')),
            (10, _('October')), (11, _('November')), (12, _('December'))
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Select the month for payslip generation.")
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
    
    # Payslip Options
    include_salary_breakdown = forms.BooleanField(
        label=_("Include Salary Breakdown"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include detailed breakdown of earnings and deductions.")
    )
    
    include_attendance_summary = forms.BooleanField(
        label=_("Include Attendance Summary"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include attendance statistics in payslip.")
    )
    
    include_overtime_details = forms.BooleanField(
        label=_("Include Overtime Details"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include overtime hours and amount details.")
    )
    
    include_bonus_details = forms.BooleanField(
        label=_("Include Bonus Details"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include bonus amounts if applicable.")
    )
    
    include_advance_deductions = forms.BooleanField(
        label=_("Include Advance Deductions"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include advance salary deductions.")
    )
    
    show_year_to_date = forms.BooleanField(
        label=_("Show Year-to-Date Totals"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include year-to-date earnings and deductions.")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current year and month as default
        now = timezone.now()
        self.fields['year'].initial = now.year
        self.fields['month'].initial = now.month

class PayslipReportView(LoginRequiredMixin, View):
    """View for generating payslip reports."""
    template_name = 'report/hrm/payslip_report.html'
    
    def get(self, request, *args, **kwargs):
        form = PayslipReportForm()
        context_data = self._get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        # Handle export request
        if 'export' in request.POST:
            return self._handle_export(request)
        
        form = PayslipReportForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                report_data = self._generate_payslip_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'payslip_data': report_data['payslip_data'],
                    'month_info': report_data['month_info'],
                    'overall_statistics': report_data['overall_statistics'],
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, _("Payslip report generated successfully for {} {}.").format(
                    calendar.month_name[int(form.cleaned_data['month'])], form.cleaned_data['year']))
                
            except Exception as e:
                logger.error(f"Error generating payslip report: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'page_title': _("Payslip Report"),
            'report_generated': False,
        }
    
    def _generate_payslip_report(self, form_data):
        """Generate payslip report using UnifiedAttendanceProcessor."""
        year = int(form_data['year'])
        month = int(form_data['month'])
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        
        # Get salary month
        try:
            salary_month = SalaryMonth.objects.get(year=year, month=month)
        except SalaryMonth.DoesNotExist:
            raise ValueError(_("Salary month not found for {} {}").format(
                calendar.month_name[month], year))
        
        # Get employee salaries for the month
        employee_salaries = EmployeeSalary.objects.filter(
            salary_month=salary_month,
            employee__in=employees
        ).select_related('employee', 'salary_month').prefetch_related('details')
        
        # Get additional data if requested
        bonus_data = {}
        advance_data = {}
        attendance_data = {}
        ytd_data = {}
        
        if form_data.get('include_bonus_details', False):
            bonus_data = self._get_bonus_data(employees, year, month)
        
        if form_data.get('include_advance_deductions', False):
            advance_data = self._get_advance_data(employees, year, month)
        
        if form_data.get('include_attendance_summary', False):
            attendance_data = self._get_attendance_data(employees, year, month, form_data)
        
        if form_data.get('show_year_to_date', False):
            ytd_data = self._get_ytd_data(employees, year, month)
        
        # Process payslip data
        payslip_data = []
        overall_statistics = {
            'total_employees': len(employees),
            'total_gross_salary': 0,
            'total_net_salary': 0,
            'total_deductions': 0,
            'total_overtime_amount': 0,
            'total_bonus_amount': 0,
            'average_salary': 0,
            'highest_salary': 0,
            'lowest_salary': float('inf'),
            'employees_with_overtime': 0,
            'employees_with_bonus': 0,
        }
        
        for emp_salary in employee_salaries:
            employee = emp_salary.employee
            
            # Get salary breakdown
            salary_breakdown = self._get_salary_breakdown(emp_salary, form_data)
            
            # Ensure all keys are present, even if the values are None or empty lists
            payslip_record = {
                'employee': employee,
                'employee_id': employee.employee_id,
                'employee_name': employee.get_full_name(),
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'joining_date': employee.joining_date,
                'salary_month': salary_month,
                'basic_salary': emp_salary.basic_salary,
                'gross_salary': emp_salary.gross_salary,
                'total_earnings': emp_salary.total_earnings,
                'total_deductions': emp_salary.total_deductions,
                'net_salary': emp_salary.net_salary,
                'working_days': emp_salary.working_days,
                'present_days': emp_salary.present_days,
                'absent_days': emp_salary.absent_days,
                'leave_days': emp_salary.leave_days,
                'overtime_hours': emp_salary.overtime_hours,
                'overtime_amount': emp_salary.overtime_amount,
                'salary_breakdown': salary_breakdown,
                'bonus_details': bonus_data.get(employee.id, []),
                'advance_details': advance_data.get(employee.id, []),
                'attendance_summary': attendance_data.get(employee.id, {}),
                'ytd_totals': ytd_data.get(employee.id, {}),
                'has_overtime': emp_salary.overtime_amount > 0,
                'has_bonus': len(bonus_data.get(employee.id, [])) > 0,
            }
            
            payslip_data.append(payslip_record)
            
            # Update overall statistics
            overall_statistics['total_gross_salary'] += emp_salary.gross_salary
            overall_statistics['total_net_salary'] += emp_salary.net_salary
            overall_statistics['total_deductions'] += emp_salary.total_deductions
            overall_statistics['total_overtime_amount'] += emp_salary.overtime_amount
            overall_statistics['total_bonus_amount'] += sum(b['amount'] for b in bonus_data.get(employee.id, []))
            
            if emp_salary.overtime_amount > 0:
                overall_statistics['employees_with_overtime'] += 1
            
            if len(bonus_data.get(employee.id, [])) > 0:
                overall_statistics['employees_with_bonus'] += 1
            
            overall_statistics['highest_salary'] = max(overall_statistics['highest_salary'], emp_salary.net_salary)
            overall_statistics['lowest_salary'] = min(overall_statistics['lowest_salary'], emp_salary.net_salary)
        
        # Calculate averages
        if payslip_data:
            overall_statistics['average_salary'] = overall_statistics['total_net_salary'] / len(payslip_data)
        
        if overall_statistics['lowest_salary'] == float('inf'):
            overall_statistics['lowest_salary'] = 0
        
        # Month information
        month_info = {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'salary_month': salary_month,
            'is_generated': salary_month.is_generated,
            'is_paid': salary_month.is_paid,
            'generated_date': salary_month.generated_date,
            'payment_date': salary_month.payment_date,
        }
        
        return {
            'payslip_data': payslip_data,
            'month_info': month_info,
            'overall_statistics': overall_statistics,
        }
    
    def _get_filtered_employees(self, form_data):
        """Get employees based on filter criteria."""
        employee_filter = form_data.get('employee_filter', 'all')
        
        queryset = Employee.objects.filter(is_active=True).select_related(
            'department', 'designation'
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
    
    def _get_salary_breakdown(self, emp_salary, form_data):
        """Get detailed salary breakdown."""
        if not form_data.get('include_salary_breakdown', False):
            return {'earnings': [], 'deductions': []}
        
        breakdown = {'earnings': [], 'deductions': []}
        
        for detail in emp_salary.details.all():
            component_data = {
                'name': detail.component.name,
                'code': detail.component.code,
                'amount': detail.amount,
                'is_taxable': detail.component.is_taxable,
            }
            
            if detail.component.component_type == 'EARN':
                breakdown['earnings'].append(component_data)
            else:
                breakdown['deductions'].append(component_data)
        
        return breakdown
    
    def _get_bonus_data(self, employees, year, month):
        """Get bonus data for employees."""
        bonus_data = {}
        
        try:
            bonus_months = BonusMonth.objects.filter(year=year, month=month)
            employee_bonuses = EmployeeBonus.objects.filter(
                bonus_month__in=bonus_months,
                employee__in=employees
            ).select_related('bonus_month__bonus_setup')
            
            for bonus in employee_bonuses:
                if bonus.employee.id not in bonus_data:
                    bonus_data[bonus.employee.id] = []
                
                bonus_data[bonus.employee.id].append({
                    'name': bonus.bonus_month.bonus_setup.name,
                    'amount': bonus.amount,
                    'remarks': bonus.remarks,
                })
        except Exception as e:
            logger.warning(f"Could not fetch bonus data: {str(e)}")
        
        return bonus_data
    
    def _get_advance_data(self, employees, year, month):
        """Get advance deduction data for employees."""
        advance_data = {}
        
        try:
            # Get advance installments for the month
            start_date = datetime(year, month, 1).date()
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day).date()
            
            installments = AdvanceInstallment.objects.filter(
                advance__employee__in=employees,
                due_date__gte=start_date,
                due_date__lte=end_date,
                is_paid=True
            ).select_related('advance__advance_setup')
            
            for installment in installments:
                employee_id = installment.advance.employee.id
                if employee_id not in advance_data:
                    advance_data[employee_id] = []
                
                advance_data[employee_id].append({
                    'setup_name': installment.advance.advance_setup.name,
                    'installment_number': installment.installment_number,
                    'amount': installment.amount,
                    'due_date': installment.due_date,
                    'payment_date': installment.payment_date,
                })
        except Exception as e:
            logger.warning(f"Could not fetch advance data: {str(e)}")
        
        return advance_data
    
    def _get_attendance_data(self, employees, year, month, form_data):
        """Get attendance summary data using UnifiedAttendanceProcessor."""
        attendance_data = {}
        
        try:
            start_date = datetime(year, month, 1).date()
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day).date()
            
            # Get holidays for the month
            holidays = Holiday.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            )
            
            # Initialize processor
            processor = UnifiedAttendanceProcessor(form_data)
            
            for employee in employees:
                # Get ZK logs for this employee
                zk_logs = ZKAttendanceLog.objects.filter(
                    user_id=employee.employee_id,
                    timestamp__date__gte=start_date,
                    timestamp__date__lte=end_date
                ).order_by('timestamp')
                
                # Get leave applications
                leave_applications = LeaveApplication.objects.filter(
                    employee=employee,
                    status='APP',
                    start_date__lte=end_date,
                    end_date__gte=start_date
                )
                
                # Process attendance
                attendance_result = processor.process_employee_attendance(
                    employee, start_date, end_date, zk_logs,
                    holidays, leave_applications, {}
                )
                
                attendance_data[employee.id] = attendance_result.get('summary_stats', {})
        
        except Exception as e:
            logger.warning(f"Could not fetch attendance data: {str(e)}")
        
        return attendance_data
    
    def _get_ytd_data(self, employees, year, month):
        """Get year-to-date totals."""
        ytd_data = {}
        
        try:
            ytd_salaries = EmployeeSalary.objects.filter(
                employee__in=employees,
                salary_month__year=year,
                salary_month__month__lte=month
            ).values('employee').annotate(
                ytd_gross=Sum('gross_salary'),
                ytd_net=Sum('net_salary'),
                ytd_deductions=Sum('total_deductions'),
                ytd_overtime=Sum('overtime_amount')
            )
            
            for ytd in ytd_salaries:
                ytd_data[ytd['employee']] = {
                    'ytd_gross_salary': ytd['ytd_gross'] or 0,
                    'ytd_net_salary': ytd['ytd_net'] or 0,
                    'ytd_deductions': ytd['ytd_deductions'] or 0,
                    'ytd_overtime': ytd['ytd_overtime'] or 0,
                }
        except Exception as e:
            logger.warning(f"Could not fetch YTD data: {str(e)}")
        
        return ytd_data
    
    def _handle_export(self, request):
        """Handle CSV export of payslip report."""
        form = PayslipReportForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please fix form errors before exporting."))
            return self.post(request)
        
        try:
            report_data = self._generate_payslip_report(form.cleaned_data)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="payslip_report_{form.cleaned_data["year"]}_{form.cleaned_data["month"]:02d}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Employee ID', 'Employee Name', 'Department', 'Designation',
                'Basic Salary', 'Gross Salary', 'Total Deductions', 'Net Salary',
                'Working Days', 'Present Days', 'Overtime Hours', 'Overtime Amount'
            ])
            
            for payslip in report_data['payslip_data']:
                writer.writerow([
                    payslip['employee_id'],
                    payslip['employee_name'],
                    payslip['department'],
                    payslip['designation'],
                    payslip['basic_salary'],
                    payslip['gross_salary'],
                    payslip['total_deductions'],
                    payslip['net_salary'],
                    payslip['working_days'],
                    payslip['present_days'],
                    payslip['overtime_hours'],
                    payslip['overtime_amount'],
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting payslip report: {str(e)}")
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)
