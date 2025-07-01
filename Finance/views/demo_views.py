from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.views import View
from django.utils import timezone
from django import forms
from django.db import transaction
from django.db.models import signals
from Finance.models import AccountType, ChartOfAccounts, JournalEntry, JournalEntryLine, CostCenter, GeneralLedger
from global_settings.models import Currency
import logging

# Set up logging
logger = logging.getLogger(__name__)

class DemoConfigForm(forms.Form):
    """Form for managing demo data import/delete with configuration options"""
    ACTION_CHOICES = (
        ('import', 'Import Demo Data'),
        ('delete', 'Delete Demo Data'),
    )
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'peer w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent premium-input text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))] focus:bg-[hsl(var(--accent))] appearance-none',
        }),
        label='Action'
    )
    
    include_journal_entries = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'sr-only peer',
        }),
        label='Include Sample Journal Entries'
    )

class DemoAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class DemoConfigView(DemoAccessMixin, View):
    template_name = 'finance/demo_config.html'
    permission_required = 'Finance.change_accounttype'
    form_class = DemoConfigForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'form': form,
            'screen_title': 'Sample Data Setup',
            'subtitle_title': 'Import or delete sample data for the finance module',
            'cancel_url': reverse_lazy('Finance:account_type_list'),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            include_journal_entries = form.cleaned_data['include_journal_entries']
            
            try:
                if action == 'import':
                    # Currency
                    bdt, _ = Currency.objects.get_or_create(
                        code='BDT',
                        defaults={
                            'name': 'Bangladeshi Taka',
                            'exchange_rate': 1
                        }
                    )

                    # Account Types
                    default_account_types = [
                        {"code": "100", "name": "Asset", "is_debit": True},
                        {"code": "200", "name": "Liability", "is_debit": False},
                        {"code": "300", "name": "Equity", "is_debit": False},
                        {"code": "400", "name": "Revenue", "is_debit": False},
                        {"code": "500", "name": "Expense", "is_debit": True},
                    ]

                    for at in default_account_types:
                        AccountType.objects.get_or_create(
                            code=at["code"], 
                            defaults={"name": at["name"], "is_debit": at["is_debit"]}
                        )

                    # Cost Centers
                    main_cost_center, _ = CostCenter.objects.get_or_create(
                        code='CC100',
                        defaults={'name': 'Main Office'}
                    )
                    branch_cost_center, _ = CostCenter.objects.get_or_create(
                        code='CC200',
                        defaults={'name': 'Branch Office'}
                    )

                    # Extended Chart of Accounts for Sales Module
                    created_accounts = {}
                    
                    # Assets (100 series)
                    cash, _ = ChartOfAccounts.objects.get_or_create(
                        code="1000", 
                        defaults={
                            "name": "Cash", 
                            "account_type": AccountType.objects.get(code="100"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['cash'] = cash
                    
                    bank, _ = ChartOfAccounts.objects.get_or_create(
                        code="1100", 
                        defaults={
                            "name": "Bank Account", 
                            "account_type": AccountType.objects.get(code="100"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['bank'] = bank
                    
                    accounts_receivable, _ = ChartOfAccounts.objects.get_or_create(
                        code="1200", 
                        defaults={
                            "name": "Accounts Receivable", 
                            "account_type": AccountType.objects.get(code="100"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['accounts_receivable'] = accounts_receivable
                    
                    inventory, _ = ChartOfAccounts.objects.get_or_create(
                        code="1300", 
                        defaults={
                            "name": "Inventory", 
                            "account_type": AccountType.objects.get(code="100"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['inventory'] = inventory
                    
                    # Liabilities (200 series)
                    accounts_payable, _ = ChartOfAccounts.objects.get_or_create(
                        code="2000", 
                        defaults={
                            "name": "Accounts Payable", 
                            "account_type": AccountType.objects.get(code="200"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['accounts_payable'] = accounts_payable
                    
                    # Revenue (400 series)
                    sales_revenue, _ = ChartOfAccounts.objects.get_or_create(
                        code="4000", 
                        defaults={
                            "name": "Sales Revenue", 
                            "account_type": AccountType.objects.get(code="400"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['sales_revenue'] = sales_revenue
                    
                    sales_returns, _ = ChartOfAccounts.objects.get_or_create(
                        code="4100", 
                        defaults={
                            "name": "Sales Returns", 
                            "account_type": AccountType.objects.get(code="400"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['sales_returns'] = sales_returns
                    
                    # Expenses (500 series)
                    cogs, _ = ChartOfAccounts.objects.get_or_create(
                        code="5000", 
                        defaults={
                            "name": "Cost of Goods Sold", 
                            "account_type": AccountType.objects.get(code="500"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['cogs'] = cogs
                    
                    office_rent, _ = ChartOfAccounts.objects.get_or_create(
                        code="5100", 
                        defaults={
                            "name": "Office Rent", 
                            "account_type": AccountType.objects.get(code="500"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['office_rent'] = office_rent

                    if include_journal_entries:
                        print("🔔 Creating sample journal entries with automatic GL posting...")
                        
                        # Journal Entry 1 (Sales Invoice)
                        entry1, created1 = JournalEntry.objects.get_or_create(
                            doc_num="JE0001",
                            defaults={
                                "posting_date": timezone.now().date(),
                                "reference": "AR-INVOICE-1",
                                "remarks": "Sales Invoice - Customer ABC",
                                "currency": bdt,
                                "total_debit": 10000,
                                "total_credit": 10000,
                                "is_posted": True,
                                "cost_center": main_cost_center,
                            }
                        )
                        logger.info(f"JournalEntry JE0001 created: {created1}")
                        
                        if created1:
                            print(f"📝 Creating lines for JE0001...")
                            # Dr. Accounts Receivable, Cr. Sales Revenue
                            line1 = JournalEntryLine.objects.create(
                                journal_entry=entry1,
                                account=created_accounts['accounts_receivable'],
                                debit_amount=10000,
                                credit_amount=0,
                                description="AR Invoice - Customer ABC"
                            )
                            line2 = JournalEntryLine.objects.create(
                                journal_entry=entry1,
                                account=created_accounts['sales_revenue'],
                                debit_amount=0,
                                credit_amount=10000,
                                description="Sales Revenue"
                            )
                            print(f"✅ Created {entry1.lines.count()} lines for JE0001")

                        # Journal Entry 2 (Payment Received)
                        entry2, created2 = JournalEntry.objects.get_or_create(
                            doc_num="JE0002",
                            defaults={
                                "posting_date": timezone.now().date(),
                                "reference": "AR-PAYMENT-1",
                                "remarks": "Payment received from Customer ABC",
                                "currency": bdt,
                                "total_debit": 10000,
                                "total_credit": 10000,
                                "is_posted": True,
                                "cost_center": main_cost_center,
                            }
                        )
                        logger.info(f"JournalEntry JE0002 created: {created2}")
                        
                        if created2:
                            print(f"📝 Creating lines for JE0002...")
                            # Dr. Cash, Cr. Accounts Receivable
                            line1 = JournalEntryLine.objects.create(
                                journal_entry=entry2,
                                account=created_accounts['cash'],
                                debit_amount=10000,
                                credit_amount=0,
                                description="Payment received"
                            )
                            line2 = JournalEntryLine.objects.create(
                                journal_entry=entry2,
                                account=created_accounts['accounts_receivable'],
                                debit_amount=0,
                                credit_amount=10000,
                                description="AR Payment"
                            )
                            print(f"✅ Created {entry2.lines.count()} lines for JE0002")

                        # Journal Entry 3 (Delivery - COGS)
                        entry3, created3 = JournalEntry.objects.get_or_create(
                            doc_num="JE0003",
                            defaults={
                                "posting_date": timezone.now().date(),
                                "reference": "DELIVERY-1",
                                "remarks": "Goods delivered to Customer ABC",
                                "currency": bdt,
                                "total_debit": 7000,
                                "total_credit": 7000,
                                "is_posted": True,
                                "cost_center": main_cost_center,
                            }
                        )
                        logger.info(f"JournalEntry JE0003 created: {created3}")
                        
                        if created3:
                            print(f"📝 Creating lines for JE0003...")
                            # Dr. COGS, Cr. Inventory
                            line1 = JournalEntryLine.objects.create(
                                journal_entry=entry3,
                                account=created_accounts['cogs'],
                                debit_amount=7000,
                                credit_amount=0,
                                description="Cost of goods sold"
                            )
                            line2 = JournalEntryLine.objects.create(
                                journal_entry=entry3,
                                account=created_accounts['inventory'],
                                debit_amount=0,
                                credit_amount=7000,
                                description="Inventory reduction"
                            )
                            print(f"✅ Created {entry3.lines.count()} lines for JE0003")

                        # Force GL creation by triggering the signal manually if needed
                        print("🔄 Ensuring GL entries are created...")
                        
                        # Check and create GL entries for each journal entry
                        for je in [entry1, entry2, entry3]:
                            if je.is_posted:
                                gl_count = GeneralLedger.objects.filter(journal_entry=je).count()
                                lines_count = je.lines.count()
                                print(f"📊 JE {je.doc_num}: {lines_count} lines, {gl_count} GL entries")
                                
                                if gl_count != lines_count:
                                    print(f"⚠️ GL count mismatch for {je.doc_num}, creating GL entries...")
                                    
                                    # Delete existing GL entries
                                    GeneralLedger.objects.filter(journal_entry=je).delete()
                                    
                                    # Create GL entries manually
                                    for line in je.lines.all():
                                        if line.account.account_type.is_debit:
                                            balance = line.debit_amount - line.credit_amount
                                        else:
                                            balance = line.credit_amount - line.debit_amount
                                        
                                        gl_entry = GeneralLedger.objects.create(
                                            account=line.account,
                                            posting_date=je.posting_date,
                                            journal_entry=je,
                                            debit_amount=line.debit_amount,
                                            credit_amount=line.credit_amount,
                                            balance=balance,
                                            currency=je.currency,
                                            cost_center=je.cost_center
                                        )
                                        print(f"✅ Created GL entry for {line.account.code}: Dr={line.debit_amount}, Cr={line.credit_amount}, Balance={balance}")

                        # Final count verification
                        total_je = JournalEntry.objects.count()
                        total_lines = JournalEntryLine.objects.count()
                        total_gl = GeneralLedger.objects.count()
                        
                        print(f"📈 Final counts: {total_je} Journal Entries, {total_lines} Lines, {total_gl} GL Entries")
                        
                        if total_lines != total_gl:
                            logger.warning(f"GL count mismatch: {total_lines} lines vs {total_gl} GL entries")
                        else:
                            logger.info(f"✅ GL entries match lines: {total_gl} entries created")

                    messages.success(request, f"Demo data imported successfully with extended sales accounts. Created {ChartOfAccounts.objects.count()} accounts.")

                elif action == 'delete':
                    # Delete in reverse order to respect foreign key constraints
                    lines_deleted = JournalEntryLine.objects.all().delete()[0]
                    entries_deleted = JournalEntry.objects.all().delete()[0]
                    ledger_deleted = GeneralLedger.objects.all().delete()[0]
                    accounts_deleted = ChartOfAccounts.objects.all().delete()[0]
                    account_types_deleted = AccountType.objects.all().delete()[0]
                    cost_centers_deleted = CostCenter.objects.all().delete()[0]

                    messages.success(request, (
                        f"Deleted all demo data successfully. "
                        f"Deleted {lines_deleted} JournalEntryLine, {entries_deleted} JournalEntry, "
                        f"{ledger_deleted} GeneralLedger, {accounts_deleted} ChartOfAccounts, "
                        f"{account_types_deleted} AccountType, {cost_centers_deleted} CostCenter"
                    ))

            except Exception as e:
                logger.error(f"Error performing {action} action: {str(e)}")
                messages.error(request, f"Error performing {action} action: {str(e)}")
                import traceback
                traceback.print_exc()

        else:
            messages.error(request, "Invalid form submission. Please check the fields.")

        return redirect('Finance:demo_config')
