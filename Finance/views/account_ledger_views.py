from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from ..models import ChartOfAccounts, GeneralLedger

class AccountLedgerView(TemplateView):
    template_name = 'finance/account_ledger.html'
    permission_required = 'Finance.view_generalledger'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        account_id = kwargs.get('account_id')
        account = get_object_or_404(ChartOfAccounts, id=account_id)
        
        # Get all GL entries for this account
        gl_entries = GeneralLedger.objects.filter(
            account=account
        ).order_by('posting_date', 'id')
        
        # Calculate running balance
        ledger_data = []
        running_balance = Decimal('0')
        
        for entry in gl_entries:
            if account.account_type.is_debit:
                # Debit account: Dr increases, Cr decreases
                running_balance += entry.debit_amount - entry.credit_amount
            else:
                # Credit account: Cr increases, Dr decreases
                running_balance += entry.credit_amount - entry.debit_amount
            
            ledger_data.append({
                'entry': entry,
                'running_balance': running_balance,
            })
        
        # Calculate totals
        total_debits = gl_entries.aggregate(total=Sum('debit_amount'))['total'] or Decimal('0')
        total_credits = gl_entries.aggregate(total=Sum('credit_amount'))['total'] or Decimal('0')
        
        context.update({
            'title': f'Account Ledger - {account.code}',
            'subtitle': account.name,
            'account': account,
            'ledger_data': ledger_data,
            'total_debits': total_debits,
            'total_credits': total_credits,
            'final_balance': running_balance,
            'generated_on': timezone.now(),
        })
        return context
