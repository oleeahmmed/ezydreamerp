from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import LeaveType
from ..forms import LeaveTypeForm, LeaveTypeFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class LeaveTypeListView(GenericFilterView):
    model = LeaveType
    template_name = 'leave/leave_type_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = LeaveTypeFilterForm
    permission_required = 'hrm.view_leavetype'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                name__icontains=filters['search']
            ) | queryset.filter(
                code__icontains=filters['search']
            ) | queryset.filter(
                description__icontains=filters['search']
            )
            
        if filters.get('paid') == 'true':
            queryset = queryset.filter(paid=True)
        elif filters.get('paid') == 'false':
            queryset = queryset.filter(paid=False)
            
        if filters.get('carry_forward') == 'true':
            queryset = queryset.filter(carry_forward=True)
        elif filters.get('carry_forward') == 'false':
            queryset = queryset.filter(carry_forward=False)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:leave_type_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_leavetype')
        context['can_view'] = self.request.user.has_perm('hrm.view_leavetype')
        context['can_update'] = self.request.user.has_perm('hrm.change_leavetype')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_leavetype')
        context['can_export'] = self.request.user.has_perm('hrm.view_leavetype')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_leavetype')
        
        return context

class LeaveTypeCreateView(CreateView):
    model = LeaveType
    form_class = LeaveTypeForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Leave Type'
        context['subtitle'] = 'Add a new leave type to the system'
        context['cancel_url'] = reverse_lazy('hrm:leave_type_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Leave type {self.object.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:leave_type_detail', kwargs={'pk': self.object.pk})

class LeaveTypeUpdateView(UpdateView):
    model = LeaveType
    form_class = LeaveTypeForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Leave Type'
        context['subtitle'] = f'Edit leave type {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:leave_type_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Leave type {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:leave_type_detail', kwargs={'pk': self.object.pk})

class LeaveTypeDetailView(DetailView):
    model = LeaveType
    template_name = 'common/premium-form.html'
    context_object_name = 'leave_type'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Leave Type Details'
        context['subtitle'] = f'Leave type: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:leave_type_list')
        context['update_url'] = reverse_lazy('hrm:leave_type_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:leave_type_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = LeaveTypeForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class LeaveTypeDeleteView(GenericDeleteView):
    model = LeaveType
    success_url = reverse_lazy('hrm:leave_type_list')
    permission_required = 'hrm.delete_leavetype'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Leave Type detail view."""
        return reverse_lazy('hrm:leave_type_detail', kwargs={'pk': self.object.pk})

class LeaveTypeExportView(BaseExportView):
    """Export view for Leave Type."""
    model = LeaveType
    filename = "leave_types.csv"
    permission_required = "hrm.view_leavetype"
    field_names = ["Name", "Code", "Paid", "Max Days Per Year", "Carry Forward", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class LeaveTypeBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Leave Types."""
    model = LeaveType
    permission_required = "hrm.delete_leavetype"
    display_fields = ["name", "code", "paid", "max_days_per_year"]
    cancel_url = reverse_lazy("hrm:leave_type_list")
    success_url = reverse_lazy("hrm:leave_type_list")

