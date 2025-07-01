import os
import sys
import django
from django.utils import timezone
from decimal import Decimal
from datetime import datetime

# ✅ SETUP DJANGO ENVIRONMENT
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
try:
    django.setup()
except Exception as e:
    print(f"❌ Error setting up Django: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

# Import models
try:
    from Hrm.models import Department, Employee, Designation, SalaryMonth, EmployeeSalary, SalaryDetail, SalaryComponent
    from Finance.models import CostCenter, AccountType, ChartOfAccounts, JournalEntry, JournalEntryLine
    from global_settings.models import Currency
except ImportError as e:
    print(f"❌ Error importing models: {e}")
    print("Make sure the Hrm, Finance, and global_settings apps are installed and models are correctly defined.")
    sys.exit(1)

print("🔄 Starting Payroll Demo Data Generation...")

# -------------------- STEP 1: SETUP DEPENDENCIES --------------------
# Currency
bdt, created = Currency.objects.get_or_create(
    code='BDT',
    defaults={'name': 'Bangladeshi Taka', 'exchange_rate': 1}
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Currency BDT")

# Cost Centers
main_cost_center, created = CostCenter.objects.get_or_create(
    code='CC100',
    defaults={'name': 'Main Office', 'is_active': True}
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Cost Center CC100")

branch_cost_center, created = CostCenter.objects.get_or_create(
    code='CC200',
    defaults={'name': 'Branch Office', 'is_active': True}
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Cost Center CC200")

# Chart of Accounts
try:
    expense, created = AccountType.objects.get_or_create(
        code="500",
        defaults={"name": "Expense", "is_debit": True}
    )
    status = "✅ Created" if created else "⏩ Already exists"
    print(f"{status}: Account Type Expense (500)")

    cash, created = ChartOfAccounts.objects.get_or_create(
        code="1000",
        defaults={"name": "Cash", "account_type": AccountType.objects.get(code="100"), "currency": bdt}
    )
    status = "✅ Created" if created else "⏩ Already exists"
    print(f"{status}: Chart of Accounts Cash (1000)")

    salary_expense, created = ChartOfAccounts.objects.get_or_create(
        code="5001",
        defaults={"name": "Salary Expense", "account_type": expense, "currency": bdt}
    )
    status = "✅ Created" if created else "⏩ Already exists"
    print(f"{status}: Chart of Accounts Salary Expense (5001)")
except Exception as e:
    print(f"⚠️ Error setting up Chart of Accounts: {e}. Ensure Finance models are correctly defined.")

# Salary Components
basic, created = SalaryComponent.objects.get_or_create(
    code="BASIC",
    defaults={"name": "Basic Salary", "component_type": "EARN", "is_taxable": True, "is_fixed": True}
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Salary Component BASIC")

hra, created = SalaryComponent.objects.get_or_create(
    code="HRA",
    defaults={"name": "House Rent Allowance", "component_type": "EARN", "is_taxable": True, "is_fixed": True}
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Salary Component HRA")

tax, created = SalaryComponent.objects.get_or_create(
    code="TAX",
    defaults={"name": "Income Tax", "component_type": "DED", "is_taxable": False, "is_fixed": False}
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Salary Component TAX")

# Departments
dept_hr, created = Department.objects.get_or_create(
    code='HR',
    defaults={
        'name': 'Human Resources',
        'description': 'Manages employee relations, recruitment, and HR policies'
    }
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Department HR")

dept_it, created = Department.objects.get_or_create(
    code='IT',
    defaults={
        'name': 'Information Technology',
        'description': 'Manages IT infrastructure, software development, and support'
    }
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Department IT")

# Designations
hr_manager, created = Designation.objects.get_or_create(
    name='HR Manager',
    department=dept_hr,
    defaults={'description': 'Manages HR department and policies'}
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Designation HR Manager")

software_engineer, created = Designation.objects.get_or_create(
    name='Software Engineer',
    department=dept_it,
    defaults={'description': 'Develops and maintains software applications'}
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Designation Software Engineer")

# Employees
employee1, created = Employee.objects.get_or_create(
    employee_id='HR-001',
    defaults={
        'first_name': 'Ahmed',
        'last_name': 'Rahman',
        'gender': 'M',
        'date_of_birth': datetime(1990, 5, 15).date(),
        'blood_group': 'A+',
        'marital_status': 'M',
        'email': 'ahmed.rahman@example.com',
        'phone': '+880-017-12345678',
        'present_address': 'House #10, Road #5, Gulshan, Dhaka-1212, Bangladesh',
        'permanent_address': 'House #10, Road #5, Gulshan, Dhaka-1212, Bangladesh',
        'department': dept_hr,
        'designation': hr_manager,
        'joining_date': datetime(2020, 1, 1).date(),
        'basic_salary': Decimal('50000.00'),
        'is_active': True
    }
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Employee HR-001")

employee2, created = Employee.objects.get_or_create(
    employee_id='IT-001',
    defaults={
        'first_name': 'Fatima',
        'last_name': 'Begum',
        'gender': 'F',
        'date_of_birth': datetime(1992, 8, 20).date(),
        'blood_group': 'B+',
        'marital_status': 'S',
        'email': 'fatima.begum@example.com',
        'phone': '+880-019-87654321',
        'present_address': 'House #20, Road #8, Uttara, Dhaka-1230, Bangladesh',
        'permanent_address': 'House #20, Road #8, Uttara, Dhaka-1230, Bangladesh',
        'department': dept_it,
        'designation': software_engineer,
        'joining_date': datetime(2021, 3, 1).date(),
        'basic_salary': Decimal('60000.00'),
        'is_active': True
    }
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Employee IT-001")

# -------------------- STEP 2: SALARY MONTH --------------------
print("\n📅 Creating Salary Month...")
salary_month, created = SalaryMonth.objects.get_or_create(
    year=2025,
    month=5,
    defaults={
        'is_generated': False,
        'remarks': 'Demo payroll for May 2025'
    }
)
status = "✅ Created" if created else "⏩ Already exists"
print(f"{status}: Salary Month 2025-05")

# -------------------- STEP 3: EMPLOYEE SALARIES --------------------
print("\n💸 Creating Employee Salaries...")
employee_salaries = [
    {
        'employee': employee1,
        'basic_salary': Decimal('50000.00'),
        'gross_salary': Decimal('55000.00'),
        'total_earnings': Decimal('55000.00'),
        'total_deductions': Decimal('2000.00'),
        'net_salary': Decimal('53000.00'),
        'working_days': 22,
        'present_days': 20,
        'absent_days': 2,
        'leave_days': 0,
        'remarks': 'Monthly salary for HR Manager'
    },
    {
        'employee': employee2,
        'basic_salary': Decimal('60000.00'),
        'gross_salary': Decimal('67000.00'),
        'total_earnings': Decimal('67000.00'),
        'total_deductions': Decimal('3000.00'),
        'net_salary': Decimal('64000.00'),
        'working_days': 22,
        'present_days': 21,
        'absent_days': 1,
        'leave_days': 0,
        'remarks': 'Monthly salary for Software Engineer'
    }
]
for es_data in employee_salaries:
    try:
        es, created = EmployeeSalary.objects.get_or_create(
            salary_month=salary_month,
            employee=es_data['employee'],
            defaults={
                'basic_salary': es_data['basic_salary'],
                'gross_salary': es_data['gross_salary'],
                'total_earnings': es_data['total_earnings'],
                'total_deductions': es_data['total_deductions'],
                'net_salary': es_data['net_salary'],
                'working_days': es_data['working_days'],
                'present_days': es_data['present_days'],
                'absent_days': es_data['absent_days'],
                'leave_days': es_data['leave_days'],
                'remarks': es_data['remarks']
            }
        )
        if created:
            # Create Salary Details
            SalaryDetail.objects.get_or_create(
                salary=es,
                component=basic,
                defaults={'amount': es_data['basic_salary']}
            )
            SalaryDetail.objects.get_or_create(
                salary=es,
                component=hra,
                defaults={'amount': es_data['gross_salary'] - es_data['basic_salary']}
            )
            SalaryDetail.objects.get_or_create(
                salary=es,
                component=tax,
                defaults={'amount': es_data['total_deductions']}
            )
            # Create corresponding Journal Entry
            try:
                je, je_created = JournalEntry.objects.get_or_create(
                    doc_num=f"JE-PAY-{es_data['employee'].employee_id}",
                    defaults={
                        "posting_date": timezone.now().date(),
                        "reference": f"Salary {salary_month}",
                        "remarks": f"Salary payment for {es_data['employee'].employee_id}",
                        "currency": bdt,
                        "total_debit": es_data['net_salary'],
                        "total_credit": es_data['net_salary'],
                        "is_posted": True,
                        "cost_center": main_cost_center if es_data['employee'].department.code == 'HR' else branch_cost_center
                    }
                )
                if je_created:
                    JournalEntryLine.objects.create(
                        journal_entry=je,
                        account=salary_expense,
                        debit_amount=es_data['net_salary'],
                        credit_amount=0,
                        description=f"Salary expense for {es_data['employee'].employee_id}"
                    )
                    JournalEntryLine.objects.create(
                        journal_entry=je,
                        account=cash,
                        debit_amount=0,
                        credit_amount=es_data['net_salary'],
                        description=f"Cash paid for {es_data['employee'].employee_id}"
                    )
            except Exception as e:
                print(f"⚠️ Error creating journal entry for {es_data['employee'].employee_id}: {e}")
        status = "✅ Created" if created else "⏩ Already exists"
        print(f"{status}: Employee Salary for {es_data['employee'].employee_id}")
    except Exception as e:
        print(f"❌ Error creating employee salary for {es_data['employee'].employee_id}: {e}")

print("\n✅ Payroll Demo Data Generation Completed!")