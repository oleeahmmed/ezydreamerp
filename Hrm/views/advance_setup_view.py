from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import AdvanceSetup
from ..forms import AdvanceSetupForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class AdvanceSetupListView(GenericFilterView):
    model = AdvanceSetup
    template_name = 'payroll/advance_setup_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_advancesetup'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                name__icontains=filters['search']
            ) | queryset.filter(
                description__icontains=filters['search']
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:advance_setup_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_advancesetup')
        context['can_view'] = self.request.user.has_perm('Hrm.view_advancesetup')
        context['can_update'] = self.request.user.has_perm('Hrm.change_advancesetup')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_advancesetup')
        context['can_export'] = self.request.user.has_perm('Hrm.view_advancesetup')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_advancesetup')
        
        return context

class AdvanceSetupCreateView(CreateView):
    model = AdvanceSetup
    form_class = AdvanceSetupForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Advance Setup'
        context['subtitle'] = 'Add a new advance setup to the system'
        context['cancel_url'] = reverse_lazy('hrm:advance_setup_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Advance Setup {self.object.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:advance_setup_detail', kwargs={'pk': self.object.pk})

class AdvanceSetupUpdateView(UpdateView):
    model = AdvanceSetup
    form_class = AdvanceSetupForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Advance Setup'
        context['subtitle'] = f'Edit advance setup {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:advance_setup_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Advance Setup {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:advance_setup_detail', kwargs={'pk': self.object.pk})

class AdvanceSetupDetailView(DetailView):
    model = AdvanceSetup
    template_name = 'common/premium-form.html'
    context_object_name = 'advance_setup'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Advance Setup Details'
        context['subtitle'] = f'Advance Setup: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:advance_setup_list')
        context['update_url'] = reverse_lazy('hrm:advance_setup_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:advance_setup_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = AdvanceSetupForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class AdvanceSetupDeleteView(GenericDeleteView):
    model = AdvanceSetup
    success_url = reverse_lazy('hrm:advance_setup_list')
    permission_required = 'Hrm.delete_advancesetup'

    def get_cancel_url(self):
        """Override cancel URL to redirect to AdvanceSetup detail view."""
        return reverse_lazy('hrm:advance_setup_detail', kwargs={'pk': self.object.pk})

class AdvanceSetupExportView(BaseExportView):
    """Export view for AdvanceSetup."""
    model = AdvanceSetup
    filename = "advance_setups.csv"
    permission_required = "Hrm.view_advancesetup"
    field_names = ["Name", "Max Amount", "Max Installments", "Interest Rate", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class AdvanceSetupBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for AdvanceSetup."""
    model = AdvanceSetup
    permission_required = "Hrm.delete_advancesetup"
    display_fields = ["name", "max_amount", "max_installments", "interest_rate", "created_at"]
    cancel_url = reverse_lazy("hrm:advance_setup_list")
    success_url = reverse_lazy("hrm:advance_setup_list")

