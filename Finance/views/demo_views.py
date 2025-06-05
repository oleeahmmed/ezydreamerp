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

                    # Chart of Accounts
                    created_accounts = {}
                    cash, _ = ChartOfAccounts.objects.get_or_create(
                        code="1000", 
                        defaults={
                            "name": "Cash", 
                            "account_type": AccountType.objects.get(code="100"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['cash'] = cash
                    sales, _ = ChartOfAccounts.objects.get_or_create(
                        code="4000", 
                        defaults={
                            "name": "Sales Revenue", 
                            "account_type": AccountType.objects.get(code="400"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['sales'] = sales
                    rent_expense, _ = ChartOfAccounts.objects.get_or_create(
                        code="5000", 
                        defaults={
                            "name": "Office Rent", 
                            "account_type": AccountType.objects.get(code="500"), 
                            "currency": bdt
                        }
                    )
                    created_accounts['rent_expense'] = rent_expense

                    if include_journal_entries:
                        # Disconnect the post_save signal to avoid duplicates
                        from Finance.signals import journal_entry
                        # signals.post_save.disconnect(journal_entry.post_journal_to_gl, sender=JournalEntry)

                        try:
                            with transaction.atomic():
                                # Journal Entry 1 (Sales)
                                if 'cash' in created_accounts and 'sales' in created_accounts:
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
                                    logger.info(f"JournalEntry JE0001 created: {created}")
                                    if created:
                                        # Journal Entry Lines
                                        line1 = JournalEntryLine.objects.create(
                                            journal_entry=entry,
                                            account=created_accounts['cash'],
                                            debit_amount=5000,
                                            credit_amount=0,
                                            description="Cash received"
                                        )
                                        line2 = JournalEntryLine.objects.create(
                                            journal_entry=entry,
                                            account=created_accounts['sales'],
                                            debit_amount=0,
                                            credit_amount=5000,
                                            description="Chair sales"
                                        )

                                        # GeneralLedger Entries
                                        for line in [line1, line2]:
                                            balance = line.debit_amount - line.credit_amount
                                            gl_entry = GeneralLedger.objects.create(
                                                account=line.account,
                                                posting_date=entry.posting_date,
                                                journal_entry=entry,
                                                debit_amount=line.debit_amount,
                                                credit_amount=line.credit_amount,
                                                balance=balance,
                                                currency=entry.currency
                                            )
                                            logger.info(f"GeneralLedger created for {line.account.code}: Debit={line.debit_amount}, Credit={line.credit_amount}, Balance={balance}")

                                # Journal Entry 2 (Rent Expense)
                                if 'rent_expense' in created_accounts and 'cash' in created_accounts:
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
                                    logger.info(f"JournalEntry JE0002 created: {created2}")
                                    if created2:
                                        # Journal Entry Lines
                                        line1 = JournalEntryLine.objects.create(
                                            journal_entry=entry2,
                                            account=created_accounts['rent_expense'],
                                            debit_amount=2000,
                                            credit_amount=0,
                                            description="Branch rent expense"
                                        )
                                        line2 = JournalEntryLine.objects.create(
                                            journal_entry=entry2,
                                            account=created_accounts['cash'],
                                            debit_amount=0,
                                            credit_amount=2000,
                                            description="Paid from cash"
                                        )

                                        # GeneralLedger Entries
                                        for line in [line1, line2]:
                                            balance = line.debit_amount - line.credit_amount
                                            gl_entry = GeneralLedger.objects.create(
                                                account=line.account,
                                                posting_date=entry2.posting_date,
                                                journal_entry=entry2,
                                                debit_amount=line.debit_amount,
                                                credit_amount=line.credit_amount,
                                                balance=balance,
                                                currency=entry2.currency
                                            )
                                            logger.info(f"GeneralLedger created for {line.account.code}: Debit={line.debit_amount}, Credit={line.credit_amount}, Balance={balance}")

                        finally:
                            # Reconnect the signal
                            signals.post_save.connect(journal_entry.post_journal_to_gl, sender=JournalEntry)

                    messages.success(request, "Demo data imported successfully.")

                elif action == 'delete':
                    # Delete in reverse order to respect foreign key constraints
                    lines_deleted = JournalEntryLine.objects.all().delete()[0]  # Count deleted JournalEntryLine
                    entries_deleted = JournalEntry.objects.all().delete()[0]   # Count deleted JournalEntry
                    ledger_deleted = GeneralLedger.objects.all().delete()[0]   # Count deleted GeneralLedger
                    accounts_deleted = ChartOfAccounts.objects.all().delete()[0]  # Count deleted ChartOfAccounts
                    account_types_deleted = AccountType.objects.all().delete()[0] # Count deleted AccountType
                    cost_centers_deleted = CostCenter.objects.all().delete()[0]   # Count deleted CostCenter

                    messages.success(request, (
                        f"Deleted all demo data successfully. "
                        f"Deleted {lines_deleted} JournalEntryLine, {entries_deleted} JournalEntry, "
                        f"{ledger_deleted} GeneralLedger, {accounts_deleted} ChartOfAccounts, "
                        f"{account_types_deleted} AccountType, {cost_centers_deleted} CostCenter, "
                    ))

            except Exception as e:
                logger.error(f"Error performing {action} action: {str(e)}")
                messages.error(request, f"Error performing {action} action: {str(e)}")

        else:
            messages.error(request, "Invalid form submission. Please check the fields.")

        return redirect('Finance:demo_config')