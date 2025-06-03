from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

from ..models import SalesEmployee
from ..forms.sales_employee_forms import SalesEmployeeForm, SalesEmployeeFilterForm

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class SalesEmployeeListView(GenericFilterView):
    model = SalesEmployee
    template_name = 'sales/sales_employee_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = SalesEmployeeFilterForm
    permission_required = 'Sales.view_salesemployee'

    def get_queryset(self):
        queryset = super().get_queryset().order_by('name')

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                employee_code__icontains=search_query
            ) | queryset.filter(
                name__icontains=search_query
            ) | queryset.filter(
                email__icontains=search_query
            ) | queryset.filter(
                phone__icontains=search_query
            )

        # Filter by department if provided
        department = self.request.GET.get('department', '')
        if department:
            queryset = queryset.filter(department__icontains=department)
            
        # Filter by position if provided
        position = self.request.GET.get('position', '')
        if position:
            queryset = queryset.filter(position__icontains=position)
            
        # Filter by status if provided
        status = self.request.GET.get('status', '')
        if status:
            is_active = status == 'True'
            queryset = queryset.filter(is_active=is_active)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sales Employees'
        context['subtitle'] = 'Manage sales employees'
        context['create_url'] = reverse_lazy('Sales:sales_employee_create')
        
        context['can_create'] = self.request.user.has_perm('Sales.add_salesemployee')
        context['can_view'] = self.request.user.has_perm('Sales.view_salesemployee')
        context['can_update'] = self.request.user.has_perm('Sales.change_salesemployee')
        context['can_delete'] = self.request.user.has_perm('Sales.delete_salesemployee')
        context['can_export'] = self.request.user.has_perm('Sales.view_salesemployee')
        context['can_bulk_delete'] = self.request.user.has_perm('Sales.delete_salesemployee')
        
        return context

class SalesEmployeeCreateView(CreateView):
    model = SalesEmployee
    form_class = SalesEmployeeForm
    template_name = 'common/premium-form.html'
    permission_required = 'Sales.add_salesemployee'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.add_salesemployee'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Sales Employee'
        context['subtitle'] = 'Create a new sales employee'
        context['cancel_url'] = reverse_lazy('Sales:sales_employee_list')
        context['submit_text'] = 'Create Employee'
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            
        messages.success(self.request, f'Sales Employee {self.object.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('Sales:sales_employee_detail', kwargs={'pk': self.object.pk})

class SalesEmployeeUpdateView(UpdateView):
    model = SalesEmployee
    form_class = SalesEmployeeForm
    template_name = 'common/premium-form.html'
    permission_required = 'Sales.change_salesemployee'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.change_salesemployee'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Sales Employee'
        context['subtitle'] = f'Edit employee {self.object.name}'
        context['cancel_url'] = reverse_lazy('Sales:sales_employee_list')
        context['submit_text'] = 'Update Employee'
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            
        messages.success(self.request, f'Sales Employee {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('Sales:sales_employee_detail', kwargs={'pk': self.object.pk})

class SalesEmployeeDetailView(DetailView):
    model = SalesEmployee
    template_name = 'common/premium-form.html'
    context_object_name = 'sales_employee'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.view_salesemployee'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sales Employee Details'
        context['subtitle'] = f'Employee: {self.object.name}'
        context['cancel_url'] = reverse_lazy('Sales:sales_employee_list')
        context['update_url'] = reverse_lazy('Sales:sales_employee_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Sales:sales_employee_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = SalesEmployeeForm(instance=self.object, request=self.request)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class SalesEmployeeDeleteView(GenericDeleteView):
    model = SalesEmployee
    success_url = reverse_lazy('Sales:sales_employee_list')
    permission_required = 'Sales.delete_salesemployee'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Sales Employee detail view.
        """
        return reverse_lazy('Sales:sales_employee_detail', kwargs={'pk': self.object.pk})

class SalesEmployeeExportView(BaseExportView):
    """
    Export view for Sales Employee.
    """
    model = SalesEmployee
    filename = "sales_employees.csv"
    permission_required = "Sales.view_salesemployee"
    field_names = ["ID", "Employee Code", "Name", "Position", "Department", "Phone", "Email", "Status", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class SalesEmployeeBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Sales Employees.
    """
    model = SalesEmployee
    permission_required = "Sales.delete_salesemployee"
    display_fields = ["employee_code", "name", "position", "department"]
    cancel_url = reverse_lazy("Sales:sales_employee_list")
    success_url = reverse_lazy("Sales:sales_employee_list")