from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import Promotion
from ..forms import PromotionForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class PromotionListView(GenericFilterView):
    model = Promotion
    template_name = 'payroll/promotion_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_promotion'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                employee__employee_id__icontains=filters['search']
            ) | queryset.filter(
                employee__first_name__icontains=filters['search']
            ) | queryset.filter(
                employee__last_name__icontains=filters['search']
            )
            
        if filters.get('department'):
            queryset = queryset.filter(employee__department=filters['department'])
            
        if filters.get('from_date'):
            queryset = queryset.filter(effective_date__gte=filters['from_date'])
            
        if filters.get('to_date'):
            queryset = queryset.filter(effective_date__lte=filters['to_date'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:promotion_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_promotion')
        context['can_view'] = self.request.user.has_perm('Hrm.view_promotion')
        context['can_update'] = self.request.user.has_perm('Hrm.change_promotion')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_promotion')
        context['can_export'] = self.request.user.has_perm('Hrm.view_promotion')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_promotion')
        
        return context

class PromotionCreateView(CreateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Promotion'
        context['subtitle'] = 'Add a new promotion to the system'
        context['cancel_url'] = reverse_lazy('hrm:promotion_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Promotion for {self.object.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:promotion_detail', kwargs={'pk': self.object.pk})

class PromotionUpdateView(UpdateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Promotion'
        context['subtitle'] = f'Edit promotion for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:promotion_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Promotion for {self.object.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:promotion_detail', kwargs={'pk': self.object.pk})

class PromotionDetailView(DetailView):
    model = Promotion
    template_name = 'common/premium-form.html'
    context_object_name = 'promotion'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Promotion Details'
        context['subtitle'] = f'Promotion for: {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:promotion_list')
        context['update_url'] = reverse_lazy('hrm:promotion_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:promotion_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = PromotionForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class PromotionDeleteView(GenericDeleteView):
    model = Promotion
    success_url = reverse_lazy('hrm:promotion_list')
    permission_required = 'Hrm.delete_promotion'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Promotion detail view."""
        return reverse_lazy('hrm:promotion_detail', kwargs={'pk': self.object.pk})

class PromotionExportView(BaseExportView):
    """Export view for Promotion."""
    model = Promotion
    filename = "promotions.csv"
    permission_required = "Hrm.view_promotion"
    field_names = ["Employee", "From Designation", "To Designation", "Effective Date", "Remarks", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class PromotionBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Promotions."""
    model = Promotion
    permission_required = "Hrm.delete_promotion"
    display_fields = ["employee__employee_id", "employee__first_name", "from_designation__name", "to_designation__name", "effective_date"]
    cancel_url = reverse_lazy("hrm:promotion_list")
    success_url = reverse_lazy("hrm:promotion_list")