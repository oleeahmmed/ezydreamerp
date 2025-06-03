from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import BonusMonth
from ..forms import BonusMonthForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class BonusMonthListView(GenericFilterView):
    model = BonusMonth
    template_name = 'payroll/bonus_month_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_bonusmonth'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                bonus_setup__name__icontains=filters['search']
            )
            
        if filters.get('year'):
            queryset = queryset.filter(year=filters['year'])
            
        if filters.get('month'):
            queryset = queryset.filter(month=filters['month'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:bonus_month_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_bonusmonth')
        context['can_view'] = self.request.user.has_perm('Hrm.view_bonusmonth')
        context['can_update'] = self.request.user.has_perm('Hrm.change_bonusmonth')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_bonusmonth')
        context['can_export'] = self.request.user.has_perm('Hrm.view_bonusmonth')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_bonusmonth')
        
        return context

class BonusMonthCreateView(CreateView):
    model = BonusMonth
    form_class = BonusMonthForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Bonus Month'
        context['subtitle'] = 'Add a new bonus month to the system'
        context['cancel_url'] = reverse_lazy('hrm:bonus_month_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Bonus Month {self.object.year}-{self.object.month:02d} for {self.object.bonus_setup.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:bonus_month_detail', kwargs={'pk': self.object.pk})

class BonusMonthUpdateView(UpdateView):
    model = BonusMonth
    form_class = BonusMonthForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Bonus Month'
        context['subtitle'] = f'Edit bonus month {self.object.year}-{self.object.month:02d} for {self.object.bonus_setup.name}'
        context['cancel_url'] = reverse_lazy('hrm:bonus_month_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Bonus Month {self.object.year}-{self.object.month:02d} for {self.object.bonus_setup.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:bonus_month_detail', kwargs={'pk': self.object.pk})

class BonusMonthDetailView(DetailView):
    model = BonusMonth
    template_name = 'common/premium-form.html'
    context_object_name = 'bonus_month'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Bonus Month Details'
        context['subtitle'] = f'Bonus Month: {self.object.year}-{self.object.month:02d} for {self.object.bonus_setup.name}'
        context['cancel_url'] = reverse_lazy('hrm:bonus_month_list')
        context['update_url'] = reverse_lazy('hrm:bonus_month_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:bonus_month_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = BonusMonthForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class BonusMonthDeleteView(GenericDeleteView):
    model = BonusMonth
    success_url = reverse_lazy('hrm:bonus_month_list')
    permission_required = 'Hrm.delete_bonusmonth'

    def get_cancel_url(self):
        """Override cancel URL to redirect to BonusMonth detail view."""
        return reverse_lazy('hrm:bonus_month_detail', kwargs={'pk': self.object.pk})

class BonusMonthExportView(BaseExportView):
    """Export view for BonusMonth."""
    model = BonusMonth
    filename = "bonus_months.csv"
    permission_required = "Hrm.view_bonusmonth"
    field_names = ["Bonus Setup", "Year", "Month", "Is Generated", "Generated Date", "Generated By", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class BonusMonthBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for BonusMonth."""
    model = BonusMonth
    permission_required = "Hrm.delete_bonusmonth"
    display_fields = ["bonus_setup", "year", "month", "is_generated", "created_at"]
    cancel_url = reverse_lazy("hrm:bonus_month_list")
    success_url = reverse_lazy("hrm:bonus_month_list")

