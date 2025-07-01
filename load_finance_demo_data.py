import os
import django

# ✅ SETUP DJANGO ENVIRONMENT
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from Finance.models import AccountType, ChartOfAccounts, JournalEntry, JournalEntryLine, CostCenter
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

# STEP 3: Cost Centers
main_cost_center, _ = CostCenter.objects.get_or_create(
    code='CC100',
    defaults={
        'name': 'Main Office'
    }
)
branch_cost_center, _ = CostCenter.objects.get_or_create(
    code='CC200',
    defaults={
        'name': 'Branch Office'
    }
)

# STEP 4: Chart of Accounts
asset = AccountType.objects.get(code="100")
liability = AccountType.objects.get(code="200")
equity = AccountType.objects.get(code="300")
revenue = AccountType.objects.get(code="400")
expense = AccountType.objects.get(code="500")

cash, _ = ChartOfAccounts.objects.get_or_create(code="1000", defaults={"name": "Cash", "account_type": asset, "currency": bdt})
sales, _ = ChartOfAccounts.objects.get_or_create(code="4000", defaults={"name": "Sales Revenue", "account_type": revenue, "currency": bdt})
rent_expense, _ = ChartOfAccounts.objects.get_or_create(code="5000", defaults={"name": "Office Rent", "account_type": expense, "currency": bdt})

# STEP 5: Journal Entry (with cost center)
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
        "cost_center": main_cost_center,
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

# STEP 6: Add another Journal Entry for rent expense (branch cost center)
entry2, created2 = JournalEntry.objects.get_or_create(
    doc_num="JE0002",
    defaults={
        "posting_date": timezone.now().date(),
        "reference": "Office Rent Payment",
        "remarks": "Paid rent for branch office",
        "currency": bdt,
        "total_debit": 2000,
        "total_credit": 2000,
        "is_posted": True,
        "cost_center": branch_cost_center,
    }
)

if created2:
    JournalEntryLine.objects.create(
        journal_entry=entry2,
        account=rent_expense,
        debit_amount=2000,
        credit_amount=0,
        description="Branch rent expense"
    )
    JournalEntryLine.objects.create(
        journal_entry=entry2,
        account=cash,
        debit_amount=0,
        credit_amount=2000,
        description="Paid from cash"
    )

print("✅ Demo data with Cost Centers loaded successfully.")
