from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from django.utils.translation import gettext_lazy as _
from ..models import ChartOfAccounts, GeneralLedger, AccountType
from django import forms

class ProfitLossFilterForm(forms.Form):
    start_date = forms.DateField(
        label=_("Start Date"),
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    end_date = forms.DateField(
        label=_("End Date"),
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )

class ProfitAndLossView(TemplateView):
    template_name = 'finance/profit_loss.html'
    permission_required = 'Finance.view_generalledger'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Initialize form with default values
        form = ProfitLossFilterForm(self.request.GET or {
            'start_date': datetime.now().date().replace(day=1),
            'end_date': datetime.now().date()
        })

        # Validate and extract date range
        start_date = datetime.now().date().replace(day=1)
        end_date = datetime.now().date()
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

        # Ensure start_date is before end_date
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        # Initialize data structures
        revenue_data = []
        expense_data = []
        total_revenue = 0
        total_expenses = 0

        # Get revenue and expense account types
        revenue_types = AccountType.objects.filter(name__icontains='revenue')
        expense_types = AccountType.objects.filter(name__icontains='expense')

        # Process Revenue Accounts
        revenue_accounts = ChartOfAccounts.objects.filter(account_type__in=revenue_types)
        for account in revenue_accounts:
            gl_entries = GeneralLedger.objects.filter(
                account=account,
                posting_date__range=[start_date, end_date]
            )
            credit_sum = gl_entries.aggregate(total=Sum('credit_amount'))['total'] or 0
            debit_sum = gl_entries.aggregate(total=Sum('debit_amount'))['total'] or 0
            amount = credit_sum - debit_sum  # Revenue: net credits

            if amount != 0:
                revenue_data.append({
                    'account': account,
                    'amount': amount,
                })
                total_revenue += amount

        # Process Expense Accounts
        expense_accounts = ChartOfAccounts.objects.filter(account_type__in=expense_types)
        for account in expense_accounts:
            gl_entries = GeneralLedger.objects.filter(
                account=account,
                posting_date__range=[start_date, end_date]  # Fixed date range
            )
            debit_sum = gl_entries.aggregate(total=Sum('debit_amount'))['total'] or 0
            credit_sum = gl_entries.aggregate(total=Sum('credit_amount'))['total'] or 0
            amount = debit_sum - credit_sum  # Expenses: net debits

            if amount != 0:
                expense_data.append({
                    'account': account,
                    'amount': amount,
                })
                total_expenses += amount

        net_profit = total_revenue - total_expenses

        context.update({
            'title': _('Profit and Loss Report'),
            'subtitle': f'From {start_date.strftime("%B %d, %Y")} to {end_date.strftime("%B %d, %Y")}',
            'form': form,
            'revenue_data': revenue_data,
            'expense_data': expense_data,
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'start_date': start_date,
            'end_date': end_date,
            'generated_on': timezone.now(),
        })
        return context