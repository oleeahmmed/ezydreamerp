"""
Finance Module Signals
Handles other finance-related signals
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps

def get_models():
    """Lazy model imports"""
    try:
        ChartOfAccounts = apps.get_model('Finance', 'ChartOfAccounts')
        AccountType = apps.get_model('Finance', 'AccountType')
        
        return {
            'ChartOfAccounts': ChartOfAccounts,
            'AccountType': AccountType,
        }
    except Exception as e:
        print(f"❌ Error getting finance models: {e}")
        return {}

@receiver(post_save, sender='Finance.ChartOfAccounts')
def account_created(sender, instance, created, **kwargs):
    """Chart of Accounts Save → Log Creation"""
    if created:
        print(f"📊 New Account Created: {instance.code} - {instance.name}")

@receiver(post_delete, sender='Finance.ChartOfAccounts')
def account_deleted(sender, instance, **kwargs):
    """Chart of Accounts Delete → Log Deletion"""
    print(f"🗑️ Account Deleted: {instance.code} - {instance.name}")

print("📡 Finance signals loaded successfully")
