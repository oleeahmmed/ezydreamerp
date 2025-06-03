

from django.db.models.signals import post_save, post_delete
from django.db import transaction
from django.dispatch import receiver
from Finance.models import JournalEntry, GeneralLedger

@receiver(post_save, sender=JournalEntry)
def post_journal_to_gl(sender, instance, created, **kwargs):
    if instance.is_posted:
        def post_gl():
            print(f"🔔 Posting JournalEntry {instance.doc_num}")
            lines = instance.lines.all()
            print(f"📌 Found {lines.count()} lines")

            # Clear old entries
            GeneralLedger.objects.filter(journal_entry=instance).delete()

            for line in lines:
                balance = line.debit_amount - line.credit_amount
                print(f"➕ Line: {line.account.code}, Dr: {line.debit_amount}, Cr: {line.credit_amount}")
                GeneralLedger.objects.create(
                    account=line.account,
                    posting_date=instance.posting_date,
                    journal_entry=instance,
                    debit_amount=line.debit_amount,
                    credit_amount=line.credit_amount,
                    balance=balance,
                    currency=instance.currency
                )

        transaction.on_commit(post_gl)

            

@receiver(post_delete, sender=JournalEntry)
def delete_gl_on_journal_delete(sender, instance, **kwargs):
    print(f"🗑️ Deleting GL for JournalEntry {instance.doc_num}")
    GeneralLedger.objects.filter(journal_entry=instance).delete()
