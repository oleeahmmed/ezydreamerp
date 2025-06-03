from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from django import forms
from django.utils.translation import gettext_lazy as _
from ..models import ChartOfAccounts, GeneralLedger, AccountType

class BalanceSheetFilterForm(forms.Form):
    end_date = forms.DateField(
        label=_("As of Date"),
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )

class BalanceSheetView(TemplateView):
    template_name = 'finance/balance_sheet.html'
    permission_required = 'Finance.view_generalledger'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Initialize form
        form = BalanceSheetFilterForm(self.request.GET or {
            'end_date': datetime.now().date()
        })

        # Validate and extract date
        end_date = datetime.now().date()
        if form.is_valid():
            end_date = form.cleaned_data['end_date']

        # Initialize data structures
        asset_data = []
        liability_data = []
        equity_data = []
        total_assets = 0
        total_liabilities = 0
        total_equity = 0

        # Get account types
        asset_types = AccountType.objects.filter(name__icontains='asset')
        liability_types = AccountType.objects.filter(name__icontains='liability')
        equity_types = AccountType.objects.filter(name__icontains='equity')

        # Process Asset Accounts
        asset_accounts = ChartOfAccounts.objects.filter(account_type__in=asset_types)
        for account in asset_accounts:
            gl_entries = GeneralLedger.objects.filter(
                account=account,
                posting_date__lte=end_date
            )
            debit_sum = gl_entries.aggregate(total=Sum('debit_amount'))['total'] or 0
            credit_sum = gl_entries.aggregate(total=Sum('credit_amount'))['total'] or 0
            balance = debit_sum - credit_sum  # Assets increase with debits

            if balance != 0:
                asset_data.append({
                    'account': account,
                    'balance': balance,
                })
                total_assets += balance

        # Process Liability Accounts
        liability_accounts = ChartOfAccounts.objects.filter(account_type__in=liability_types)
        for account in liability_accounts:
            gl_entries = GeneralLedger.objects.filter(
                account=account,
                posting_date__lte=end_date
            )
            debit_sum = gl_entries.aggregate(total=Sum('debit_amount'))['total'] or 0
            credit_sum = gl_entries.aggregate(total=Sum('credit_amount'))['total'] or 0
            balance = credit_sum - debit_sum  # Liabilities increase with credits

            if balance != 0:
                liability_data.append({
                    'account': account,
                    'balance': balance,
                })
                total_liabilities += balance

        # Process Equity Accounts
        equity_accounts = ChartOfAccounts.objects.filter(account_type__in=equity_types)
        for account in equity_accounts:
            gl_entries = GeneralLedger.objects.filter(
                account=account,
                posting_date__lte=end_date
            )
            debit_sum = gl_entries.aggregate(total=Sum('debit_amount'))['total'] or 0
            credit_sum = gl_entries.aggregate(total=Sum('credit_amount'))['total'] or 0
            balance = credit_sum - debit_sum  # Equity increases with credits

            if balance != 0:
                equity_data.append({
                    'account': account,
                    'balance': balance,
                })
                total_equity += balance

        # Total Liabilities + Equity
        total_liabilities_equity = total_liabilities + total_equity

        context.update({
            'title': 'Balance Sheet',
            'subtitle': f'As of {end_date.strftime("%B %d, %Y")}',
            'form': form,
            'asset_data': asset_data,
            'liability_data': liability_data,
            'equity_data': equity_data,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'total_liabilities_equity': total_liabilities_equity,
            'end_date': end_date,
            'generated_on': timezone.now(),
        })
        return context