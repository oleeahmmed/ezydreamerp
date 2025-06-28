import os
import django

# ✅ SETUP DJANGO ENVIRONMENT
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from Finance.models import AccountType, ChartOfAccounts, JournalEntry, JournalEntryLine
from global_settings.models import Currency
from django.utils import timezone

# STEP 1: Currency
bdt, _ = Currency.objects.get_or_create(
    code='BDT',
    defaults={
        'name': 'Bangladeshi Taka',
        'exchange_rate': 1
    }
)

# STEP 2: Account Types
account_types = [
    {"code": "100", "name": "Asset", "is_debit": True},
    {"code": "200", "name": "Liability", "is_debit": False},
    {"code": "300", "name": "Equity", "is_debit": False},
    {"code": "400", "name": "Revenue", "is_debit": False},
    {"code": "500", "name": "Expense", "is_debit": True},
]

for at in account_types:
    AccountType.objects.get_or_create(code=at["code"], defaults={"name": at["name"], "is_debit": at["is_debit"]})

# STEP 3: Chart of Accounts
asset = AccountType.objects.get(code="100")
liability = AccountType.objects.get(code="200")
equity = AccountType.objects.get(code="300")
revenue = AccountType.objects.get(code="400")
expense = AccountType.objects.get(code="500")

ChartOfAccounts.objects.get_or_create(code="1000", defaults={"name": "Cash", "account_type": asset, "currency": bdt})
ChartOfAccounts.objects.get_or_create(code="1020", defaults={"name": "Customer Receivable", "account_type": asset, "currency": bdt})
ChartOfAccounts.objects.get_or_create(code="1500", defaults={"name": "Chair Inventory", "account_type": asset, "currency": bdt})
ChartOfAccounts.objects.get_or_create(code="2000", defaults={"name": "Accounts Payable", "account_type": liability, "currency": bdt})
ChartOfAccounts.objects.get_or_create(code="3000", defaults={"name": "Owner Capital", "account_type": equity, "currency": bdt})
ChartOfAccounts.objects.get_or_create(code="4000", defaults={"name": "Sales Revenue", "account_type": revenue, "currency": bdt})
ChartOfAccounts.objects.get_or_create(code="5000", defaults={"name": "Office Rent", "account_type": expense, "currency": bdt})

# STEP 4: Journal Entry
cash = ChartOfAccounts.objects.get(code="1000")
sales = ChartOfAccounts.objects.get(code="4000")

entry, created = JournalEntry.objects.get_or_create(
    doc_num="JE0001",
    defaults={
        "posting_date": timezone.now().date(),
        "reference": "Invoice #A123",
        "remarks": "Sold 1 chair to customer",
        "currency": bdt,
        "total_debit": 5000,
        "total_credit": 5000,
        "is_posted": True,
    }
)

if created:
    JournalEntryLine.objects.create(
        journal_entry=entry,
        account=cash,
        debit_amount=5000,
        credit_amount=0,
        description="Cash received"
    )

    JournalEntryLine.objects.create(
        journal_entry=entry,
        account=sales,
        debit_amount=0,
        credit_amount=5000,
        description="Chair sales"
    )

print("✅ Demo data loaded successfully.")
