from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.views import View
from django.utils import timezone
from django import forms
from django.db import transaction
from django.http import JsonResponse
from Hrm.models import (
    Department, Designation, Employee, EmployeeSeparation, WorkPlace, Shift, Roster,
    RosterAssignment, RosterDay, Holiday, LeaveType, LeaveApplication, ShortLeaveApplication,
    LeaveBalance, AttendanceMonth, AttendanceLog, Attendance, OvertimeRecord,
    SalaryComponent, EmployeeSalaryStructure, SalaryStructureComponent, BonusSetup,
    BonusMonth, EmployeeBonus, AdvanceSetup, EmployeeAdvance, AdvanceInstallment,
    SalaryMonth, EmployeeSalary, SalaryDetail, Promotion, Increment, Deduction,
    ProvidentFundSetting, EmployeeProvidentFund, ProvidentFundTransaction,
    FixedDepositReceipt, TaxYear, TaxRate, AllowanceCalculationPlan,
    AllowanceCalculation, EmployeeInvestment, EmployeeTax, LetterTemplate,
    EmployeeLetter, MobileAttendance, Location, UserLocation, LocationAttendance,
    ZKDevice, ZKAttendanceLog
)
from global_settings.models import Currency
import logging
from datetime import timedelta, datetime

# Set up logging
logger = logging.getLogger(__name__)

class HRMDemoConfigForm(forms.Form):
    """Form for selecting HRM or Payroll demo data action"""
    ACTION_CHOICES = (
        ('import_hrm', 'Import HRM Data'),
        ('import_payroll', 'Import Payroll Data'),
        ('delete_hrm', 'Delete HRM Data'),
        ('delete_payroll', 'Delete Payroll Data'),
    )
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Action',
        required=True
    )

class HRMDemoAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': "You don't have permission to access this page."}, status=403)
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied()
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': "Please log in to access this page."}, status=401)
        return super().handle_no_permission()

