import os
import django

# ✅ SETUP DJANGO ENVIRONMENT
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from Finance.models import (
    AccountType, ChartOfAccounts, JournalEntry, JournalEntryLine, CostCenter, GeneralLedger
)
from global_settings.models import Currency

# STEP 1: Delete JournalEntryLine
lines_deleted, _ = JournalEntryLine.objects.all().delete()
print(f"✅ Deleted {lines_deleted} JournalEntryLine records.")

# STEP 2: Delete JournalEntry
entries_deleted, _ = JournalEntry.objects.all().delete()
print(f"✅ Deleted {entries_deleted} JournalEntry records.")

# STEP 3: Delete GeneralLedger
ledger_deleted, _ = GeneralLedger.objects.all().delete()
print(f"✅ Deleted {ledger_deleted} GeneralLedger records.")

# STEP 4: Delete ChartOfAccounts
accounts_deleted, _ = ChartOfAccounts.objects.all().delete()
print(f"✅ Deleted {accounts_deleted} ChartOfAccounts records.")

# STEP 5: Delete AccountType
account_types_deleted, _ = AccountType.objects.all().delete()
print(f"✅ Deleted {account_types_deleted} AccountType records.")

# STEP 6: Delete CostCenter
cost_centers_deleted, _ = CostCenter.objects.all().delete()
print(f"✅ Deleted {cost_centers_deleted} CostCenter records.")

# STEP 7: (Optional) Delete Currency only if demo-only
# If you only want to remove 'BDT' used in demo:
demo_currency_deleted, _ = Currency.objects.filter(code='BDT').delete()
print(f"✅ Deleted {demo_currency_deleted} Currency records (only BDT).")

print("🎉 All Finance demo data deleted successfully!")
