"""
Sales Module Signals
Handles: ARInvoice, Delivery, Return, and their line items
Creates Journal Entries for sales transactions
"""

from django.db.models.signals import post_save, post_delete
from django.db import transaction
from django.dispatch import receiver
from django.apps import apps
from decimal import Decimal
import re

def get_models():
    """Lazy model imports"""
    try:
        # Sales models
        ARInvoice = apps.get_model('Sales', 'ARInvoice')
        ARInvoiceLine = apps.get_model('Sales', 'ARInvoiceLine')
        Delivery = apps.get_model('Sales', 'Delivery')
        DeliveryLine = apps.get_model('Sales', 'DeliveryLine')
        Return = apps.get_model('Sales', 'Return')
        ReturnLine = apps.get_model('Sales', 'ReturnLine')
        
        # Finance models
        JournalEntry = apps.get_model('Finance', 'JournalEntry')
        JournalEntryLine = apps.get_model('Finance', 'JournalEntryLine')
        ChartOfAccounts = apps.get_model('Finance', 'ChartOfAccounts')
        
        # Global models
        Currency = apps.get_model('global_settings', 'Currency')
        
        return {
            'ARInvoice': ARInvoice,
            'ARInvoiceLine': ARInvoiceLine,
            'Delivery': Delivery,
            'DeliveryLine': DeliveryLine,
            'Return': Return,
            'ReturnLine': ReturnLine,
            'JournalEntry': JournalEntry,
            'JournalEntryLine': JournalEntryLine,
            'ChartOfAccounts': ChartOfAccounts,
            'Currency': Currency,
        }
    except Exception as e:
        print(f"❌ Error getting models: {e}")
        return {}

def get_account_by_code(code):
    """Get account by code with lazy loading"""
    models = get_models()
    ChartOfAccounts = models.get('ChartOfAccounts')
    
    if not ChartOfAccounts:
        return None
        
    try:
        return ChartOfAccounts.objects.get(code=code)
    except ChartOfAccounts.DoesNotExist:
        print(f"❌ Account {code} not found!")
        return None

def generate_doc_number(prefix="JE"):
    """Generate unique document number"""
    models = get_models()
    JournalEntry = models.get('JournalEntry')
    
    if not JournalEntry:
        return f"{prefix}-000001"
        
    try:
        last_entries = JournalEntry.objects.filter(
            doc_num__startswith=prefix
        ).values_list('doc_num', flat=True)
        
        if not last_entries:
            return f"{prefix}-000001"
        
        max_number = 0
        for doc_num in last_entries:
            match = re.search(r'-(\d+)$', doc_num)
            if match:
                number = int(match.group(1))
                if number > max_number:
                    max_number = number
        
        next_number = max_number + 1
        return f"{prefix}-{next_number:06d}"
        
    except Exception as e:
        print(f"Error generating doc number: {e}")
        import time
        timestamp = int(time.time() * 1000) % 1000000
        return f"{prefix}-{timestamp:06d}"

def calculate_invoice_total(invoice):
    """Calculate total amount from invoice lines"""
    try:
        lines = invoice.lines.all()
        if lines.exists():
            line_total = sum(line.total_amount for line in lines)
            print(f"📊 Calculated total from {lines.count()} lines: {line_total}")
            return line_total
        else:
            total = invoice.total_amount or Decimal('0')
            print(f"📊 Using invoice total_amount: {total}")
            return total
    except Exception as e:
        print(f"❌ Error calculating total: {e}")
        return Decimal('0')

# ==================== AR INVOICE SIGNALS ====================

