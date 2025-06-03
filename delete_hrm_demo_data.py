import os
import sys
import django
from datetime import date  # Import date class correctly

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
    from Hrm.models import (
        Department, Designation, Employee, 
        WorkPlace, Shift, Holiday, LeaveType,
        SalaryComponent
    )
except ImportError as e:
    print(f"❌ Error importing models: {e}")
    print("Make sure the Hrm app is installed and models are correctly defined.")
    sys.exit(1)

print("🔄 Starting HR Management System Demo Data Deletion...")

# STEP 1: Delete Employees
employees_deleted, _ = Employee.objects.filter(employee_id__in=['HR-001', 'IT-001']).delete()
print(f"✅ Deleted {employees_deleted} Employee records.")

# STEP 2: Delete Designations
designations_deleted, _ = Designation.objects.filter(name__in=['HR Manager', 'Software Engineer']).delete()
print(f"✅ Deleted {designations_deleted} Designation records.")

# STEP 3: Delete Departments
departments_deleted, _ = Department.objects.filter(code__in=['HR', 'IT']).delete()
print(f"✅ Deleted {departments_deleted} Department records.")

# STEP 4: Delete Workplaces
workplaces_deleted, _ = WorkPlace.objects.filter(name__in=['Head Office', 'Chittagong Office']).delete()
print(f"✅ Deleted {workplaces_deleted} WorkPlace records.")

# STEP 5: Delete Shifts
shifts_deleted, _ = Shift.objects.filter(name='General Shift').delete()
print(f"✅ Deleted {shifts_deleted} Shift records.")

# STEP 6: Delete Leave Types
leave_types_deleted, _ = LeaveType.objects.filter(code__in=['CL', 'SL']).delete()
print(f"✅ Deleted {leave_types_deleted} LeaveType records.")

# STEP 7: Delete Holidays
holidays_deleted, _ = Holiday.objects.filter(date__in=[date(2025, 3, 30), date(2025, 3, 26)]).delete()
print(f"✅ Deleted {holidays_deleted} Holiday records.")

# STEP 8: Delete Salary Components
salary_components_deleted, _ = SalaryComponent.objects.filter(code__in=['BASIC', 'HRA', 'TAX']).delete()
print(f"✅ Deleted {salary_components_deleted} SalaryComponent records.")

print("\n🎉 All HRM Demo Data Deleted Successfully!")