class HRMDemoConfigView(HRMDemoAccessMixin, View):
    template_name = 'demo_config.html'
    permission_required = 'Hrm.change_department'
    form_class = HRMDemoConfigForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'form': form,
            'screen_title': 'HRM & Payroll Demo Setup',
            'subtitle_title': 'Manage sample data for HRM and Payroll modules',
            'cancel_url': reverse_lazy('hrm:department_list'),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if form.is_valid():
            action = form.cleaned_data['action']

            try:
                with transaction.atomic():
                    import_summary = []
                    deletion_summary = []

                    if action == 'import_hrm':
                        # Currency
                        bdt, _ = Currency.objects.get_or_create(
                            code='BDT',
                            defaults={'name': 'Bangladeshi Taka', 'exchange_rate': 1}
                        )
                        import_summary.append("1 Currency")

                        # Departments
                        departments = [
                            ('DEPT001', 'Human Resources', 'Handles HR operations'),
                            ('DEPT002', 'Information Technology', 'Manages IT infrastructure'),
                            ('DEPT003', 'Finance', 'Manages financial operations'),
                            ('DEPT004', 'Payroll', 'Manages payroll operations')
                        ]
                        dept_objects = {}
                        for code, name, desc in departments:
                            dept, _ = Department.objects.get_or_create(
                                code=code,
                                defaults={'name': name, 'description': desc}
                            )
                            dept_objects[code] = dept
                        import_summary.append(f"{len(departments)} Departments")

                        # Designations
                        designations = [
                            ('HR Manager', 'DEPT001', 'Oversees HR operations'),
                            ('Software Engineer', 'DEPT002', 'Develops software solutions'),
                            ('Accountant', 'DEPT003', 'Manages accounts'),
                            ('Payroll Officer', 'DEPT004', 'Handles payroll processing')
                        ]
                        designation_objects = {}
                        for name, dept_code, desc in designations:
                            desig, _ = Designation.objects.get_or_create(
                                name=name,
                                department=dept_objects[dept_code],
                                defaults={'description': desc}
                            )
                            designation_objects[name] = desig
                        import_summary.append(f"{len(designations)} Designations")

                        # Users and Employees
                        employees = [
                            (
                                'john_doe', 'John', 'Doe', 'EMP001', 'M', '1985-01-01',
                                'john.demo@example.com', '+8801234567890', 'DEPT001', 'HR Manager', 50000
                            ),
                            (
                                'jane_smith', 'Jane', 'Smith', 'EMP002', 'F', '1990-02-02',
                                'jane.demo@example.com', '+8801234567891', 'DEPT004', 'Payroll Officer', 45000
                            )
                        ]
                        emp_objects = {}
                        for username, fname, lname, emp_id, gender, dob, email, phone, dept_code, designation_name, salary in employees:
                            user, _ = User.objects.get_or_create(
                                username=username,
                                defaults={'first_name': fname, 'last_name': lname, 'email': email}
                            )
                            emp, _ = Employee.objects.get_or_create(
                                employee_id=emp_id,
                                defaults={
                                    'user': user,
                                    'first_name': fname,
                                    'last_name': lname,
                                    'name': f'{fname} {lname}',
                                    'gender': gender,
                                    'date_of_birth': datetime.strptime(dob, '%Y-%m-%d').date(),
                                    'blood_group': 'A+',
                                    'marital_status': 'S',
                                    'email': email,
                                    'phone': phone,
                                    'present_address': '123 Demo Street, Dhaka',
                                    'permanent_address': '123 Demo Street, Dhaka',
                                    'department': dept_objects[dept_code],
                                    'designation': designation_objects[designation_name],
                                    'joining_date': timezone.now().date() - timedelta(days=365),
                                    'basic_salary': salary,
                                    'is_active': True
                                }
                            )
                            emp_objects[emp_id] = emp
                        import_summary.append(f"{len(employees)} Employees")

                        # Employee Separation
                        separations = [
                            ('EMP001', 'RES', 'Pursuing new opportunities'),
                        ]
                        for emp_id, sep_type, reason in separations:
                            EmployeeSeparation.objects.get_or_create(
                                employee=emp_objects[emp_id],
                                defaults={
                                    'separation_type': sep_type,
                                    'separation_date': timezone.now().date() - timedelta(days=30),
                                    'reason': reason,
                                    'notice_period_served': True,
                                    'exit_interview_conducted': True,
                                    'clearance_completed': True,
                                    'final_settlement_completed': True
                                }
                            )
                        import_summary.append(f"{len(separations)} Employee Separations")

                        # WorkPlaces
                        workplaces = [
                            ('Main Office', '789 Business Ave, Dhaka', 'Headquarters'),
                        ]
                        wp_objects = {}
                        for name, addr, desc in workplaces:
                            wp, _ = WorkPlace.objects.get_or_create(
                                name=name, defaults={'address': addr, 'description': desc}
                            )
                            wp_objects[name] = wp
                        import_summary.append(f"{len(workplaces)} WorkPlaces")

                        # Shifts
                        shifts = [
                            ('Day Shift', '09:00:00', '17:00:00', 60, 15),
                        ]
                        shift_objects = {}
                        for name, start, end, break_time, grace in shifts:
                            shift, _ = Shift.objects.get_or_create(
                                name=name,
                                defaults={
                                    'start_time': start,
                                    'end_time': end,
                                    'break_time': break_time,
                                    'grace_time': grace
                                }
                            )
                            shift_objects[name] = shift
                        import_summary.append(f"{len(shifts)} Shifts")

                        # Rosters
                        roster, _ = Roster.objects.get_or_create(
                            name='Q1 2025 Roster',
                            defaults={
                                'start_date': timezone.now().date(),
                                'end_date': timezone.now().date() + timedelta(days=90),
                                'description': 'Quarterly roster for Q1 2025'
                            }
                        )
                        import_summary.append("1 Roster")

                        # Roster Assignments and Days
                        for emp_id in ['EMP002']:
                            ra, _ = RosterAssignment.objects.get_or_create(roster=roster, employee=emp_objects[emp_id])
                            for i in range(3):
                                RosterDay.objects.get_or_create(
                                    roster_assignment=ra,
                                    date=timezone.now().date() + timedelta(days=i),
                                    defaults={'shift': shift_objects['Day Shift'], 'workplace': wp_objects['Main Office']}
                                )
                        import_summary.append("3 Roster Days")

                        # Holidays
                        holidays = [
                            ('Eid-ul-Fitr', timezone.now().date() + timedelta(days=10)),
                        ]
                        for name, date in holidays:
                            Holiday.objects.get_or_create(name=name, defaults={'date': date})
                        import_summary.append(f"{len(holidays)} Holidays")

                        # Leave Types
                        leave_types = [
                            ('AL', 'Annual Leave', 20, True, 10),
                        ]
                        lt_objects = {}
                        for code, name, max_days, carry, carry_max in leave_types:
                            lt, _ = LeaveType.objects.get_or_create(
                                code=code,
                                defaults={
                                    'name': name,
                                    'max_days_per_year': max_days,
                                    'carry_forward': carry,
                                    'max_carry_forward_days': carry_max
                                }
                            )
                            lt_objects[code] = lt
                        import_summary.append(f"{len(leave_types)} Leave Types")

                        # Leave Applications
                        LeaveApplication.objects.get_or_create(
                            employee=emp_objects['EMP002'],
                            leave_type=lt_objects['AL'],
                            start_date=timezone.now().date() + timedelta(days=15),
                            end_date=timezone.now().date() + timedelta(days=17),
                            defaults={
                                'reason': 'Personal vacation',
                                'status': 'APP',
                                'approved_by': emp_objects['EMP002'],
                                'approved_date': timezone.now()
                            }
                        )
                        import_summary.append("1 Leave Application")

                        # Short Leave Application
                        ShortLeaveApplication.objects.get_or_create(
                            employee=emp_objects['EMP002'],
                            date=timezone.now().date(),
                            start_time='14:00:00',
                            end_time='16:00:00',
                            defaults={
                                'reason': 'Medical appointment',
                                'status': 'APP',
                                'approved_by': emp_objects['EMP002'],
                                'approved_date': timezone.now()
                            }
                        )
                        import_summary.append("1 Short Leave Application")

                        # Leave Balance
                        for emp_id in ['EMP002']:
                            LeaveBalance.objects.get_or_create(
                                employee=emp_objects[emp_id],
                                leave_type=lt_objects['AL'],
                                year=timezone.now().year,
                                defaults={'total_days': 20, 'used_days': 3, 'remaining_days': 17}
                            )
                        import_summary.append("1 Leave Balance")

                        # Attendance Month
                        att_month, _ = AttendanceMonth.objects.get_or_create(
                            year=timezone.now().year,
                            month=timezone.now().month,
                            defaults={
                                'is_processed': True,
                                'processed_date': timezone.now(),
                                'processed_by': emp_objects['EMP002']
                            }
                        )
                        import_summary.append("1 Attendance Month")

                        # Attendance Logs and Attendance
                        for emp_id in ['EMP002']:
                            AttendanceLog.objects.get_or_create(
                                employee=emp_objects[emp_id],
                                timestamp=timezone.now(),
                                defaults={'is_in': True, 'location': 'Main Office', 'device': 'Mobile'}
                            )
                            ra = RosterAssignment.objects.get(roster=roster, employee=emp_objects[emp_id])
                            rd = RosterDay.objects.get(roster_assignment=ra, date=timezone.now().date())
                            Attendance.objects.get_or_create(
                                employee=emp_objects[emp_id],
                                date=timezone.now().date(),
                                defaults={
                                    'status': 'PRE',
                                    'roster_day': rd,
                                    'check_in': timezone.now(),
                                    'check_out': timezone.now() + timedelta(hours=8),
                                    'late_minutes': 0,
                                    'early_out_minutes': 0,
                                    'overtime_minutes': 0
                                }
                            )
                        import_summary.append("1 Attendance Log, 1 Attendance")

                        # Overtime Record
                        OvertimeRecord.objects.get_or_create(
                            employee=emp_objects['EMP002'],
                            date=timezone.now().date(),
                            start_time='17:00:00',
                            end_time='19:00:00',
                            defaults={
                                'hours': 2,
                                'reason': 'Project deadline',
                                'status': 'APP',
                                'approved_by': emp_objects['EMP002'],
                                'approved_date': timezone.now()
                            }
                        )
                        import_summary.append("1 Overtime Record")

                        # Mobile Attendance
                        MobileAttendance.objects.get_or_create(
                            employee=emp_objects['EMP002'],
                            check_in=timezone.now(),
                            defaults={'check_in_location': 'Main Office', 'check_in_notes': 'Checked in via mobile'}
                        )
                        import_summary.append("1 Mobile Attendance")

                        # Location
                        location, _ = Location.objects.get_or_create(
                            name='Main Office',
                            defaults={
                                'address': '789 Business Ave, Dhaka',
                                'latitude': 23.8103,
                                'longitude': 90.4125,
                                'radius': 0.5
                            }
                        )
                        import_summary.append("1 Location")

                        # User Location
                        UserLocation.objects.get_or_create(
                            user=User.objects.get(username='jane_smith'),
                            location=location,
                            defaults={'is_primary': True}
                        )
                        import_summary.append("1 User Location")

                        # Location Attendance
                        LocationAttendance.objects.get_or_create(
                            user=User.objects.get(username='jane_smith'),
                            location=location,
                            attendance_type='IN',
                            defaults={
                                'latitude': 23.8103,
                                'longitude': 90.4125,
                                'is_within_radius': True,
                                'distance': 0.1,
                                'device_info': 'Mobile App'
                            }
                        )
                        import_summary.append("1 Location Attendance")

                        # ZK Device
                        zk_device, _ = ZKDevice.objects.get_or_create(
                            name='ZK Device 1',
                            ip_address='192.168.1.100',
                            defaults={'port': 4370, 'timeout': 5}
                        )
                        import_summary.append("1 ZK Device")

                        # ZK Attendance Log
                        ZKAttendanceLog.objects.get_or_create(
                            device=zk_device,
                            user_id='EMP002',
                            timestamp=timezone.now(),
                            defaults={'punch_type': 'IN', 'status': 0, 'verify_type': 'Fingerprint'}
                        )
                        import_summary.append("1 ZK Attendance Log")

                        message = f"HRM demo data imported: {', '.join(import_summary)}." if import_summary else "No HRM data imported."
                        status = 'success' if import_summary else 'warning'

                    elif action == 'import_payroll':
                        emp_objects = {emp.employee_id: emp for emp in Employee.objects.filter(employee_id__in=['EMP002'])}
                        if not emp_objects:
                            message = "Required employee data not found. Import HRM data first."
                            status = 'error'
                            if is_ajax:
                                return JsonResponse({'status': status, 'message': message})
                            messages.error(request, message)
                            return redirect('hrm:hrm_demo_config')

                        # Salary Components
                        salary_components = [
                            ('BASIC', 'Basic Salary', 'EARN', True, True),
                            ('TAX', 'Income Tax', 'DED', False, False),
                        ]
                        sc_objects = {}
                        for code, name, comp_type, taxable, fixed in salary_components:
                            sc, _ = SalaryComponent.objects.get_or_create(
                                code=code,
                                defaults={
                                    'name': name,
                                    'component_type': comp_type,
                                    'is_taxable': taxable,
                                    'is_fixed': fixed
                                }
                            )
                            sc_objects[code] = sc
                        import_summary.append(f"{len(salary_components)} Salary Components")

                        # Employee Salary Structure
                        for emp_id in ['EMP002']:
                            salary_structure, _ = EmployeeSalaryStructure.objects.get_or_create(
                                employee=emp_objects[emp_id],
                                effective_date=timezone.now().date() - timedelta(days=180),
                                defaults={'gross_salary': 45000}
                            )
                            SalaryStructureComponent.objects.get_or_create(
                                salary_structure=salary_structure,
                                component=sc_objects['BASIC'],
                                defaults={'amount': 45000}
                            )
                        import_summary.append("1 Salary Structure")

                        # Bonus Setup
                        bonus_setup, _ = BonusSetup.objects.get_or_create(
                            name='Annual Bonus',
                            defaults={'description': 'Year-end performance bonus'}
                        )
                        import_summary.append("1 Bonus Setup")

                        # Bonus Month
                        bonus_month, _ = BonusMonth.objects.get_or_create(
                            bonus_setup=bonus_setup,
                            year=timezone.now().year,
                            month=12,
                            defaults={
                                'is_generated': True,
                                'generated_date': timezone.now(),
                                'generated_by': emp_objects['EMP002']
                            }
                        )
                        import_summary.append("1 Bonus Month")

                        # Employee Bonus
                        for emp_id in ['EMP002']:
                            EmployeeBonus.objects.get_or_create(
                                bonus_month=bonus_month,
                                employee=emp_objects[emp_id],
                                defaults={'amount': 5000, 'remarks': 'Performance bonus'}
                            )
                        import_summary.append("1 Employee Bonus")

                        # Advance Setup
                        advance_setup, _ = AdvanceSetup.objects.get_or_create(
                            name='Salary Advance',
                            defaults={
                                'max_amount': 5000,
                                'max_installments': 6,
                                'interest_rate': 5,
                                'description': 'Short-term salary advance'
                            }
                        )
                        import_summary.append("1 Advance Setup")

                        # Employee Advance
                        advance, _ = EmployeeAdvance.objects.get_or_create(
                            employee=emp_objects['EMP002'],
                            advance_setup=advance_setup,
                            application_date=timezone.now().date(),
                            defaults={
                                'amount': 2000,
                                'installments': 4,
                                'installment_amount': 525,
                                'interest_amount': 100,
                                'total_amount': 2100,
                                'status': 'APP',
                                'approved_by': emp_objects['EMP002'],
                                'approval_date': timezone.now().date(),
                                'reason': 'Personal need'
                            }
                        )
                        import_summary.append("1 Employee Advance")

                        # Advance Installment
                        AdvanceInstallment.objects.get_or_create(
                            advance=advance,
                            installment_number=1,
                            defaults={
                                'amount': 525,
                                'due_date': timezone.now().date() + timedelta(days=30),
                                'is_paid': False
                            }
                        )
                        import_summary.append("1 Advance Installment")

                        # Salary Month
                        salary_month, _ = SalaryMonth.objects.get_or_create(
                            year=timezone.now().year,
                            month=timezone.now().month,
                            defaults={
                                'is_generated': True,
                                'generated_date': timezone.now(),
                                'generated_by': emp_objects['EMP002'],
                                'is_paid': True,
                                'payment_date': timezone.now().date()
                            }
                        )
                        import_summary.append("1 Salary Month")

                        # Employee Salary
                        for emp_id in ['EMP002']:
                            employee_salary, created = EmployeeSalary.objects.get_or_create(
                                salary_month=salary_month,
                                employee=emp_objects[emp_id],
                                defaults={
                                    'basic_salary': 45000,
                                    'gross_salary': 45000,
                                    'total_earnings': 45200,
                                    'total_deductions': 100,
                                    'net_salary': 45100,
                                    'working_days': 22,
                                    'present_days': 20,
                                    'absent_days': 2,
                                    'leave_days': 0,
                                    'overtime_hours': 2,
                                    'overtime_amount': 200
                                }
                            )
                            if created:
                                SalaryDetail.objects.create(
                                    salary=employee_salary,
                                    component=sc_objects['BASIC'],
                                    amount=45000
                                )
                                SalaryDetail.objects.create(
                                    salary=employee_salary,
                                    component=sc_objects['TAX'],
                                    amount=100
                                )
                        import_summary.append("1 Employee Salary")

                        # Promotion
                        designation_objects = {desig.name: desig for desig in Designation.objects.filter(name='Payroll Officer')}
                        Promotion.objects.get_or_create(
                            employee=emp_objects['EMP002'],
                            from_designation=designation_objects['Payroll Officer'],
                            to_designation=designation_objects['Payroll Officer'],
                            effective_date=timezone.now().date() - timedelta(days=90),
                            defaults={'salary_increment': 500}
                        )
                        import_summary.append("1 Promotion")

                        # Increment
                        Increment.objects.get_or_create(
                            employee=emp_objects['EMP002'],
                            effective_date=timezone.now().date() - timedelta(days=90),
                            defaults={'amount': 500, 'percentage': 1.11}
                        )
                        import_summary.append("1 Increment")

                        # Deduction
                        Deduction.objects.get_or_create(
                            employee=emp_objects['EMP002'],
                            salary_month=salary_month,
                            defaults={'amount': 100, 'reason': 'Late attendance penalty'}
                        )
                        import_summary.append("1 Deduction")

                        # Provident Fund Setting
                        pf_setting, _ = ProvidentFundSetting.objects.get_or_create(
                            effective_date=timezone.now().date() - timedelta(days=365),
                            defaults={'employee_contribution': 10, 'employer_contribution': 10}
                        )
                        import_summary.append("1 Provident Fund Setting")

                        # Employee Provident Fund
                        for emp_id in ['EMP002']:
                            EmployeeProvidentFund.objects.get_or_create(
                                employee=emp_objects[emp_id],
                                defaults={
                                    'enrollment_date': timezone.now().date() - timedelta(days=180),
                                    'employee_contribution': 10,
                                    'employer_contribution': 10
                                }
                            )
                        import_summary.append("1 Employee Provident Fund")

                        # Provident Fund Transaction
                        for emp_id in ['EMP002']:
                            emp_pf = EmployeeProvidentFund.objects.get(employee=emp_objects[emp_id])
                            ProvidentFundTransaction.objects.get_or_create(
                                employee_pf=emp_pf,
                                transaction_date=timezone.now().date(),
                                defaults={
                                    'transaction_type': 'CON',
                                    'employee_amount': 600,
                                    'employer_amount': 600,
                                    'total_amount': 1200,
                                    'reference': 'Monthly PF contribution'
                                }
                            )
                        import_summary.append("1 Provident Fund Transaction")

                        # Fixed Deposit Receipt
                        FixedDepositReceipt.objects.get_or_create(
                            fdr_number='FDR001',
                            defaults={
                                'bank_name': 'Sample Bank',
                                'branch_name': 'Main Branch',
                                'amount': 10000,
                                'interest_rate': 6.5,
                                'start_date': timezone.now().date() - timedelta(days=180),
                                'maturity_date': timezone.now().date() + timedelta(days=180)
                            }
                        )
                        import_summary.append("1 Fixed Deposit Receipt")

                        # Tax Year
                        tax_year, _ = TaxYear.objects.get_or_create(
                            name='2025-2026',
                            defaults={
                                'start_date': timezone.now().date().replace(month=7, day=1),
                                'end_date': timezone.now().date().replace(month=6, day=30) + timedelta(days=365)
                            }
                        )
                        import_summary.append("1 Tax Year")

                        # Tax Rate
                        tax_rates = [
                            (0, 30000, 0),
                        ]
                        for min_amt, max_amt, rate in tax_rates:
                            TaxRate.objects.get_or_create(
                                tax_year=tax_year,
                                min_amount=min_amt,
                                defaults={'max_amount': max_amt, 'rate': rate}
                            )
                        import_summary.append(f"{len(tax_rates)} Tax Rates")

                        # Allowance Calculation Plan
                        allowance_plan, _ = AllowanceCalculationPlan.objects.get_or_create(
                            name='Standard Allowance',
                            defaults={'description': 'Standard allowance calculation'}
                        )
                        import_summary.append("1 Allowance Calculation Plan")

                        # Allowance Calculation
                        AllowanceCalculation.objects.get_or_create(
                            plan=allowance_plan,
                            component=sc_objects['BASIC'],
                            defaults={'percentage': 100}
                        )
                        import_summary.append("1 Allowance Calculation")

                        # Employee Investment
                        EmployeeInvestment.objects.get_or_create(
                            employee=emp_objects['EMP002'],
                            tax_year=tax_year,
                            defaults={'investment_type': 'Mutual Fund', 'amount': 5000}
                        )
                        import_summary.append("1 Employee Investment")

                        # Employee Tax
                        EmployeeTax.objects.get_or_create(
                            employee=emp_objects['EMP002'],
                            tax_year=tax_year,
                            defaults={
                                'total_income': 72000,
                                'total_exemptions': 30000,
                                'total_investments': 5000,
                                'taxable_income': 37000,
                                'tax_amount': 1850,
                                'generated_date': timezone.now(),
                                'generated_by': emp_objects['EMP002']
                            }
                        )
                        import_summary.append("1 Employee Tax")

                        # Letter Template
                        letter_template, _ = LetterTemplate.objects.get_or_create(
                            name='Appointment Letter',
                            defaults={
                                'letter_type': 'APP',
                                'content': 'Dear {{employee.first_name}}, Congratulations on your appointment as {{employee.designation.name}}.'
                            }
                        )
                        import_summary.append("1 Letter Template")

                        # Employee Letter
                        EmployeeLetter.objects.get_or_create(
                            employee=emp_objects['EMP002'],
                            template=letter_template,
                            reference_number='LET001',
                            defaults={
                                'duration_date': timedelta(days=365),
                                'content': 'Dear Jane, Congratulations on your appointment as Payroll Officer.',
                                'issued_by': emp_objects['EMP002']
                            }
                        )
                        import_summary.append("1 Employee Letter")

                        message = f"Payroll demo data imported: {', '.join(import_summary)}." if import_summary else "No payroll data imported."
                        status = 'success' if import_summary else 'warning'

                    elif action == 'delete_hrm':
                        hrm_models = [
                            ZKAttendanceLog, LocationAttendance, UserLocation, Location, MobileAttendance,
                            LeaveBalance, ShortLeaveApplication, LeaveApplication, LeaveType, Holiday,
                            RosterDay, RosterAssignment, Roster, Shift, WorkPlace,
                            EmployeeSeparation, Employee, Designation, Department
                        ]
                        for model in hrm_models:
                            count = model.objects.all().count()
                            model.objects.all().delete()
                            deletion_summary.append(f"{count} {model.__name__}")
                        user_count = User.objects.filter(username__in=['john_doe', 'jane_smith']).count()
                        User.objects.filter(username__in=['john_doe', 'jane_smith']).delete()
                        if user_count:
                            deletion_summary.append(f"{user_count} Users")

                        message = f"Deleted HRM data: {', '.join(deletion_summary)}." if deletion_summary else "No HRM data deleted."
                        status = 'success' if deletion_summary else 'warning'

                    elif action == 'delete_payroll':
                        payroll_models = [
                            EmployeeLetter, LetterTemplate, EmployeeTax, EmployeeInvestment,
                            AllowanceCalculation, AllowanceCalculationPlan, TaxRate, TaxYear,
                            FixedDepositReceipt, ProvidentFundTransaction, EmployeeProvidentFund,
                            ProvidentFundSetting, Deduction, Increment, Promotion, SalaryDetail,
                            EmployeeSalary, SalaryMonth, AdvanceInstallment, EmployeeAdvance,
                            AdvanceSetup, EmployeeBonus, BonusMonth, BonusSetup,
                            SalaryStructureComponent, EmployeeSalaryStructure, SalaryComponent,
                            OvertimeRecord, Attendance, AttendanceLog, AttendanceMonth
                        ]
                        for model in payroll_models:
                            count = model.objects.all().count()
                            model.objects.all().delete()
                            deletion_summary.append(f"{count} {model.__name__}")

                        message = f"Deleted Payroll data: {', '.join(deletion_summary)}." if deletion_summary else "No Payroll data deleted."
                        status = 'success' if deletion_summary else 'warning'

                    if is_ajax:
                        return JsonResponse({'status': status, 'message': message})
                    messages.add_message(request, messages.SUCCESS if status == 'success' else messages.WARNING, message)
                    return redirect('hrm:hrm_demo_config')

            except Exception as e:
                logger.error(f"Error performing {action}: {str(e)}")
                message = f"Error performing {action}: {str(e)}"
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': message}, status=500)
                messages.error(request, message)
                return redirect('hrm:hrm_demo_config')

        else:
            message = "Invalid form submission. Please check the fields."
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': message}, status=400)
            messages.error(request, message)
            return redirect('hrm:hrm_demo_config')