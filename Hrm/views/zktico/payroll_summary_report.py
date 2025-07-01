import logging
from datetime import timedelta, datetime
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.db.models import Q, Sum, Avg, Count, Max, Min
from django.http import JsonResponse, HttpResponse
import json
import csv
import calendar

from Hrm.models import *
from .unified_attendance_processor import UnifiedAttendanceProcessor

logger = logging.getLogger(__name__)

class PayrollSummaryReportForm(forms.Form):
    """Form for generating payroll summary reports."""
    
    # Date Range Selection
    report_type = forms.ChoiceField(
        label=_("Report Type"),
        choices=[
            ('monthly', _('Monthly Summary')),
            ('quarterly', _('Quarterly Summary')),
            ('yearly', _('Yearly Summary')),
            ('custom', _('Custom Date Range')),
        ],
        initial='monthly',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Select the type of payroll summary report.")
    )
    
    year = forms.IntegerField(
        label=_("Year"),
        min_value=2020,
        max_value=2030,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text=_("Select the year for payroll summary.")
    )
    
    month = forms.ChoiceField(
        label=_("Month"),
        choices=[
            (1, _('January')), (2, _('February')), (3, _('March')),
            (4, _('April')), (5, _('May')), (6, _('June')),
            (7, _('July')), (8, _('August')), (9, _('September')),
            (10, _('October')), (11, _('November')), (12, _('December'))
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Select the month (for monthly reports).")
    )
    
    quarter = forms.ChoiceField(
        label=_("Quarter"),
        choices=[
            (1, _('Q1 (Jan-Mar)')),
            (2, _('Q2 (Apr-Jun)')),
            (3, _('Q3 (Jul-Sep)')),
            (4, _('Q4 (Oct-Dec)')),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Select the quarter (for quarterly reports).")
    )
    
    start_date = forms.DateField(
        label=_("Start Date"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("Start date for custom range.")
    )
    
    end_date = forms.DateField(
        label=_("End Date"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text=_("End date for custom range.")
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
    
    # Summary Options
    include_department_breakdown = forms.BooleanField(
        label=_("Include Department Breakdown"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include department-wise payroll breakdown.")
    )
    
    include_designation_breakdown = forms.BooleanField(
        label=_("Include Designation Breakdown"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include designation-wise payroll breakdown.")
    )
    
    include_overtime_analysis = forms.BooleanField(
        label=_("Include Overtime Analysis"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include overtime cost analysis.")
    )
    
    include_bonus_analysis = forms.BooleanField(
        label=_("Include Bonus Analysis"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include bonus distribution analysis.")
    )
    
    include_attendance_correlation = forms.BooleanField(
        label=_("Include Attendance Correlation"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Include attendance vs salary correlation.")
    )
    
    show_trends = forms.BooleanField(
        label=_("Show Trends"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_("Show payroll trends over time.")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current year and month as default
        now = timezone.now()
        self.fields['year'].initial = now.year
        self.fields['month'].initial = now.month

class PayrollSummaryReportView(LoginRequiredMixin, View):
    """View for generating payroll summary reports."""
    template_name = 'report/hrm/payroll_summary_report.html'
    
    def get(self, request, *args, **kwargs):
        form = PayrollSummaryReportForm()
        context_data = self._get_context_data(form)
        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        # Handle export request
        if 'export' in request.POST:
            return self._handle_export(request)
        
        form = PayrollSummaryReportForm(request.POST)
        context_data = self._get_context_data(form)

        if form.is_valid():
            try:
                report_data = self._generate_payroll_summary_report(form.cleaned_data)
                
                context_data.update({
                    'report_generated': True,
                    'summary_data': report_data['summary_data'],
                    'department_breakdown': report_data['department_breakdown'],
                    'designation_breakdown': report_data['designation_breakdown'],
                    'period_info': report_data['period_info'],
                    'overall_statistics': report_data['overall_statistics'],
                    'trends_data': report_data.get('trends_data', []),
                    'form_data': form.cleaned_data,
                })
                
                messages.success(request, _("Payroll summary report generated successfully for {}.").format(
                    report_data['period_info']['period_description']))
                
            except Exception as e:
                logger.error(f"Error generating payroll summary report: {str(e)}")
                messages.error(request, _("Failed to generate report: {}").format(str(e)))

        return render(request, self.template_name, context_data)
    
    def _get_context_data(self, form):
        """Get context data for template."""
        return {
            'form': form,
            'departments': Department.objects.all().order_by('name'),
            'designations': Designation.objects.all().order_by('name'),
            'page_title': _("Payroll Summary Report"),
            'report_generated': False,
        }
    
    def _generate_payroll_summary_report(self, form_data):
        """Generate payroll summary report using UnifiedAttendanceProcessor."""
        
        # Determine date range based on report type
        date_range = self._get_date_range(form_data)
        start_date, end_date = date_range['start_date'], date_range['end_date']
        
        # Get employees based on filter
        employees = self._get_filtered_employees(form_data)
        
        # Get salary months in the date range
        salary_months = SalaryMonth.objects.filter(
            year__gte=start_date.year,
            year__lte=end_date.year
        )
        
        if start_date.year == end_date.year:
            salary_months = salary_months.filter(
                month__gte=start_date.month,
                month__lte=end_date.month
            )
        
        # Get employee salaries for the period
        employee_salaries = EmployeeSalary.objects.filter(
            salary_month__in=salary_months,
            employee__in=employees
        ).select_related('employee', 'salary_month').prefetch_related('details')
        
        # Process summary data
        summary_data = self._process_summary_data(employee_salaries, form_data)
        
        # Generate breakdowns
        department_breakdown = []
        designation_breakdown = []
        
        if form_data.get('include_department_breakdown', False):
            department_breakdown = self._generate_department_breakdown(employee_salaries)
        
        if form_data.get('include_designation_breakdown', False):
            designation_breakdown = self._generate_designation_breakdown(employee_salaries)
        
        # Generate trends data
        trends_data = []
        if form_data.get('show_trends', False):
            trends_data = self._generate_trends_data(salary_months, employees)
        
        # Calculate overall statistics
        overall_statistics = self._calculate_overall_statistics(employee_salaries, employees)
        
        return {
            'summary_data': summary_data,
            'department_breakdown': department_breakdown,
            'designation_breakdown': designation_breakdown,
            'period_info': date_range,
            'overall_statistics': overall_statistics,
            'trends_data': trends_data,
        }
    
    def _get_date_range(self, form_data):
        """Get date range based on report type."""
        report_type = form_data['report_type']
        year = form_data['year']
        
        if report_type == 'monthly':
            month = int(form_data['month'])
            start_date = datetime(year, month, 1).date()
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day).date()
            period_description = f"{calendar.month_name[month]} {year}"
            
        elif report_type == 'quarterly':
            quarter = int(form_data['quarter'])
            start_month = (quarter - 1) * 3 + 1
            end_month = quarter * 3
            start_date = datetime(year, start_month, 1).date()
            last_day = calendar.monthrange(year, end_month)[1]
            end_date = datetime(year, end_month, last_day).date()
            period_description = f"Q{quarter} {year}"
            
        elif report_type == 'yearly':
            start_date = datetime(year, 1, 1).date()
            end_date = datetime(year, 12, 31).date()
            period_description = f"Year {year}"
            
        else:  # custom
            start_date = form_data['start_date']
            end_date = form_data['end_date']
            period_description = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'period_description': period_description,
            'report_type': report_type,
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
    
    def _process_summary_data(self, employee_salaries, form_data):
        """Process summary data for each employee."""
        summary_data = []
        
        # Group salaries by employee
        employee_salary_dict = {}
        for salary in employee_salaries:
            emp_id = salary.employee.id
            if emp_id not in employee_salary_dict:
                employee_salary_dict[emp_id] = {
                    'employee': salary.employee,
                    'salaries': []
                }
            employee_salary_dict[emp_id]['salaries'].append(salary)
        
        for emp_id, emp_data in employee_salary_dict.items():
            employee = emp_data['employee']
            salaries = emp_data['salaries']
            
            # Calculate totals
            total_gross = sum(s.gross_salary for s in salaries)
            total_net = sum(s.net_salary for s in salaries)
            total_deductions = sum(s.total_deductions for s in salaries)
            total_overtime = sum(s.overtime_amount for s in salaries)
            total_working_days = sum(s.working_days for s in salaries)
            total_present_days = sum(s.present_days for s in salaries)
            
            summary_record = {
                'employee': employee,
                'employee_id': employee.employee_id,
                'employee_name': employee.get_full_name(),
                'department': employee.department.name if employee.department else 'N/A',
                'designation': employee.designation.name if employee.designation else 'N/A',
                'total_months': len(salaries),
                'total_gross_salary': total_gross,
                'total_net_salary': total_net,
                'total_deductions': total_deductions,
                'total_overtime_amount': total_overtime,
                'average_monthly_salary': total_net / len(salaries) if salaries else 0,
                'total_working_days': total_working_days,
                'total_present_days': total_present_days,
                'attendance_percentage': (total_present_days / total_working_days * 100) if total_working_days > 0 else 0,
                'has_overtime': total_overtime > 0,
                'salary_details': salaries,
            }
            
            summary_data.append(summary_record)
        
        return summary_data
    
    def _generate_department_breakdown(self, employee_salaries):
        """Generate department-wise breakdown."""
        dept_data = {}
        
        for salary in employee_salaries:
            dept_name = salary.employee.department.name if salary.employee.department else 'No Department'
            
            if dept_name not in dept_data:
                dept_data[dept_name] = {
                    'department': dept_name,
                    'employee_count': set(),
                    'total_gross': 0,
                    'total_net': 0,
                    'total_deductions': 0,
                    'total_overtime': 0,
                    'salary_records': 0,
                }
            
            dept_data[dept_name]['employee_count'].add(salary.employee.id)
            dept_data[dept_name]['total_gross'] += salary.gross_salary
            dept_data[dept_name]['total_net'] += salary.net_salary
            dept_data[dept_name]['total_deductions'] += salary.total_deductions
            dept_data[dept_name]['total_overtime'] += salary.overtime_amount
            dept_data[dept_name]['salary_records'] += 1
        
        # Convert to list and calculate averages
        breakdown = []
        for dept_name, data in dept_data.items():
            employee_count = len(data['employee_count'])
            breakdown.append({
                'department': dept_name,
                'employee_count': employee_count,
                'total_gross_salary': data['total_gross'],
                'total_net_salary': data['total_net'],
                'total_deductions': data['total_deductions'],
                'total_overtime_amount': data['total_overtime'],
                'average_salary_per_employee': data['total_net'] / employee_count if employee_count > 0 else 0,
                'salary_records': data['salary_records'],
            })
        
        return sorted(breakdown, key=lambda x: x['total_net_salary'], reverse=True)
    
    def _generate_designation_breakdown(self, employee_salaries):
        """Generate designation-wise breakdown."""
        desig_data = {}
        
        for salary in employee_salaries:
            desig_name = salary.employee.designation.name if salary.employee.designation else 'No Designation'
            
            if desig_name not in desig_data:
                desig_data[desig_name] = {
                    'designation': desig_name,
                    'employee_count': set(),
                    'total_gross': 0,
                    'total_net': 0,
                    'total_deductions': 0,
                    'total_overtime': 0,
                    'salary_records': 0,
                }
            
            desig_data[desig_name]['employee_count'].add(salary.employee.id)
            desig_data[desig_name]['total_gross'] += salary.gross_salary
            desig_data[desig_name]['total_net'] += salary.net_salary
            desig_data[desig_name]['total_deductions'] += salary.total_deductions
            desig_data[desig_name]['total_overtime'] += salary.overtime_amount
            desig_data[desig_name]['salary_records'] += 1
        
        # Convert to list and calculate averages
        breakdown = []
        for desig_name, data in desig_data.items():
            employee_count = len(data['employee_count'])
            breakdown.append({
                'designation': desig_name,
                'employee_count': employee_count,
                'total_gross_salary': data['total_gross'],
                'total_net_salary': data['total_net'],
                'total_deductions': data['total_deductions'],
                'total_overtime_amount': data['total_overtime'],
                'average_salary_per_employee': data['total_net'] / employee_count if employee_count > 0 else 0,
                'salary_records': data['salary_records'],
            })
        
        return sorted(breakdown, key=lambda x: x['total_net_salary'], reverse=True)
    
    def _generate_trends_data(self, salary_months, employees):
        """Generate trends data over time."""
        trends_data = []
        
        for salary_month in salary_months.order_by('year', 'month'):
            month_salaries = EmployeeSalary.objects.filter(
                salary_month=salary_month,
                employee__in=employees
            ).aggregate(
                total_gross=Sum('gross_salary'),
                total_net=Sum('net_salary'),
                total_deductions=Sum('total_deductions'),
                total_overtime=Sum('overtime_amount'),
                employee_count=Count('employee', distinct=True),
                avg_salary=Avg('net_salary')
            )
            
            trends_data.append({
                'year': salary_month.year,
                'month': salary_month.month,
                'month_name': calendar.month_name[salary_month.month],
                'period': f"{calendar.month_name[salary_month.month]} {salary_month.year}",
                'total_gross_salary': month_salaries['total_gross'] or 0,
                'total_net_salary': month_salaries['total_net'] or 0,
                'total_deductions': month_salaries['total_deductions'] or 0,
                'total_overtime_amount': month_salaries['total_overtime'] or 0,
                'employee_count': month_salaries['employee_count'] or 0,
                'average_salary': month_salaries['avg_salary'] or 0,
            })
        
        return trends_data
    
    def _calculate_overall_statistics(self, employee_salaries, employees):
        """Calculate overall payroll statistics."""
        if not employee_salaries:
            return {
                'total_employees': 0,
                'total_salary_records': 0,
                'total_gross_salary': 0,
                'total_net_salary': 0,
                'total_deductions': 0,
                'total_overtime_amount': 0,
                'average_salary': 0,
                'highest_salary': 0,
                'lowest_salary': 0,
                'employees_with_overtime': 0,
                'total_payroll_cost': 0,
                'deduction_percentage': 0,
                'overtime_percentage': 0,
            }
        
        # Calculate aggregates
        aggregates = employee_salaries.aggregate(
            total_gross=Sum('gross_salary'),
            total_net=Sum('net_salary'),
            total_deductions=Sum('total_deductions'),
            total_overtime=Sum('overtime_amount'),
            avg_salary=Avg('net_salary'),
            max_salary=Max('net_salary'),
            min_salary=Min('net_salary'),
            employees_with_overtime=Count('employee', filter=Q(overtime_amount__gt=0), distinct=True)
        )
        
        unique_employees = len(set(salary.employee.id for salary in employee_salaries))
        
        statistics = {
            'total_employees': unique_employees,
            'total_salary_records': employee_salaries.count(),
            'total_gross_salary': aggregates['total_gross'] or 0,
            'total_net_salary': aggregates['total_net'] or 0,
            'total_deductions': aggregates['total_deductions'] or 0,
            'total_overtime_amount': aggregates['total_overtime'] or 0,
            'average_salary': aggregates['avg_salary'] or 0,
            'highest_salary': aggregates['max_salary'] or 0,
            'lowest_salary': aggregates['min_salary'] or 0,
            'employees_with_overtime': aggregates['employees_with_overtime'] or 0,
            'total_payroll_cost': aggregates['total_net'] or 0,
        }
        
        # Calculate percentages
        if statistics['total_gross_salary'] > 0:
            statistics['deduction_percentage'] = round(
                (statistics['total_deductions'] / statistics['total_gross_salary']) * 100, 2
            )
            statistics['overtime_percentage'] = round(
                (statistics['total_overtime_amount'] / statistics['total_gross_salary']) * 100, 2
            )
        else:
            statistics['deduction_percentage'] = 0
            statistics['overtime_percentage'] = 0
        
        return statistics
    
    def _handle_export(self, request):
        """Handle CSV export of payroll summary report."""
        form = PayrollSummaryReportForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Please fix form errors before exporting."))
            return self.post(request)
        
        try:
            report_data = self._generate_payroll_summary_report(form.cleaned_data)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="payroll_summary_report_{report_data["period_info"]["period_description"].replace(" ", "_")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Employee ID', 'Employee Name', 'Department', 'Designation',
                'Total Months', 'Total Gross Salary', 'Total Net Salary', 'Total Deductions',
                'Total Overtime', 'Average Monthly Salary', 'Attendance %'
            ])
            
            for summary in report_data['summary_data']:
                writer.writerow([
                    summary['employee_id'],
                    summary['employee_name'],
                    summary['department'],
                    summary['designation'],
                    summary['total_months'],
                    summary['total_gross_salary'],
                    summary['total_net_salary'],
                    summary['total_deductions'],
                    summary['total_overtime_amount'],
                    summary['average_monthly_salary'],
                    summary['attendance_percentage'],
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting payroll summary report: {str(e)}")
            messages.error(request, _("Failed to export report: {}").format(str(e)))
            return self.post(request)
