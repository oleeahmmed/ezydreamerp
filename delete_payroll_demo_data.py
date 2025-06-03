import os
import sys
import django
from datetime import date

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
    from Hrm.models import SalaryMonth, EmployeeSalary
    from Finance.models import JournalEntry, JournalEntryLine, ChartOfAccounts
except ImportError as e:
    print(f"❌ Error importing models: {e}")
    print("Make sure the Hrm and Finance apps are installed and models are correctly defined.")
    sys.exit(1)

print("🔄 Starting Payroll Demo Data Deletion...")

# STEP 1: Delete Employee Salaries
employee_salaries_deleted, _ = EmployeeSalary.objects.filter(
    salary_month__year=2025,
    salary_month__month=5,
    employee__employee_id__in=['HR-001', 'IT-001']
).delete()
print(f"✅ Deleted {employee_salaries_deleted} EmployeeSalary records.")

# STEP 2: Delete Salary Months
salary_months_deleted, _ = SalaryMonth.objects.filter(year=2025, month=5).delete()
print(f"✅ Deleted {salary_months_deleted} SalaryMonth records.")

# STEP 3: Delete Payroll-Related Journal Entries
journal_lines_deleted, _ = JournalEntryLine.objects.filter(
    journal_entry__doc_num__in=['JE-PAY-HR-001', 'JE-PAY-IT-001']
).delete()
print(f"✅ Deleted {journal_lines_deleted} JournalEntryLine records for payroll.")
journal_entries_deleted, _ = JournalEntry.objects.filter(
    doc_num__in=['JE-PAY-HR-001', 'JE-PAY-IT-001']
).delete()
print(f"✅ Deleted {journal_entries_deleted} JournalEntry records for payroll.")

# STEP 4: Delete Salary Expense Account
try:
    salary_account_deleted, _ = ChartOfAccounts.objects.filter(code='5001').delete()
    print(f"✅ Deleted {salary_account_deleted} Salary Expense account.")
except NameError:
    print("⚠️ ChartOfAccounts model not found. Skipping Salary Expense account deletion.")

print("\n🎉 All Payroll Demo Data Deleted Successfully!")