from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import BonusSetup
from ..forms import BonusSetupForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class BonusSetupListView(GenericFilterView):
    model = BonusSetup
    template_name = 'payroll/bonus_setup_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_bonussetup'
    
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
        context['create_url'] = reverse_lazy('hrm:bonus_setup_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_bonussetup')
        context['can_view'] = self.request.user.has_perm('Hrm.view_bonussetup')
        context['can_update'] = self.request.user.has_perm('Hrm.change_bonussetup')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_bonussetup')
        context['can_export'] = self.request.user.has_perm('Hrm.view_bonussetup')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_bonussetup')
        
        return context

class BonusSetupCreateView(CreateView):
    model = BonusSetup
    form_class = BonusSetupForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Bonus Setup'
        context['subtitle'] = 'Add a new bonus setup to the system'
        context['cancel_url'] = reverse_lazy('hrm:bonus_setup_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Bonus Setup {self.object.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:bonus_setup_detail', kwargs={'pk': self.object.pk})

class BonusSetupUpdateView(UpdateView):
    model = BonusSetup
    form_class = BonusSetupForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Bonus Setup'
        context['subtitle'] = f'Edit bonus setup {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:bonus_setup_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Bonus Setup {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:bonus_setup_detail', kwargs={'pk': self.object.pk})

class BonusSetupDetailView(DetailView):
    model = BonusSetup
    template_name = 'common/premium-form.html'
    context_object_name = 'bonus_setup'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Bonus Setup Details'
        context['subtitle'] = f'Bonus Setup: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:bonus_setup_list')
        context['update_url'] = reverse_lazy('hrm:bonus_setup_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:bonus_setup_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = BonusSetupForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class BonusSetupDeleteView(GenericDeleteView):
    model = BonusSetup
    success_url = reverse_lazy('hrm:bonus_setup_list')
    permission_required = 'Hrm.delete_bonussetup'

    def get_cancel_url(self):
        """Override cancel URL to redirect to BonusSetup detail view."""
        return reverse_lazy('hrm:bonus_setup_detail', kwargs={'pk': self.object.pk})

class BonusSetupExportView(BaseExportView):
    """Export view for BonusSetup."""
    model = BonusSetup
    filename = "bonus_setups.csv"
    permission_required = "Hrm.view_bonussetup"
    field_names = ["Name", "Description", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class BonusSetupBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for BonusSetup."""
    model = BonusSetup
    permission_required = "Hrm.delete_bonussetup"
    display_fields = ["name", "description", "created_at"]
    cancel_url = reverse_lazy("hrm:bonus_setup_list")
    success_url = reverse_lazy("hrm:bonus_setup_list")

