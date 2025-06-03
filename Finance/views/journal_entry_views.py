from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.utils import timezone

from ..models import JournalEntry, JournalEntryLine, ChartOfAccounts
from ..forms import JournalEntryForm, JournalEntryLineFormSet, JournalEntryFilterForm, JournalEntryExtraInfoForm

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class JournalEntryListView(GenericFilterView):
    model = JournalEntry
    template_name = 'finance/journal_entry_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Finance.view_journalentry'
    filter_form_class = JournalEntryFilterForm
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-posting_date')
        
        # Filter by search query if provided
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                doc_num__icontains=search_query
            ) | queryset.filter(
                reference__icontains=search_query
            ) | queryset.filter(
                remarks__icontains=search_query
            )
            
        # Apply date range filter
        date_from = self.request.GET.get('date_from', '')
        if date_from:
            queryset = queryset.filter(posting_date__gte=date_from)
            
        date_to = self.request.GET.get('date_to', '')
        if date_to:
            queryset = queryset.filter(posting_date__lte=date_to)
            
        # Apply posted status filter
        is_posted = self.request.GET.get('is_posted', '')
        if is_posted:
            is_posted_bool = is_posted.lower() == 'true'
            queryset = queryset.filter(is_posted=is_posted_bool)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Journal Entries",
            'subtitle': "Manage journal entries",
            'create_url': reverse_lazy('Finance:journal_entry_create'),
            'print_url': reverse_lazy('Finance:journal_entry_print_list'),
            'export_url': reverse_lazy('Finance:journal_entry_export'),
            'model_name': "journal entry",
            'can_create': self.request.user.has_perm('Finance.add_journalentry'),
            'can_view': self.request.user.has_perm('Finance.view_journalentry'),
            'can_update': self.request.user.has_perm('Finance.change_journalentry'),
            'can_delete': self.request.user.has_perm('Finance.delete_journalentry'),
            'can_print': self.request.user.has_perm('Finance.view_journalentry'),
            'can_export': self.request.user.has_perm('Finance.view_journalentry'),
            'can_bulk_delete': self.request.user.has_perm('Finance.delete_journalentry'),
        })
        return context

class JournalEntryCreateView(CreateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'finance/journal-entry-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Journal Entry'
        context['subtitle'] = 'Add a new journal entry'
        context['cancel_url'] = reverse_lazy('Finance:journal_entry_list')
        context['submit_text'] = 'Create Journal Entry'
        
        if self.request.POST:
            context['formset'] = JournalEntryLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = JournalEntryExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = JournalEntryLineFormSet(instance=self.object)
            context['extra_form'] = JournalEntryExtraInfoForm(instance=self.object)
            
        # Get all accounts for the template
        context['accounts'] = ChartOfAccounts.objects.all()
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']
        
        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                # Save the main form
                self.object = form.save()
                
                # Update with extra form data
                for field in extra_form.cleaned_data:
                    if hasattr(self.object, field):
                        setattr(self.object, field, extra_form.cleaned_data[field])
                self.object.save()
                
                # Save the formset
                formset.instance = self.object
                formset.save()
            
            messages.success(self.request, f'Journal Entry {self.object.doc_num} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Finance:journal_entry_list')

class JournalEntryUpdateView(UpdateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = 'finance/journal-entry-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Journal Entry'
        context['subtitle'] = f'Edit journal entry {self.object.doc_num}'
        context['cancel_url'] = reverse_lazy('Finance:journal_entry_detail', kwargs={'pk': self.object.pk})
        context['submit_text'] = 'Update Journal Entry'
        
        if self.request.POST:
            context['formset'] = JournalEntryLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = JournalEntryExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = JournalEntryLineFormSet(instance=self.object)
            context['extra_form'] = JournalEntryExtraInfoForm(instance=self.object)
            
        # Get all accounts for the template
        context['accounts'] = ChartOfAccounts.objects.all()
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']
        
        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                # Save the main form
                self.object = form.save()
                
                # Update with extra form data
                for field in extra_form.cleaned_data:
                    if hasattr(self.object, field):
                        setattr(self.object, field, extra_form.cleaned_data[field])
                self.object.save()
                
                # Save the formset
                formset.instance = self.object
                formset.save()
            
            messages.success(self.request, f'Journal Entry {self.object.doc_num} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Finance:journal_entry_detail', kwargs={'pk': self.object.pk})

class JournalEntryDetailView(DetailView):
    model = JournalEntry
    template_name = 'finance/journal-entry-form.html'
    context_object_name = 'journal_entry'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Journal Entry Details'
        context['subtitle'] = f'Journal Entry {self.object.doc_num}'
        context['cancel_url'] = reverse_lazy('Finance:journal_entry_list')
        context['update_url'] = reverse_lazy('Finance:journal_entry_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Finance:journal_entry_delete', kwargs={'pk': self.object.pk})
        context['print_url'] = reverse_lazy('Finance:journal_entry_print_detail', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = JournalEntryForm(instance=self.object)
        context['extra_form'] = JournalEntryExtraInfoForm(instance=self.object)
        context['formset'] = JournalEntryLineFormSet(instance=self.object)
        
        # Get all accounts for the template
        context['accounts'] = ChartOfAccounts.objects.all()
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        # Make extra form fields read-only
        for form_field in context['extra_form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        # Make formset fields read-only
        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['disabled'] = 'disabled'
        
        # Add permission context variables
        context['can_update'] = self.request.user.has_perm('Finance.change_journalentry')
        context['can_delete'] = self.request.user.has_perm('Finance.delete_journalentry')
        
        return context



class JournalEntryDeleteView(GenericDeleteView):
    model = JournalEntry
    success_url = reverse_lazy('Finance:journal_entry_list')
    permission_required = 'Finance.delete_journalentry'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Journal Entry detail view.
        """
        return reverse_lazy('Finance:journal_entry_detail', kwargs={'pk': self.object.pk})

class JournalEntryExportView(BaseExportView):
    """
    Export view for Journal Entry.
    """
    model = JournalEntry
    filename = "journal_entries.csv"
    permission_required = "Finance.view_journalentry"
    field_names = ["Document Number", "Posting Date", "Reference", "Is Posted", 
                  "Currency", "Total Debit", "Total Credit"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class JournalEntryPrintView(ListView):
    model = JournalEntry
    template_name = 'finance/journal_entry_print_list.html'
    context_object_name = 'journal_entries'
    permission_required = 'Finance.view_journalentry'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Journal Entries List'
        context['user'] = self.request.user
        context['timestamp'] = timezone.now()
        return context

class JournalEntryPrintDetailView(DetailView):
    model = JournalEntry
    template_name = 'finance/journal_entry_print_detail.html'
    context_object_name = 'journal_entry'
    permission_required = 'Finance.view_journalentry'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Journal Entry: {self.object.doc_num}'
        context['lines'] = self.object.lines.all()
        context['user'] = self.request.user
        context['timestamp'] = timezone.now()
        return context

class JournalEntryBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Journal Entries.
    """
    model = JournalEntry
    permission_required = "Finance.delete_journalentry"
    display_fields = ["doc_num", "posting_date", "total_debit", "total_credit"]
    cancel_url = reverse_lazy("Finance:journal_entry_list")
    success_url = reverse_lazy("Finance:journal_entry_list")

