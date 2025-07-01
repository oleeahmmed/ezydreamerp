from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone

from ..models import GeneralLedger, ChartOfAccounts
from ..forms import GeneralLedgerForm, GeneralLedgerFilterForm

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class GeneralLedgerListView(GenericFilterView):
    model = GeneralLedger
    template_name = 'finance/general_ledger_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Finance.view_generalledger'
    filter_form_class = GeneralLedgerFilterForm
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-posting_date')
        
        # Filter by search query if provided
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                account__code__icontains=search_query
            ) | queryset.filter(
                account__name__icontains=search_query
            ) | queryset.filter(
                journal_entry__doc_num__icontains=search_query
            )
            
        # Apply account filter
        account = self.request.GET.get('account', '')
        if account:
            queryset = queryset.filter(account_id=account)
            
        # Apply journal entry filter
        journal_entry = self.request.GET.get('journal_entry', '')
        if journal_entry:
            queryset = queryset.filter(journal_entry_id=journal_entry)
            
        # Apply date range filter
        date_from = self.request.GET.get('date_from', '')
        if date_from:
            queryset = queryset.filter(posting_date__gte=date_from)
            
        date_to = self.request.GET.get('date_to', '')
        if date_to:
            queryset = queryset.filter(posting_date__lte=date_to)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "General Ledger",
            'subtitle': "View general ledger entries",
            'create_url': reverse_lazy('Finance:general_ledger_create'),
            'print_url': reverse_lazy('Finance:general_ledger_print_list'),
            'export_url': reverse_lazy('Finance:general_ledger_export'),
            'model_name': "general ledger entry",
            'can_create': self.request.user.has_perm('Finance.add_generalledger'),
            'can_view': self.request.user.has_perm('Finance.view_generalledger'),
            'can_update': self.request.user.has_perm('Finance.change_generalledger'),
            'can_delete': self.request.user.has_perm('Finance.delete_generalledger'),
            'can_print': self.request.user.has_perm('Finance.view_generalledger'),
            'can_export': self.request.user.has_perm('Finance.view_generalledger'),
            'can_bulk_delete': self.request.user.has_perm('Finance.delete_generalledger'),
        })
        return context

class GeneralLedgerCreateView(SuccessMessageMixin, CreateView):
    model = GeneralLedger
    form_class = GeneralLedgerForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Finance:general_ledger_list')
    success_message = "General Ledger entry was created successfully"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create General Ledger Entry",
            'subtitle': "Add a new general ledger entry",
            'cancel_url': reverse_lazy('Finance:general_ledger_list'),
        })
        return context

class GeneralLedgerUpdateView(SuccessMessageMixin, UpdateView):
    model = GeneralLedger
    form_class = GeneralLedgerForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Finance:general_ledger_list')
    success_message = "General Ledger entry was updated successfully"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update General Ledger Entry",
            'subtitle': f"Edit general ledger entry for {self.object.account.code}",
            'cancel_url': reverse_lazy('Finance:general_ledger_detail', kwargs={'pk': self.object.pk}),
        })
        return context

class GeneralLedgerDetailView(DetailView):
    model = GeneralLedger
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "General Ledger Entry Details",
            'subtitle': f"View details for {self.object.account.code}",
            'form': GeneralLedgerForm(instance=self.object),
            'readonly': True,
            'print_url': reverse_lazy('Finance:general_ledger_print_detail', kwargs={'pk': self.object.pk}),
            'update_url': reverse_lazy('Finance:general_ledger_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('Finance:general_ledger_delete', kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('Finance:general_ledger_list'),
            'can_update': self.request.user.has_perm('Finance.change_generalledger'),
            'can_delete': self.request.user.has_perm('Finance.delete_generalledger'),
        })
        return context

class GeneralLedgerDeleteView(GenericDeleteView):
    model = GeneralLedger
    success_url = reverse_lazy('Finance:general_ledger_list')
    permission_required = 'Finance.delete_generalledger'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to General Ledger detail view.
        """
        return reverse_lazy('Finance:general_ledger_detail', kwargs={'pk': self.object.pk})

class GeneralLedgerExportView(BaseExportView):
    """
    Export view for General Ledger.
    """
    model = GeneralLedger
    filename = "general_ledger.csv"
    permission_required = "Finance.view_generalledger"
    field_names = ["Account", "Posting Date", "Journal Entry", "Debit Amount", 
                  "Credit Amount", "Balance", "Currency"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed.
        """
        # Apply filters if provided
        account = request.GET.get('account', '')
        if account:
            queryset = queryset.filter(account_id=account)
            
        journal_entry = request.GET.get('journal_entry', '')
        if journal_entry:
            queryset = queryset.filter(journal_entry_id=journal_entry)
            
        date_from = request.GET.get('date_from', '')
        if date_from:
            queryset = queryset.filter(posting_date__gte=date_from)
            
        date_to = request.GET.get('date_to', '')
        if date_to:
            queryset = queryset.filter(posting_date__lte=date_to)
            
        return queryset

class GeneralLedgerPrintView(ListView):
    model = GeneralLedger
    template_name = 'finance/general_ledger_print_list.html'
    context_object_name = 'general_ledger_entries'
    permission_required = 'Finance.view_generalledger'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'General Ledger Entries'
        context['user'] = self.request.user
        context['timestamp'] = timezone.now()
        return context

class GeneralLedgerPrintDetailView(DetailView):
    model = GeneralLedger
    template_name = 'finance/general_ledger_print_detail.html'
    context_object_name = 'general_ledger'
    permission_required = 'Finance.view_generalledger'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'General Ledger Entry: {self.object.account.code}'
        context['user'] = self.request.user
        context['timestamp'] = timezone.now()
        return context

class GeneralLedgerBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for General Ledger entries.
    """
    model = GeneralLedger
    permission_required = "Finance.delete_generalledger"
    display_fields = ["account", "posting_date", "journal_entry", "debit_amount", "credit_amount", "balance"]
    cancel_url = reverse_lazy("Finance:general_ledger_list")
    success_url = reverse_lazy("Finance:general_ledger_list")

