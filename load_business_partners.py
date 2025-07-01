import os
import django

# ✅ SETUP DJANGO ENVIRONMENT
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from BusinessPartnerMasterData.models import BusinessPartnerGroup, BusinessPartner
from global_settings.models import Currency
from django.utils import timezone

print("🔄 Loading demo data for BusinessPartnerMasterData...")

# STEP 1: Currency (ensure we have a default currency)
try:
    bdt = Currency.objects.get(code='BDT')
    print("⏩ Currency BDT already exists")
except Currency.DoesNotExist:
    bdt = Currency.objects.create(
        code='BDT',
        name='Bangladeshi Taka',
        exchange_rate=1
    )
    print("✅ Created Currency: BDT")

# STEP 2: Business Partner Groups
bp_groups = [
    {"name": "Retail Customers", "description": "Individual retail customers"},
    {"name": "Corporate Clients", "description": "Business and corporate clients"},
    {"name": "Raw Material Suppliers", "description": "Suppliers of raw materials"},
    {"name": "Service Providers", "description": "Providers of services"},
    {"name": "Distributors", "description": "Product distributors and wholesalers"},
]

created_groups = {}
for group in bp_groups:
    obj, created = BusinessPartnerGroup.objects.get_or_create(
        name=group["name"],
        defaults={"description": group["description"]}
    )
    created_groups[group["name"]] = obj
    status = "✅ Created" if created else "⏩ Already exists"
    print(f"{status}: {group['name']}")

# STEP 3: Business Partners (Customers)
customers = [
    {
        "code": "C0001",
        "name": "Dhaka Retail Store",
        "bp_type": "C",
        "group": created_groups["Retail Customers"],
        "phone": "+880-2-9876543",
        "email": "info@dhakaretail.com",
        "default_billing_street": "123 Main Road",
        "default_billing_city": "Dhaka",
        "default_billing_country": "Bangladesh",
        "default_contact_name": "Ahmed Khan",
        "default_contact_phone": "+880-1712-345678"
    },
    {
        "code": "C0002",
        "name": "Chittagong Enterprises Ltd",
        "bp_type": "C",
        "group": created_groups["Corporate Clients"],
        "phone": "+880-31-654321",
        "email": "contact@chittagongent.com",
        "default_billing_street": "45 Port Road",
        "default_billing_city": "Chittagong",
        "default_billing_country": "Bangladesh",
        "default_contact_name": "Fatima Rahman",
        "default_contact_phone": "+880-1812-987654"
    },
    {
        "code": "C0003",
        "name": "Sylhet Trading Co.",
        "bp_type": "C",
        "group": created_groups["Distributors"],
        "phone": "+880-821-765432",
        "email": "sales@sylhettrading.com",
        "default_billing_street": "78 Tea Garden Road",
        "default_billing_city": "Sylhet",
        "default_billing_country": "Bangladesh",
        "default_contact_name": "Kamal Hossain",
        "default_contact_phone": "+880-1912-876543"
    }
]

# STEP 4: Business Partners (Suppliers)
suppliers = [
    {
        "code": "S0001",
        "name": "Bangladesh Materials Ltd",
        "bp_type": "S",
        "group": created_groups["Raw Material Suppliers"],
        "phone": "+880-2-1234567",
        "email": "supply@bdmaterials.com",
        "default_billing_street": "56 Industrial Area",
        "default_billing_city": "Gazipur",
        "default_billing_country": "Bangladesh",
        "default_contact_name": "Rahim Uddin",
        "default_contact_phone": "+880-1612-345678"
    },
    {
        "code": "S0002",
        "name": "Global IT Services",
        "bp_type": "S",
        "group": created_groups["Service Providers"],
        "phone": "+880-2-9876543",
        "email": "support@globalitbd.com",
        "default_billing_street": "89 Tech Park",
        "default_billing_city": "Dhaka",
        "default_billing_country": "Bangladesh",
        "default_contact_name": "Nusrat Jahan",
        "default_contact_phone": "+880-1512-987654"
    }
]

# Create all business partners
for bp_data in customers + suppliers:
    bp, created = BusinessPartner.objects.get_or_create(
        code=bp_data["code"],
        defaults={
            "name": bp_data["name"],
            "bp_type": bp_data["bp_type"],
            "group": bp_data["group"],
            "currency": bdt,
            "phone": bp_data.get("phone", ""),
            "email": bp_data.get("email", ""),
            "default_billing_street": bp_data.get("default_billing_street", ""),
            "default_billing_city": bp_data.get("default_billing_city", ""),
            "default_billing_country": bp_data.get("default_billing_country", ""),
            "default_contact_name": bp_data.get("default_contact_name", ""),
            "default_contact_phone": bp_data.get("default_contact_phone", ""),
            "credit_limit": 100000 if bp_data["bp_type"] == "C" else 0,
        }
    )
    status = "✅ Created" if created else "⏩ Already exists"
    print(f"{status}: {bp_data['name']} ({bp_data['code']})")

print("✅ BusinessPartnerMasterData demo data loaded successfully.")