from django.views.generic import CreateView, UpdateView, DetailView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.mixins import PermissionRequiredMixin

from ..models import LeaveBalance, Employee, LeaveType
from ..forms.leave_balance_form import LeaveBalanceForm, LeaveBalanceFilterForm, LeaveBalanceInitializeForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class LeaveBalanceListView(GenericFilterView):
    model = LeaveBalance
    template_name = 'leave/leave_balance_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = LeaveBalanceFilterForm
    permission_required = 'hrm.view_leavebalance'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            # Search by employee name
            queryset = queryset.filter(
                employee__first_name__icontains=filters['search']
            ) | queryset.filter(
                employee__last_name__icontains=filters['search']
            ) | queryset.filter(
                leave_type__name__icontains=filters['search']
            )
            
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
            
        if filters.get('leave_type'):
            queryset = queryset.filter(leave_type=filters['leave_type'])
            
        if filters.get('year'):
            queryset = queryset.filter(year=filters['year'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:leave_balance_create')
        context['initialize_url'] = reverse_lazy('hrm:leave_balance_initialize')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_leavebalance')
        context['can_view'] = self.request.user.has_perm('hrm.view_leavebalance')
        context['can_update'] = self.request.user.has_perm('hrm.change_leavebalance')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_leavebalance')
        context['can_export'] = self.request.user.has_perm('hrm.view_leavebalance')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_leavebalance')
        
        return context

class LeaveBalanceCreateView(CreateView):
    model = LeaveBalance
    form_class = LeaveBalanceForm
    template_name = 'common/premium-form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        initial['year'] = timezone.now().year
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Leave Balance'
        context['subtitle'] = 'Add a new leave balance record'
        context['cancel_url'] = reverse_lazy('hrm:leave_balance_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Leave balance for {self.object.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:leave_balance_detail', kwargs={'pk': self.object.pk})

class LeaveBalanceUpdateView(UpdateView):
    model = LeaveBalance
    form_class = LeaveBalanceForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Leave Balance'
        context['subtitle'] = f'Edit leave balance for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:leave_balance_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Leave balance for {self.object.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:leave_balance_detail', kwargs={'pk': self.object.pk})

class LeaveBalanceDetailView(DetailView):
    model = LeaveBalance
    template_name = 'common/premium-form.html'
    context_object_name = 'leave_balance'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Leave Balance Details'
        context['subtitle'] = f'Leave balance for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:leave_balance_list')
        context['update_url'] = reverse_lazy('hrm:leave_balance_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:leave_balance_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = LeaveBalanceForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        # Get leave applications for this employee and leave type
        context['leave_applications'] = self.object.employee.leave_applications.filter(
            leave_type=self.object.leave_type,
            start_date__year=self.object.year
        ).order_by('-start_date')
        
        return context

class LeaveBalanceDeleteView(GenericDeleteView):
    model = LeaveBalance
    success_url = reverse_lazy('hrm:leave_balance_list')
    permission_required = 'hrm.delete_leavebalance'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Leave Balance detail view."""
        return reverse_lazy('hrm:leave_balance_detail', kwargs={'pk': self.object.pk})

class LeaveBalanceExportView(BaseExportView):
    """Export view for Leave Balance."""
    model = LeaveBalance
    filename = "leave_balances.csv"
    permission_required = "hrm.view_leavebalance"
    field_names = ["Employee", "Leave Type", "Year", "Total Days", "Used Days", "Pending Days", "Available Days"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class LeaveBalanceBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Leave Balances."""
    model = LeaveBalance
    permission_required = "hrm.delete_leavebalance"
    display_fields = ["employee", "leave_type", "year", "total_days", "used_days"]
    cancel_url = reverse_lazy("hrm:leave_balance_list")
    success_url = reverse_lazy("hrm:leave_balance_list")

class LeaveBalanceInitializeView(PermissionRequiredMixin, FormView):
    """View for initializing leave balances for all employees."""
    template_name = 'common/premium-form.html'
    form_class = LeaveBalanceInitializeForm
    permission_required = 'hrm.add_leavebalance'
    success_url = reverse_lazy('hrm:leave_balance_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Initialize Leave Balances'
        context['subtitle'] = 'Create leave balance records for all active employees'
        context['cancel_url'] = reverse_lazy('hrm:leave_balance_list')
        return context
    
    @transaction.atomic
    def form_valid(self, form):
        year = int(form.cleaned_data['year'])
        leave_types = form.cleaned_data['leave_types']
        reset_existing = form.cleaned_data['reset_existing']
        
        employees = Employee.objects.filter(is_active=True)
        balances_created = 0
        balances_updated = 0
        
        for employee in employees:
            for leave_type in leave_types:
                # Check if balance already exists
                balance, created = LeaveBalance.objects.get_or_create(
                    employee=employee,
                    leave_type=leave_type,
                    year=year,
                    defaults={
                        'total_days': leave_type.max_days_per_year,
                        'used_days': 0,
                        'pending_days': 0,
                        'carried_forward_days': 0
                    }
                )
                
                if created:
                    balances_created += 1
                elif reset_existing:
                    balance.total_days = leave_type.max_days_per_year
                    balance.used_days = 0
                    balance.pending_days = 0
                    balance.carried_forward_days = 0
                    balance.save()
                    balances_updated += 1
        
        if balances_created > 0:
            messages.success(self.request, f'Successfully created {balances_created} leave balance records.')
        
        if balances_updated > 0:
            messages.info(self.request, f'Reset {balances_updated} existing leave balance records.')
            
        if balances_created == 0 and balances_updated == 0:
            messages.info(self.request, 'No new leave balance records were created.')
            
        return super().form_valid(form)