@receiver(post_save, sender='Sales.ARInvoice')
def create_invoice_journal_entry(sender, instance, created, **kwargs):
    """
    AR Invoice Save → Journal Entry Created
    Dr. 1200 - Accounts Receivable
    Cr. 4000 - Sales Revenue
    """
    def create_je():
        try:
            models = get_models()
            JournalEntry = models.get('JournalEntry')
            JournalEntryLine = models.get('JournalEntryLine')
            Currency = models.get('Currency')
            
            if not all([JournalEntry, JournalEntryLine, Currency]):
                print("❌ Required models not available")
                return
                
            print(f"🔔 AR Invoice #{instance.id} saved → Creating Journal Entry")
            
            # Total amount calculate
            total_amount = calculate_invoice_total(instance)
            
            if total_amount <= 0:
                print(f"⚠️ Total amount is {total_amount}, skipping")
                return
            
            if instance.status not in ['Open', 'Partially Paid', 'Paid']:
                print(f"⚠️ Status {instance.status} doesn't require journal entry")
                return
            
            # Delete old entries
            old_entries = JournalEntry.objects.filter(
                reference=f"AR-INVOICE-{instance.id}"
            )
            if old_entries.exists():
                print(f"🗑️ Deleting {old_entries.count()} old journal entries")
                old_entries.delete()
            
            # Get currency and accounts
            currency = instance.currency or Currency.objects.first()
            ar_account = get_account_by_code("1200")  # Accounts Receivable
            sales_account = get_account_by_code("4000")  # Sales Revenue
            
            if not all([currency, ar_account, sales_account]):
                print("❌ Required data not found!")
                return
            
            # Create Journal Entry
            je = JournalEntry.objects.create(
                doc_num=generate_doc_number("JE"),
                posting_date=instance.posting_date,
                reference=f"AR-INVOICE-{instance.id}",
                remarks=f"Sales Invoice - {instance.customer.name}",
                currency=currency,
                total_debit=total_amount,
                total_credit=total_amount,
                is_posted=True
            )
            
            # Create Journal Entry Lines
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=ar_account,
                debit_amount=total_amount,
                credit_amount=Decimal('0'),
                description=f"AR Invoice #{instance.id} - {instance.customer.name}"
            )
            
            JournalEntryLine.objects.create(
                journal_entry=je,
                account=sales_account,
                debit_amount=Decimal('0'),
                credit_amount=total_amount,
                description=f"Sales Revenue - Invoice #{instance.id}"
            )
            
            print(f"✅ Journal Entry {je.doc_num} created for Invoice #{instance.id}")
            
        except Exception as e:
            print(f"❌ Error creating invoice journal entry: {e}")
            import traceback
            traceback.print_exc()
            
    transaction.on_commit(create_je)

@receiver(post_save, sender='Sales.ARInvoice')
def create_payment_journal_entry(sender, instance, **kwargs):
    """
    AR Invoice Payment → Journal Entry Created
    Dr. 1000/1100 - Cash/Bank
    Cr. 1200 - Accounts Receivable
    """
    if instance.paid_amount and instance.paid_amount > 0 and instance.payment_date:
        def create_payment_je():
            try:
                models = get_models()
                JournalEntry = models.get('JournalEntry')
                JournalEntryLine = models.get('JournalEntryLine')
                Currency = models.get('Currency')
                
                print(f"💳 AR Invoice #{instance.id} payment → Creating Payment Journal Entry")
                
                # Get or create payment entry
                existing_payment_je = JournalEntry.objects.filter(
                    reference=f"AR-PAYMENT-{instance.id}"
                ).first()
                
                currency = instance.currency or Currency.objects.first()
                
                # Determine cash/bank account
                if instance.payment_method and 'bank' in instance.payment_method.lower():
                    cash_account = get_account_by_code("1100")  # Bank
                else:
                    cash_account = get_account_by_code("1000")  # Cash
                
                ar_account = get_account_by_code("1200")  # AR
                
                if not all([cash_account, ar_account]):
                    print("❌ Required payment accounts not found!")
                    return
                
                if existing_payment_je:
                    # Update existing
                    existing_payment_je.total_debit = instance.paid_amount
                    existing_payment_je.total_credit = instance.paid_amount
                    existing_payment_je.save()
                    existing_payment_je.lines.all().delete()
                else:
                    # Create new
                    existing_payment_je = JournalEntry.objects.create(
                        doc_num=generate_doc_number("JE"),
                        posting_date=instance.payment_date,
                        reference=f"AR-PAYMENT-{instance.id}",
                        remarks=f"Payment from {instance.customer.name}",
                        currency=currency,
                        total_debit=instance.paid_amount,
                        total_credit=instance.paid_amount,
                        is_posted=True
                    )
                
                # Create lines
                JournalEntryLine.objects.create(
                    journal_entry=existing_payment_je,
                    account=cash_account,
                    debit_amount=instance.paid_amount,
                    credit_amount=Decimal('0'),
                    description=f"Payment received - Invoice #{instance.id}"
                )
                
                JournalEntryLine.objects.create(
                    journal_entry=existing_payment_je,
                    account=ar_account,
                    debit_amount=Decimal('0'),
                    credit_amount=instance.paid_amount,
                    description=f"AR Payment - {instance.customer.name}"
                )
                
                print(f"✅ Payment Journal Entry {existing_payment_je.doc_num} created")
                
            except Exception as e:
                print(f"❌ Error creating payment journal entry: {e}")
                import traceback
                traceback.print_exc()
                
        transaction.on_commit(create_payment_je)

# ==================== DELIVERY SIGNALS ====================

