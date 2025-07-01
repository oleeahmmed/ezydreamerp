from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from ..models import ChartOfAccounts, GeneralLedger, AccountType

class BalanceSheetView(TemplateView):
    template_name = 'finance/balance_sheet.html'
    permission_required = 'Finance.view_generalledger'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get account types
        asset_types = AccountType.objects.filter(code='100')  # Assets
        liability_types = AccountType.objects.filter(code='200')  # Liabilities
        equity_types = AccountType.objects.filter(code='300')  # Equity

        # Initialize data structures
        asset_data = []
        liability_data = []
        equity_data = []
        
        total_assets = Decimal('0')
        total_liabilities = Decimal('0')
        total_equity = Decimal('0')

        print("📊 Generating Balance Sheet...")

        # Process Assets (100 series)
        asset_accounts = ChartOfAccounts.objects.filter(
            account_type__in=asset_types
        ).order_by('code')
        
        for account in asset_accounts:
            gl_entries = GeneralLedger.objects.filter(account=account)
            debit_sum = gl_entries.aggregate(total=Sum('debit_amount'))['total'] or Decimal('0')
            credit_sum = gl_entries.aggregate(total=Sum('credit_amount'))['total'] or Decimal('0')
            balance = debit_sum - credit_sum  # Assets have debit balances
            
            if balance != 0:
                asset_data.append({
                    'account': account,
                    'account_code': account.code,
                    'account_name': account.name,
                    'balance': balance,
                })
                total_assets += balance

        # Process Liabilities (200 series)
        liability_accounts = ChartOfAccounts.objects.filter(
            account_type__in=liability_types
        ).order_by('code')
        
        for account in liability_accounts:
            gl_entries = GeneralLedger.objects.filter(account=account)
            debit_sum = gl_entries.aggregate(total=Sum('debit_amount'))['total'] or Decimal('0')
            credit_sum = gl_entries.aggregate(total=Sum('credit_amount'))['total'] or Decimal('0')
            balance = credit_sum - debit_sum  # Liabilities have credit balances
            
            if balance != 0:
                liability_data.append({
                    'account': account,
                    'account_code': account.code,
                    'account_name': account.name,
                    'balance': balance,
                })
                total_liabilities += balance

        # Process Equity (300 series)
        equity_accounts = ChartOfAccounts.objects.filter(
            account_type__in=equity_types
        ).order_by('code')
        
        for account in equity_accounts:
            gl_entries = GeneralLedger.objects.filter(account=account)
            debit_sum = gl_entries.aggregate(total=Sum('debit_amount'))['total'] or Decimal('0')
            credit_sum = gl_entries.aggregate(total=Sum('credit_amount'))['total'] or Decimal('0')
            balance = credit_sum - debit_sum  # Equity has credit balances
            
            if balance != 0:
                equity_data.append({
                    'account': account,
                    'account_code': account.code,
                    'account_name': account.name,
                    'balance': balance,
                })
                total_equity += balance

        # Calculate totals
        total_liabilities_equity = total_liabilities + total_equity
        balance_difference = total_assets - total_liabilities_equity
        is_balanced = abs(balance_difference) < Decimal('0.01')

        print(f"📈 Balance Sheet Summary:")
        print(f"   Total Assets: {total_assets}")
        print(f"   Total Liabilities: {total_liabilities}")
        print(f"   Total Equity: {total_equity}")
        print(f"   Balanced: {is_balanced}")

        context.update({
            'title': _('Balance Sheet'),
            'subtitle': f'As of {timezone.now().date()}',
            'asset_data': asset_data,
            'liability_data': liability_data,
            'equity_data': equity_data,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'total_liabilities_equity': total_liabilities_equity,
            'balance_difference': balance_difference,
            'is_balanced': is_balanced,
            'generated_on': timezone.now(),
        })
        return context
