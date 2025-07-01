import os
import sys
import django
from datetime import datetime, timedelta, time
import random
from decimal import Decimal

# ✅ SETUP DJANGO ENVIRONMENT - This must be done before importing any models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    django.setup()
except Exception as e:
    print(f"❌ Error setting up Django: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

# Now try to import models - with error handling
try:
    from Hrm.models import (
        Department, Designation, Employee, 
        WorkPlace, Shift, 
        Holiday, LeaveType,
        SalaryComponent
    )
except ImportError as e:
    print(f"❌ Error importing models: {e}")
    print("Make sure the Hrm app is installed and the models are correctly defined.")
    sys.exit(1)

print("🔄 Starting HR Management System Demo Data Generation...")

# -------------------- UTILITY FUNCTIONS --------------------

def get_random_date(start_year=2022, end_year=2023):
    """Generate a random date between start_year and end_year"""
    start_date = datetime(start_year, 1, 1).date()
    end_date = datetime(end_year, 12, 31).date()
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    return start_date + timedelta(days=random_days)

def get_random_phone():
    """Generate a random Bangladeshi phone number"""
    operators = ['013', '014', '015', '016', '017', '018', '019']
    operator = random.choice(operators)
    number = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return f"+880-{operator}-{number}"

def get_random_bd_address():
    """Generate a random Bangladeshi address"""
    areas = [
        "Gulshan", "Banani", "Dhanmondi", "Uttara", "Mirpur", 
        "Mohakhali", "Motijheel", "Baridhara", "Bashundhara", "Khilgaon"
    ]
    cities = ["Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna", "Barisal", "Rangpur"]
    
    house = f"House #{random.randint(1, 100)}"
    road = f"Road #{random.randint(1, 20)}"
    area = random.choice(areas)
    city = random.choice(cities)
    
    return f"{house}, {road}, {area}, {city}-{random.randint(1000, 9999)}, Bangladesh"

def get_random_bd_name(gender=None):
    """Generate a random Bangladeshi name based on gender"""
    if gender is None:
        gender = random.choice(['M', 'F'])
    
    male_first_names = [
        "Abul", "Ahmed", "Akbar", "Ali", "Amir", "Anwar", "Ashraf", "Aziz",
        "Farid", "Farooq", "Habib", "Hamid", "Hasan", "Ibrahim", "Imran", "Jamal",
        "Kamal", "Khalid", "Mahmud", "Malik", "Mohammad", "Monir", "Nasir", "Omar",
        "Rafiq", "Rahim", "Rahman", "Rashid", "Riaz", "Saif", "Salim", "Shahid"
    ]
    
    female_first_names = [
        "Aisha", "Amina", "Asma", "Ayesha", "Begum", "Farida", "Fatima", "Farzana",
        "Hasina", "Jasmine", "Khadija", "Laila", "Lubna", "Maliha", "Maryam", "Nasreen",
        "Nazia", "Noor", "Rabia", "Rahima", "Razia", "Rehana", "Sabina", "Saima"
    ]
    
    last_names = [
        "Ahmed", "Akhtar", "Ali", "Bhuiyan", "Chowdhury", "Das", "Haque", "Hossain",
        "Islam", "Jahan", "Khan", "Mahmud", "Miah", "Molla", "Mondol", "Rahman"
    ]
    
    if gender == 'M':
        first_name = random.choice(male_first_names)
    else:
        first_name = random.choice(female_first_names)
    
    last_name = random.choice(last_names)
    
    return first_name, last_name, gender

# -------------------- STEP 1: DEPARTMENTS --------------------
print("\n🏢 Creating Departments...")

departments = [
    {"name": "Administration", "code": "ADMIN", "description": "Administrative department handling overall operations"},
    {"name": "Human Resources", "code": "HR", "description": "Manages employee relations, recruitment, and HR policies"},
    {"name": "Finance & Accounts", "code": "FIN", "description": "Handles financial operations, accounting, and reporting"},
    {"name": "Information Technology", "code": "IT", "description": "Manages IT infrastructure, software development, and support"},
    {"name": "Sales & Marketing", "code": "SALES", "description": "Handles sales operations, marketing, and customer relations"},
    {"name": "Production", "code": "PROD", "description": "Manages production operations and quality control"},
    {"name": "Supply Chain", "code": "SCM", "description": "Handles procurement, logistics, and inventory management"},
    {"name": "Research & Development", "code": "RND", "description": "Focuses on product development and innovation"}
]

created_departments = {}
for dept_data in departments:
    try:
        dept, created = Department.objects.get_or_create(
            code=dept_data["code"],
            defaults={
                "name": dept_data["name"],
                "description": dept_data["description"]
            }
        )
        created_departments[dept_data["code"]] = dept
        status = "✅ Created" if created else "⏩ Already exists"
        print(f"{status}: {dept_data['name']} ({dept_data['code']})")
    except Exception as e:
        print(f"❌ Error creating department {dept_data['name']}: {e}")

# -------------------- STEP 2: DESIGNATIONS --------------------
print("\n👔 Creating Designations...")

designations = [
    # Administration
    {"name": "Managing Director", "department": "ADMIN", "description": "Head of the company"},
    {"name": "Chief Executive Officer", "department": "ADMIN", "description": "Executive responsible for company operations"},
    {"name": "Executive Assistant", "department": "ADMIN", "description": "Provides administrative support to executives"},
    
    # Human Resources
    {"name": "HR Manager", "department": "HR", "description": "Manages HR department and policies"},
    {"name": "HR Executive", "department": "HR", "description": "Handles day-to-day HR operations"},
    {"name": "Recruitment Specialist", "department": "HR", "description": "Focuses on recruitment and selection"},
    
    # Finance & Accounts
    {"name": "Finance Manager", "department": "FIN", "description": "Manages financial operations"},
    {"name": "Accountant", "department": "FIN", "description": "Handles accounting and financial reporting"},
    {"name": "Accounts Executive", "department": "FIN", "description": "Manages accounts payable and receivable"},
    
    # Information Technology
    {"name": "IT Manager", "department": "IT", "description": "Manages IT department and infrastructure"},
    {"name": "Software Engineer", "department": "IT", "description": "Develops and maintains software applications"},
    {"name": "System Administrator", "department": "IT", "description": "Manages IT systems and networks"},
    
    # Sales & Marketing
    {"name": "Sales Manager", "department": "SALES", "description": "Manages sales operations and team"},
    {"name": "Marketing Executive", "department": "SALES", "description": "Handles marketing campaigns and promotions"},
    {"name": "Sales Executive", "department": "SALES", "description": "Manages sales and client relationships"},
    
    # Production
    {"name": "Production Manager", "department": "PROD", "description": "Manages production operations"},
    {"name": "Production Supervisor", "department": "PROD", "description": "Supervises production processes"},
    {"name": "Quality Control Officer", "department": "PROD", "description": "Ensures product quality standards"},
    
    # Supply Chain
    {"name": "Supply Chain Manager", "department": "SCM", "description": "Manages supply chain operations"},
    {"name": "Procurement Officer", "department": "SCM", "description": "Handles procurement and vendor management"},
    {"name": "Logistics Coordinator", "department": "SCM", "description": "Coordinates logistics and transportation"},
    
    # Research & Development
    {"name": "R&D Manager", "department": "RND", "description": "Manages research and development activities"},
    {"name": "Product Developer", "department": "RND", "description": "Develops new products and innovations"},
    {"name": "Research Analyst", "department": "RND", "description": "Conducts market and product research"}
]

created_designations = {}
for desig_data in designations:
    try:
        if desig_data["department"] not in created_departments:
            print(f"⚠️ Skipping designation {desig_data['name']} - Department {desig_data['department']} not found")
            continue
            
        dept = created_departments[desig_data["department"]]
        desig, created = Designation.objects.get_or_create(
            name=desig_data["name"],
            department=dept,
            defaults={
                "description": desig_data["description"]
            }
        )
        key = f"{desig_data['department']}_{desig_data['name'].replace(' ', '_')}"
        created_designations[key] = desig
        status = "✅ Created" if created else "⏩ Already exists"
        print(f"{status}: {desig_data['name']} ({dept.name})")
    except Exception as e:
        print(f"❌ Error creating designation {desig_data['name']}: {e}")

# -------------------- STEP 3: WORKPLACES --------------------
print("\n🏢 Creating Workplaces...")

workplaces = [
    {
        "name": "Head Office",
        "address": "House #42, Road #11, Banani, Dhaka-1213, Bangladesh",
        "description": "Main corporate headquarters"
    },
    {
        "name": "Factory Unit 1",
        "address": "Plot #45, BSCIC Industrial Area, Tongi, Gazipur-1710, Bangladesh",
        "description": "Main production facility"
    },
    {
        "name": "Factory Unit 2",
        "address": "Plot #78, BSCIC Industrial Area, Savar, Dhaka-1340, Bangladesh",
        "description": "Secondary production facility"
    },
    {
        "name": "Chittagong Office",
        "address": "House #15, Road #3, Agrabad C/A, Chittagong-4100, Bangladesh",
        "description": "Regional office in Chittagong"
    },
    {
        "name": "Sylhet Office",
        "address": "House #7, Road #2, Shahjalal Upashahar, Sylhet-3100, Bangladesh",
        "description": "Regional office in Sylhet"
    }
]

created_workplaces = {}
for wp_data in workplaces:
    try:
        wp, created = WorkPlace.objects.get_or_create(
            name=wp_data["name"],
            defaults={
                "address": wp_data["address"],
                "description": wp_data["description"]
            }
        )
        created_workplaces[wp_data["name"]] = wp
        status = "✅ Created" if created else "⏩ Already exists"
        print(f"{status}: {wp_data['name']}")
    except Exception as e:
        print(f"❌ Error creating workplace {wp_data['name']}: {e}")

# -------------------- STEP 4: SHIFTS --------------------
print("\n⏰ Creating Shifts...")

shifts = [
    {
        "name": "General Shift",
        "start_time": time(9, 0),
        "end_time": time(17, 0),
        "break_time": 60,
        "grace_time": 15
    },
    {
        "name": "Morning Shift",
        "start_time": time(6, 0),
        "end_time": time(14, 0),
        "break_time": 60,
        "grace_time": 15
    },
    {
        "name": "Evening Shift",
        "start_time": time(14, 0),
        "end_time": time(22, 0),
        "break_time": 60,
        "grace_time": 15
    },
    {
        "name": "Night Shift",
        "start_time": time(22, 0),
        "end_time": time(6, 0),
        "break_time": 60,
        "grace_time": 15
    },
    {
        "name": "Half Day",
        "start_time": time(9, 0),
        "end_time": time(13, 0),
        "break_time": 0,
        "grace_time": 15
    }
]

created_shifts = {}
for shift_data in shifts:
    try:
        shift, created = Shift.objects.get_or_create(
            name=shift_data["name"],
            defaults={
                "start_time": shift_data["start_time"],
                "end_time": shift_data["end_time"],
                "break_time": shift_data["break_time"],
                "grace_time": shift_data["grace_time"]
            }
        )
        created_shifts[shift_data["name"]] = shift
        status = "✅ Created" if created else "⏩ Already exists"
        print(f"{status}: {shift_data['name']} ({shift_data['start_time'].strftime('%H:%M')} - {shift_data['end_time'].strftime('%H:%M')})")
    except Exception as e:
        print(f"❌ Error creating shift {shift_data['name']}: {e}")

# -------------------- STEP 5: LEAVE TYPES --------------------
print("\n🏖️ Creating Leave Types...")

leave_types = [
    {
        "name": "Casual Leave",
        "code": "CL",
        "description": "Leave for personal matters",
        "paid": True,
        "max_days_per_year": 10,
        "carry_forward": False,
        "max_carry_forward_days": 0
    },
    {
        "name": "Sick Leave",
        "code": "SL",
        "description": "Leave for medical reasons",
        "paid": True,
        "max_days_per_year": 14,
        "carry_forward": False,
        "max_carry_forward_days": 0
    },
    {
        "name": "Annual Leave",
        "code": "AL",
        "description": "Annual vacation leave",
        "paid": True,
        "max_days_per_year": 15,
        "carry_forward": True,
        "max_carry_forward_days": 5
    },
    {
        "name": "Maternity Leave",
        "code": "ML",
        "description": "Leave for female employees for childbirth",
        "paid": True,
        "max_days_per_year": 112,  # 16 weeks as per Bangladesh Labor Law
        "carry_forward": False,
        "max_carry_forward_days": 0
    },
    {
        "name": "Paternity Leave",
        "code": "PL",
        "description": "Leave for male employees for childbirth",
        "paid": True,
        "max_days_per_year": 7,
        "carry_forward": False,
        "max_carry_forward_days": 0
    },
    {
        "name": "Leave Without Pay",
        "code": "LWP",
        "description": "Unpaid leave",
        "paid": False,
        "max_days_per_year": 30,
        "carry_forward": False,
        "max_carry_forward_days": 0
    },
    {
        "name": "Compensatory Leave",
        "code": "COMP",
        "description": "Leave in lieu of working on holidays",
        "paid": True,
        "max_days_per_year": 10,
        "carry_forward": False,
        "max_carry_forward_days": 0
    }
]

created_leave_types = {}
for lt_data in leave_types:
    try:
        lt, created = LeaveType.objects.get_or_create(
            code=lt_data["code"],
            defaults={
                "name": lt_data["name"],
                "description": lt_data["description"],
                "paid": lt_data["paid"],
                "max_days_per_year": lt_data["max_days_per_year"],
                "carry_forward": lt_data["carry_forward"],
                "max_carry_forward_days": lt_data["max_carry_forward_days"]
            }
        )
        created_leave_types[lt_data["code"]] = lt
        status = "✅ Created" if created else "⏩ Already exists"
        print(f"{status}: {lt_data['name']} ({lt_data['code']}) - {lt_data['max_days_per_year']} days")
    except Exception as e:
        print(f"❌ Error creating leave type {lt_data['name']}: {e}")

# -------------------- STEP 6: HOLIDAYS --------------------
print("\n🎉 Creating Holidays...")

# Bangladeshi holidays for 2023
holidays = [
    {"name": "New Year's Day", "date": datetime(2023, 1, 1).date(), "description": "New Year's Day celebration"},
    {"name": "International Mother Language Day", "date": datetime(2023, 2, 21).date(), "description": "Commemorating the Bengali Language Movement"},
    {"name": "Independence Day", "date": datetime(2023, 3, 26).date(), "description": "Bangladesh Independence Day"},
    {"name": "Bengali New Year (Pohela Boishakh)", "date": datetime(2023, 4, 14).date(), "description": "Bengali New Year celebration"},
    {"name": "May Day", "date": datetime(2023, 5, 1).date(), "description": "International Workers' Day"},
    {"name": "Eid-ul-Fitr", "date": datetime(2023, 4, 22).date(), "description": "Eid-ul-Fitr celebration"},
    {"name": "Eid-ul-Fitr (2nd Day)", "date": datetime(2023, 4, 23).date(), "description": "Eid-ul-Fitr celebration (2nd day)"},
    {"name": "Eid-ul-Fitr (3rd Day)", "date": datetime(2023, 4, 24).date(), "description": "Eid-ul-Fitr celebration (3rd day)"},
    {"name": "Eid-ul-Adha", "date": datetime(2023, 6, 29).date(), "description": "Eid-ul-Adha celebration"},
    {"name": "Eid-ul-Adha (2nd Day)", "date": datetime(2023, 6, 30).date(), "description": "Eid-ul-Adha celebration (2nd day)"},
    {"name": "Eid-ul-Adha (3rd Day)", "date": datetime(2023, 7, 1).date(), "description": "Eid-ul-Adha celebration (3rd day)"},
    {"name": "National Mourning Day", "date": datetime(2023, 8, 15).date(), "description": "Commemorating the assassination of Sheikh Mujibur Rahman"},
    {"name": "Durga Puja", "date": datetime(2023, 10, 24).date(), "description": "Hindu festival of Durga Puja"},
    {"name": "Victory Day", "date": datetime(2023, 12, 16).date(), "description": "Bangladesh Victory Day"},
    {"name": "Christmas Day", "date": datetime(2023, 12, 25).date(), "description": "Christmas Day celebration"}
]

for holiday_data in holidays:
    try:
        holiday, created = Holiday.objects.get_or_create(
            name=holiday_data["name"],
            date=holiday_data["date"],
            defaults={
                "description": holiday_data["description"]
            }
        )
        status = "✅ Created" if created else "⏩ Already exists"
        print(f"{status}: {holiday_data['name']} ({holiday_data['date'].strftime('%Y-%m-%d')})")
    except Exception as e:
        print(f"❌ Error creating holiday {holiday_data['name']}: {e}")

# -------------------- STEP 7: SALARY COMPONENTS --------------------
print("\n💰 Creating Salary Components...")

salary_components = [
    # Earnings
    {"name": "Basic Salary", "code": "BASIC", "component_type": "EARN", "is_taxable": True, "is_fixed": True, "description": "Basic salary component"},
    {"name": "House Rent Allowance", "code": "HRA", "component_type": "EARN", "is_taxable": True, "is_fixed": True, "description": "Allowance for housing"},
    {"name": "Medical Allowance", "code": "MED", "component_type": "EARN", "is_taxable": True, "is_fixed": True, "description": "Allowance for medical expenses"},
    {"name": "Conveyance Allowance", "code": "CONV", "component_type": "EARN", "is_taxable": True, "is_fixed": True, "description": "Allowance for transportation"},
    {"name": "Food Allowance", "code": "FOOD", "component_type": "EARN", "is_taxable": True, "is_fixed": True, "description": "Allowance for food expenses"},
    {"name": "Special Allowance", "code": "SPCL", "component_type": "EARN", "is_taxable": True, "is_fixed": True, "description": "Special allowance"},
    {"name": "Overtime", "code": "OT", "component_type": "EARN", "is_taxable": True, "is_fixed": False, "description": "Payment for overtime work"},
    {"name": "Bonus", "code": "BONUS", "component_type": "EARN", "is_taxable": True, "is_fixed": False, "description": "Performance or festival bonus"},
    
    # Deductions
    {"name": "Income Tax", "code": "TAX", "component_type": "DED", "is_taxable": False, "is_fixed": False, "description": "Income tax deduction"},
    {"name": "Provident Fund", "code": "PF", "component_type": "DED", "is_taxable": False, "is_fixed": True, "description": "Employee contribution to provident fund"},
    {"name": "Advance", "code": "ADV", "component_type": "DED", "is_taxable": False, "is_fixed": False, "description": "Deduction for advance payment"},
    {"name": "Loan", "code": "LOAN", "component_type": "DED", "is_taxable": False, "is_fixed": False, "description": "Deduction for loan repayment"},
    {"name": "Late Deduction", "code": "LATE", "component_type": "DED", "is_taxable": False, "is_fixed": False, "description": "Deduction for late attendance"},
    {"name": "Absent Deduction", "code": "ABS", "component_type": "DED", "is_taxable": False, "is_fixed": False, "description": "Deduction for absence"}
]

created_salary_components = {}
for sc_data in salary_components:
    try:
        sc, created = SalaryComponent.objects.get_or_create(
            code=sc_data["code"],
            defaults={
                "name": sc_data["name"],
                "component_type": sc_data["component_type"],
                "is_taxable": sc_data["is_taxable"],
                "is_fixed": sc_data["is_fixed"],
                "description": sc_data["description"]
            }
        )
        created_salary_components[sc_data["code"]] = sc
        status = "✅ Created" if created else "⏩ Already exists"
        print(f"{status}: {sc_data['name']} ({sc_data['code']}) - {sc_data['component_type']}")
    except Exception as e:
        print(f"❌ Error creating salary component {sc_data['name']}: {e}")

# -------------------- STEP 8: EMPLOYEES --------------------
print("\n👨‍💼 Creating Employees...")

# Create 10 employees (simplified version)
employee_data = []

# Create one employee for each department
for dept_code, dept in created_departments.items():
    # Find a designation for this department
    desig_keys = [key for key, desig in created_designations.items() if key.startswith(dept_code)]
    
    if desig_keys:
        desig_key = random.choice(desig_keys)
        desig = created_designations[desig_key]
        
        first_name, last_name, gender = get_random_bd_name()
        email = f"{first_name.lower()}.{last_name.lower()}@example.com"
        
        employee_data.append({
            "employee_id": f"{dept_code}-001",
            "first_name": first_name,
            "last_name": last_name,
            "gender": gender,
            "date_of_birth": get_random_date(1970, 1985),
            "blood_group": random.choice(['A+', 'B+', 'O+', 'AB+', 'A-', 'B-', 'O-', 'AB-']),
            "marital_status": random.choice(['S', 'M']),
            "email": email,
            "phone": get_random_phone(),
            "present_address": get_random_bd_address(),
            "permanent_address": get_random_bd_address(),
            "department": dept,
            "designation": desig,
            "joining_date": get_random_date(2015, 2020),
            "basic_salary": Decimal(random.randint(50000, 80000)),
            "is_active": True
        })

created_employees = {}
for emp_data in employee_data:
    try:
        # Check if we need to create a user for the employee
        try:
            from django.contrib.auth.models import User
            # Create user only if User model is available
            email_username = emp_data["email"].split('@')[0]
            user = None
            try:
                user = User.objects.create_user(
                    username=email_username,
                    email=emp_data["email"],
                    password="password123",  # Default password
                    first_name=emp_data["first_name"],
                    last_name=emp_data["last_name"]
                )
            except Exception as e:
                print(f"⚠️ Could not create user for {emp_data['first_name']} {emp_data['last_name']}: {e}")
        except ImportError:
            user = None
            print("⚠️ Django User model not available, skipping user creation")
        
        emp, created = Employee.objects.get_or_create(
            employee_id=emp_data["employee_id"],
            defaults={
                "user": user,
                "first_name": emp_data["first_name"],
                "last_name": emp_data["last_name"],
                "gender": emp_data["gender"],
                "date_of_birth": emp_data["date_of_birth"],
                "blood_group": emp_data["blood_group"],
                "marital_status": emp_data["marital_status"],
                "email": emp_data["email"],
                "phone": emp_data["phone"],
                "present_address": emp_data["present_address"],
                "permanent_address": emp_data["permanent_address"],
                "department": emp_data["department"],
                "designation": emp_data["designation"],
                "joining_date": emp_data["joining_date"],
                "basic_salary": emp_data["basic_salary"],
                "is_active": emp_data["is_active"]
            }
        )
        created_employees[emp_data["employee_id"]] = emp
        status = "✅ Created" if created else "⏩ Already exists"
        print(f"{status}: {emp_data['first_name']} {emp_data['last_name']} ({emp_data['employee_id']}) - {emp_data['designation'].name}")
    except Exception as e:
        print(f"❌ Error creating employee {emp_data['first_name']} {emp_data['last_name']}: {e}")

print("\n✅ HR Management System Demo Data Generation Completed!")