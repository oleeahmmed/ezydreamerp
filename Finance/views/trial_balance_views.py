from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone
from django.urls import reverse_lazy

from ..models import ChartOfAccounts, GeneralLedger

class TrialBalanceView(TemplateView):
    template_name = 'finance/trial_balance.html'
    permission_required = 'Finance.view_generalledger'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        trial_data = []
        total_debit = 0
        total_credit = 0

        accounts = ChartOfAccounts.objects.all()

        for account in accounts:
            gl_entries = GeneralLedger.objects.filter(account=account)
            debit_sum = gl_entries.aggregate(total=Sum('debit_amount'))['total'] or 0
            credit_sum = gl_entries.aggregate(total=Sum('credit_amount'))['total'] or 0
            balance = debit_sum - credit_sum

            if account.account_type.is_debit:
                debit = balance if balance >= 0 else 0
                credit = abs(balance) if balance < 0 else 0
            else:
                credit = balance if balance >= 0 else 0
                debit = abs(balance) if balance < 0 else 0

            total_debit += debit
            total_credit += credit

            trial_data.append({
                'account': account,
                'debit': debit,
                'credit': credit,
            })

        context.update({
            'title': 'Trial Balance',
            'subtitle': 'Summary of all accounts',
            'trial_data': trial_data,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'generated_on': timezone.now(),
            'print_url': reverse_lazy('Finance:trial_balance_print'),
        })
        return context
