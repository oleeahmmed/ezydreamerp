"""
Journal Entry Signals
Handles: JournalEntry, JournalEntryLine
Creates General Ledger entries when Journal Entries are posted
"""

from django.db.models.signals import post_save, post_delete
from django.db import transaction
from django.dispatch import receiver
from django.apps import apps

def get_models():
    """Lazy model imports"""
    try:
        JournalEntry = apps.get_model('Finance', 'JournalEntry')
        JournalEntryLine = apps.get_model('Finance', 'JournalEntryLine')
        GeneralLedger = apps.get_model('Finance', 'GeneralLedger')
        
        return {
            'JournalEntry': JournalEntry,
            'JournalEntryLine': JournalEntryLine,
            'GeneralLedger': GeneralLedger,
        }
    except Exception as e:
        print(f"❌ Error getting journal models: {e}")
        return {}

@receiver(post_save, sender='Finance.JournalEntry')
def post_journal_to_gl(sender, instance, created, **kwargs):
    """
    Journal Entry Save → General Ledger Entries Created
    """
    if instance.is_posted:
        try:
            models = get_models()
            GeneralLedger = models.get('GeneralLedger')
            
            if not GeneralLedger:
                print("❌ GeneralLedger model not available")
                return
                
            print(f"🔔 Journal Entry {instance.doc_num} saved → Creating GL entries")
            
            # Get journal entry lines
            lines = instance.lines.all()
            print(f"📌 Found {lines.count()} lines for JE {instance.doc_num}")
            
            if not lines.exists():
                print(f"⚠️ No lines found, skipping GL posting")
                return
            
            # Delete old GL entries
            old_gl_count = GeneralLedger.objects.filter(journal_entry=instance).count()
            if old_gl_count > 0:
                print(f"🗑️ Deleting {old_gl_count} old GL entries")
                GeneralLedger.objects.filter(journal_entry=instance).delete()
            
            # Create new GL entries
            gl_entries_created = 0
            for line in lines:
                # Calculate balance based on account type
                if line.account.account_type.is_debit:
                    # Debit account: Dr increases, Cr decreases
                    balance = line.debit_amount - line.credit_amount
                else:
                    # Credit account: Cr increases, Dr decreases
                    balance = line.credit_amount - line.debit_amount
                
                print(f"➕ Creating GL: {line.account.code}, Dr={line.debit_amount}, Cr={line.credit_amount}, Balance={balance}")
                
                gl_entry = GeneralLedger.objects.create(
                    account=line.account,
                    posting_date=instance.posting_date,
                    journal_entry=instance,
                    debit_amount=line.debit_amount,
                    credit_amount=line.credit_amount,
                    balance=balance,
                    currency=instance.currency,
                    cost_center=instance.cost_center
                )
                
                gl_entries_created += 1
                print(f"✅ GL entry #{gl_entry.id} created for {line.account.code}")
            
            print(f"✅ {gl_entries_created} GL entries created for JE {instance.doc_num}")
            
        except Exception as e:
            print(f"❌ Error posting JE to GL: {e}")
            import traceback
            traceback.print_exc()

@receiver(post_delete, sender='Finance.JournalEntry')
def delete_gl_on_journal_delete(sender, instance, **kwargs):
    """Journal Entry Delete → GL Entries Deleted"""
    try:
        models = get_models()
        GeneralLedger = models.get('GeneralLedger')
        
        if GeneralLedger:
            gl_count = GeneralLedger.objects.filter(journal_entry=instance).count()
            if gl_count > 0:
                GeneralLedger.objects.filter(journal_entry=instance).delete()
                print(f"🗑️ Journal Entry {instance.doc_num} deleted → {gl_count} GL entries deleted")
    except Exception as e:
        print(f"❌ Error deleting GL entries: {e}")

@receiver(post_save, sender='Finance.JournalEntryLine')
def update_gl_on_line_change(sender, instance, **kwargs):
    """Journal Entry Line Save → GL Entries Updated"""
    journal_entry = instance.journal_entry
    if journal_entry.is_posted:
        try:
            models = get_models()
            GeneralLedger = models.get('GeneralLedger')
            
            if not GeneralLedger:
                return
                
            print(f"🔄 Journal Entry Line changed → Updating GL for JE {journal_entry.doc_num}")
            
            # Delete old GL entries
            GeneralLedger.objects.filter(journal_entry=journal_entry).delete()
            
            # Recreate GL entries
            lines = journal_entry.lines.all()
            for line in lines:
                if line.account.account_type.is_debit:
                    balance = line.debit_amount - line.credit_amount
                else:
                    balance = line.credit_amount - line.debit_amount
                
                GeneralLedger.objects.create(
                    account=line.account,
                    posting_date=journal_entry.posting_date,
                    journal_entry=journal_entry,
                    debit_amount=line.debit_amount,
                    credit_amount=line.credit_amount,
                    balance=balance,
                    currency=journal_entry.currency,
                    cost_center=journal_entry.cost_center
                )
            
            print(f"✅ GL entries updated for JE {journal_entry.doc_num}")
            
        except Exception as e:
            print(f"❌ Error updating GL: {e}")

@receiver(post_delete, sender='Finance.JournalEntryLine')
def update_gl_on_line_delete(sender, instance, **kwargs):
    """Journal Entry Line Delete → GL Entries Updated"""
    journal_entry = instance.journal_entry
    if journal_entry.is_posted:
        try:
            models = get_models()
            GeneralLedger = models.get('GeneralLedger')
            
            if not GeneralLedger:
                return
                
            print(f"🗑️ Journal Entry Line deleted → Updating GL for JE {journal_entry.doc_num}")
            
            # Delete old GL entries
            GeneralLedger.objects.filter(journal_entry=journal_entry).delete()
            
            # Recreate from remaining lines
            remaining_lines = journal_entry.lines.all()
            for line in remaining_lines:
                if line.account.account_type.is_debit:
                    balance = line.debit_amount - line.credit_amount
                else:
                    balance = line.credit_amount - line.debit_amount
                
                GeneralLedger.objects.create(
                    account=line.account,
                    posting_date=journal_entry.posting_date,
                    journal_entry=journal_entry,
                    debit_amount=line.debit_amount,
                    credit_amount=line.credit_amount,
                    balance=balance,
                    currency=journal_entry.currency,
                    cost_center=journal_entry.cost_center
                )
            
            print(f"✅ GL entries updated after line deletion")
            
        except Exception as e:
            print(f"❌ Error updating GL after line deletion: {e}")

print("📡 Journal Entry signals loaded successfully")
