from django.views.generic import TemplateView
from django.db.models import Sum, Q
from django.utils import timezone
from django.urls import reverse_lazy
from decimal import Decimal

from ..models import ChartOfAccounts, GeneralLedger

class TrialBalanceView(TemplateView):
    template_name = 'finance/trial_balance.html'
    permission_required = 'Finance.view_generalledger'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        trial_data = []
        total_debit = Decimal('0')
        total_credit = Decimal('0')

        # Get all accounts that have GL entries
        accounts = ChartOfAccounts.objects.filter(
            id__in=GeneralLedger.objects.values_list('account_id', flat=True).distinct()
        ).order_by('code')

        print("🔍 Calculating Trial Balance...")

        for account in accounts:
            # Get all GL entries for this account
            gl_entries = GeneralLedger.objects.filter(account=account)
            
            # Calculate total debits and credits
            debit_sum = gl_entries.aggregate(total=Sum('debit_amount'))['total'] or Decimal('0')
            credit_sum = gl_entries.aggregate(total=Sum('credit_amount'))['total'] or Decimal('0')
            
            print(f"📊 Account {account.code}: Dr={debit_sum}, Cr={credit_sum}")
            
            # Calculate net balance
            net_balance = debit_sum - credit_sum
            
            # Determine trial balance presentation
            if account.account_type.is_debit:
                # Debit accounts (Assets, Expenses): 
                # Positive balance = Debit side, Negative balance = Credit side
                if net_balance >= 0:
                    trial_debit = net_balance
                    trial_credit = Decimal('0')
                else:
                    trial_debit = Decimal('0')
                    trial_credit = abs(net_balance)
            else:
                # Credit accounts (Liabilities, Equity, Revenue):
                # Positive balance = Credit side, Negative balance = Debit side
                if net_balance >= 0:
                    trial_debit = Decimal('0')
                    trial_credit = net_balance
                else:
                    trial_debit = abs(net_balance)
                    trial_credit = Decimal('0')

            # Only include accounts with non-zero balances
            if trial_debit != 0 or trial_credit != 0:
                trial_data.append({
                    'account': account,
                    'account_code': account.code,
                    'account_name': account.name,
                    'account_type': account.account_type.name,
                    'is_debit_account': account.account_type.is_debit,
                    'debit': trial_debit,
                    'credit': trial_credit,
                    'net_balance': net_balance,
                })
                
                total_debit += trial_debit
                total_credit += trial_credit
                
                print(f"✅ {account.code}: Trial Dr={trial_debit}, Trial Cr={trial_credit}")

        # Check if trial balance balances
        balance_difference = total_debit - total_credit
        is_balanced = abs(balance_difference) < Decimal('0.01')  # Allow for small rounding differences
        
        print(f"📈 Trial Balance Totals: Dr={total_debit}, Cr={total_credit}")
        print(f"⚖️ Balanced: {is_balanced}, Difference: {balance_difference}")

        context.update({
            'title': 'Trial Balance',
            'subtitle': f'As of {timezone.now().date()}',
            'trial_data': trial_data,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'balance_difference': balance_difference,
            'is_balanced': is_balanced,
            'generated_on': timezone.now(),
            'print_url': reverse_lazy('Finance:trial_balance_print'),
        })
        return context