@receiver(post_save, sender='Sales.Delivery')
def create_delivery_journal_entry(sender, instance, created, **kwargs):
    """
    Delivery Save → Journal Entry Created (COGS)
    Dr. 5000 - Cost of Goods Sold
    Cr. 1300 - Inventory
    """
    if instance.status in ['Delivered', 'Open', 'Partially Delivered']:
        def create_delivery_je():
            try:
                models = get_models()
                JournalEntry = models.get('JournalEntry')
                JournalEntryLine = models.get('JournalEntryLine')
                Currency = models.get('Currency')
                
                print(f"🚚 Delivery #{instance.id} saved → Creating COGS Journal Entry")
                
                # Calculate total
                lines = instance.lines.all()
                if lines.exists():
                    total_amount = sum(line.total_amount for line in lines)
                else:
                    total_amount = instance.total_amount or Decimal('0')
                
                if total_amount <= 0:
                    print(f"⚠️ Delivery total is {total_amount}, skipping")
                    return
                
                # Delete old entries
                JournalEntry.objects.filter(
                    reference=f"DELIVERY-{instance.id}"
                ).delete()
                
                # COGS calculation (70% of sales)
                cogs_amount = total_amount * Decimal('0.70')
                currency = instance.currency or Currency.objects.first()
                
                # Get accounts
                cogs_account = get_account_by_code("5000")  # COGS
                inventory_account = get_account_by_code("1300")  # Inventory
                
                if not all([cogs_account, inventory_account]):
                    print("❌ Required delivery accounts not found!")
                    return
                
                # Create Journal Entry
                je = JournalEntry.objects.create(
                    doc_num=generate_doc_number("JE"),
                    posting_date=instance.posting_date,
                    reference=f"DELIVERY-{instance.id}",
                    remarks=f"Goods delivered to {instance.customer.name}",
                    currency=currency,
                    total_debit=cogs_amount,
                    total_credit=cogs_amount,
                    is_posted=True
                )
                
                # Create lines
                JournalEntryLine.objects.create(
                    journal_entry=je,
                    account=cogs_account,
                    debit_amount=cogs_amount,
                    credit_amount=Decimal('0'),
                    description=f"COGS - Delivery #{instance.id}"
                )
                
                JournalEntryLine.objects.create(
                    journal_entry=je,
                    account=inventory_account,
                    debit_amount=Decimal('0'),
                    credit_amount=cogs_amount,
                    description=f"Inventory reduction - Delivery #{instance.id}"
                )
                
                print(f"✅ Delivery Journal Entry {je.doc_num} created")
                
            except Exception as e:
                print(f"❌ Error creating delivery journal entry: {e}")
                import traceback
                traceback.print_exc()
                
        transaction.on_commit(create_delivery_je)

# ==================== DELETE SIGNALS ====================

@receiver(post_delete, sender='Sales.ARInvoice')
def delete_invoice_journal_entries(sender, instance, **kwargs):
    """AR Invoice Delete → Journal Entries Deleted"""
    try:
        models = get_models()
        JournalEntry = models.get('JournalEntry')
        
        if JournalEntry:
            deleted_count = JournalEntry.objects.filter(
                reference__in=[f"AR-INVOICE-{instance.id}", f"AR-PAYMENT-{instance.id}"]
            ).delete()[0]
            print(f"🗑️ AR Invoice #{instance.id} deleted → {deleted_count} Journal Entries deleted")
    except Exception as e:
        print(f"❌ Error deleting invoice journal entries: {e}")

@receiver(post_delete, sender='Sales.Delivery')
def delete_delivery_journal_entry(sender, instance, **kwargs):
    """Delivery Delete → Journal Entry Deleted"""
    try:
        models = get_models()
        JournalEntry = models.get('JournalEntry')
        
        if JournalEntry:
            deleted_count = JournalEntry.objects.filter(
                reference=f"DELIVERY-{instance.id}"
            ).delete()[0]
            print(f"🗑️ Delivery #{instance.id} deleted → {deleted_count} Journal Entry deleted")
    except Exception as e:
        print(f"❌ Error deleting delivery journal entry: {e}")

# ==================== LINE ITEM SIGNALS ====================

@receiver(post_save, sender='Sales.ARInvoiceLine')
def update_invoice_total_on_line_save(sender, instance, **kwargs):
    """Invoice Line Save → Invoice Total Updated → Journal Entry Updated"""
    def update_total():
        try:
            models = get_models()
            ARInvoice = models.get('ARInvoice')
            
            if not ARInvoice:
                return
                
            invoice = instance.invoice
            lines = invoice.lines.all()
            new_total = sum(line.total_amount for line in lines)
            
            print(f"📊 Invoice Line saved → Updating Invoice #{invoice.id} total: {new_total}")
            
            # Update without triggering signals
            ARInvoice.objects.filter(id=invoice.id).update(
                total_amount=new_total,
                payable_amount=new_total + (invoice.tax_amount or 0) - (invoice.discount_amount or 0),
                due_amount=(new_total + (invoice.tax_amount or 0) - (invoice.discount_amount or 0)) - (invoice.paid_amount or 0)
            )
            
        except Exception as e:
            print(f"❌ Error updating invoice total: {e}")
    
    transaction.on_commit(update_total)

print("📡 Sales signals loaded successfully")
