from django.views.generic import CreateView, UpdateView, DetailView,ListView
from django.utils import timezone
import datetime
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Q, Prefetch
from ..models import Employee,LeaveBalance,LeaveApplication
from ..forms import EmployeeForm, EmployeeFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class EmployeeListView(GenericFilterView):
    model = Employee
    template_name = 'employee/employee_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = EmployeeFilterForm
    permission_required = 'hrm.view_employee'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                employee_id__icontains=filters['search']
            ) | queryset.filter(
                first_name__icontains=filters['search']
            ) | queryset.filter(
                last_name__icontains=filters['search']
            ) | queryset.filter(
                email__icontains=filters['search']
            )
            
        if filters.get('department'):
            queryset = queryset.filter(department=filters['department'])
            
        if filters.get('designation'):
            queryset = queryset.filter(designation=filters['designation'])
            
        if filters.get('is_active') == 'true':
            queryset = queryset.filter(is_active=True)
        elif filters.get('is_active') == 'false':
            queryset = queryset.filter(is_active=False)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:employee_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_employee')
        context['can_view'] = self.request.user.has_perm('hrm.view_employee')
        context['can_update'] = self.request.user.has_perm('hrm.change_employee')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_employee')
        context['can_export'] = self.request.user.has_perm('hrm.view_employee')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_employee')
        
        return context
class EmployeeCardView(ListView):
    model = Employee
    template_name = 'employee/employee_card_view.html'  
    context_object_name = 'objects'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'department', 'designation'  # Removed 'reporting_to' as it doesn't exist
        ).prefetch_related(
            Prefetch(
                'leave_balances',
                queryset=LeaveBalance.objects.filter(year=timezone.now().year).select_related('leave_type')
            ),
            Prefetch(
                'leave_applications',
                queryset=LeaveApplication.objects.filter(
                    start_date__year=timezone.now().year
                ).select_related('leave_type')
            )
        )
        
        # Apply filters
        form = EmployeeFilterForm(self.request.GET)
        if form.is_valid():
            filters = form.cleaned_data
            
            if filters.get('search'):
                search_query = filters['search']
                queryset = queryset.filter(
                    Q(first_name__icontains=search_query) | 
                    Q(last_name__icontains=search_query) | 
                    Q(employee_id__icontains=search_query) |
                    Q(email__icontains=search_query)
                )
            
            if filters.get('department'):
                queryset = queryset.filter(department=filters['department'])
                
            if filters.get('designation'):
                queryset = queryset.filter(designation=filters['designation'])
                
            if filters.get('is_active') == 'true':
                queryset = queryset.filter(is_active=True)
            elif filters.get('is_active') == 'false':
                queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = EmployeeFilterForm(self.request.GET)
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_employee')
        context['can_view'] = self.request.user.has_perm('hrm.view_employee')
        context['can_update'] = self.request.user.has_perm('hrm.change_employee')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_employee')
        context['can_export'] = self.request.user.has_perm('hrm.view_employee')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_employee')
        
        return context
    


class EmployeeAllView(GenericFilterView):
    model = Employee
    template_name = 'employee/employee_all.html'
    context_object_name = 'objects'
    filter_form_class = EmployeeFilterForm
    permission_required = 'hrm.view_employee'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                employee_id__icontains=filters['search']
            ) | queryset.filter(
                first_name__icontains=filters['search']
            ) | queryset.filter(
                last_name__icontains=filters['search']
            ) | queryset.filter(
                email__icontains=filters['search']
            )
            
        if filters.get('department'):
            queryset = queryset.filter(department=filters['department'])
            
        if filters.get('designation'):
            queryset = queryset.filter(designation=filters['designation'])
            
        if filters.get('is_active') == 'true':
            queryset = queryset.filter(is_active=True)
        elif filters.get('is_active') == 'false':
            queryset = queryset.filter(is_active=False)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:employee_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_employee')
        context['can_view'] = self.request.user.has_perm('hrm.view_employee')
        context['can_update'] = self.request.user.has_perm('hrm.change_employee')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_employee')
        context['can_export'] = self.request.user.has_perm('hrm.view_employee')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_employee')
        
        return context


class EmployeeCreateView(CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Employee'
        context['subtitle'] = 'Add a new employee to the system'
        context['cancel_url'] = reverse_lazy('hrm:employee_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Employee {self.object.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_detail', kwargs={'pk': self.object.pk})

class EmployeeUpdateView(UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Employee'
        context['subtitle'] = f'Edit employee {self.object.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Employee {self.object.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_detail', kwargs={'pk': self.object.pk})

class EmployeeDetailView(DetailView):
    model = Employee
    template_name = 'common/premium-form.html'
    context_object_name = 'employee'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Employee Details'
        context['subtitle'] = f'Employee: {self.object.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_list')
        context['update_url'] = reverse_lazy('hrm:employee_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:employee_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = EmployeeForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class EmployeeDeleteView(GenericDeleteView):
    model = Employee
    success_url = reverse_lazy('hrm:employee_list')
    permission_required = 'hrm.delete_employee'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Employee detail view."""
        return reverse_lazy('hrm:employee_detail', kwargs={'pk': self.object.pk})

class EmployeeExportView(BaseExportView):
    """Export view for Employee."""
    model = Employee
    filename = "employees.csv"
    permission_required = "hrm.view_employee"
    field_names = ["Employee ID", "First Name", "Last Name", "Email", "Department", "Designation", "Joining Date", "Status"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class EmployeeBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Employees."""
    model = Employee
    permission_required = "hrm.delete_employee"
    display_fields = ["employee_id", "first_name", "last_name", "department", "designation"]
    cancel_url = reverse_lazy("hrm:employee_list")
    success_url = reverse_lazy("hrm:employee_list")

