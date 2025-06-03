# sales/views/delivery_views.py
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from ..models import Delivery, DeliveryLine, SalesOrder
from ..forms.delivery_forms import (
    DeliveryForm, 
    DeliveryExtraInfoForm, 
    DeliveryLineForm, 
    DeliveryLineFormSet,
    get_delivery_line_formset
)
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class DeliveryListView(GenericFilterView):
    model = Delivery
    template_name = 'sales/delivery_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Sales.view_delivery'
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-document_date', '-id')
        user = self.request.user

        # Apply role-based filtering
        if not user.is_superuser:
            if hasattr(user, 'sales_employee'):
                queryset = queryset.filter(sales_employee=user.sales_employee)
            else:
                return queryset.none()

        # Apply search filter
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                id__icontains=search_query
            ) | queryset.filter(
                customer__name__icontains=search_query
            ) | queryset.filter(
                remarks__icontains=search_query
            ) | queryset.filter(
                sales_employee__name__icontains=search_query
            ) | queryset.filter(
                deliveryemployee__icontains=search_query
            ) | queryset.filter(
                status__icontains=search_query
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Deliveries'
        context['subtitle'] = 'Manage delivery documents'
        context['create_url'] = reverse_lazy('Sales:delivery_create')
        
        context['can_create'] = self.request.user.has_perm('Sales.add_delivery')
        context['can_view'] = self.request.user.has_perm('Sales.view_delivery')
        context['can_update'] = self.request.user.has_perm('Sales.change_delivery')
        context['can_delete'] = self.request.user.has_perm('Sales.delete_delivery')
        context['can_print'] = self.request.user.has_perm('Sales.view_delivery')
        context['can_export'] = self.request.user.has_perm('Sales.view_delivery')
        context['can_bulk_delete'] = self.request.user.has_perm('Sales.delete_delivery')
        
        return context

class DeliveryCreateView(CreateView):
    model = Delivery
    form_class = DeliveryForm
    template_name = 'common/formset-form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        prefill_data = self.request.session.pop('prefill_delivery_data', None)
        if prefill_data:
            self.prefill_lines = prefill_data.get('lines', [])
            self.prefill_order = prefill_data.get('sales_order')
            for key, value in prefill_data.items():
                if key not in ['lines', 'sales_order']:
                    initial[key] = value
            initial['sales_order'] = self.prefill_order  # ✅ ensure this is passed
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Delivery'
        context['subtitle'] = 'Create a new delivery'
        context['cancel_url'] = reverse_lazy('Sales:delivery_list')
        context['submit_text'] = 'Create Delivery'

        if self.request.POST:
            context['formset'] = DeliveryLineFormSet(self.request.POST)
            context['extra_form'] = DeliveryExtraInfoForm(self.request.POST)
        else:
            initial_lines = getattr(self, 'prefill_lines', [])
            extra_count = len(initial_lines) if initial_lines else 1  # ✅ Ensure at least 1 form
            dynamic_formset = inlineformset_factory(
                Delivery,
                DeliveryLine,
                form=DeliveryLineForm,
                extra=extra_count,
                can_delete=True
            )
            context['formset'] = dynamic_formset(initial=initial_lines)
            context['extra_form'] = DeliveryExtraInfoForm(initial=self.get_initial())

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']

        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                # ✅ Delivery Object বানাবো (commit=False)
                self.object = form.save(commit=False)

                # ✅ যদি Prefill SalesOrder থাকে সেট করবো
                if hasattr(self, 'prefill_order'):
                    self.object.sales_order_id = self.prefill_order

                # ✅ ExtraForm থেকে Additional Field গুলো Save করবো
                for field, value in extra_form.cleaned_data.items():
                    if hasattr(self.object, field):
                        setattr(self.object, field, value)

                # ✅ Main Delivery Save করবো
                self.object.save()

                # ✅ Delivery Line Save করবো
                formset.instance = self.object
                formset.save()

            messages.success(self.request, f"Delivery {self.object.pk} created successfully.")
            return HttpResponseRedirect(self.get_success_url())

        return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('Sales:delivery_detail', kwargs={'pk': self.object.pk})


class DeliveryUpdateView(UpdateView):
    model = Delivery
    form_class = DeliveryForm
    template_name = 'common/formset-form.html'
    permission_required = 'Sales.change_delivery'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # Pass request to form
        return kwargs
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.change_delivery'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Delivery'
        context['subtitle'] = f'Edit delivery {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Sales:delivery_list')
        context['submit_text'] = 'Update Delivery'
        
        if self.request.POST:
            context['formset'] = DeliveryLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = DeliveryExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = DeliveryLineFormSet(instance=self.object)
            context['extra_form'] = DeliveryExtraInfoForm(instance=self.object)
            
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
                
                # Update sales order status if needed
                if self.object.sales_order:
                    self._update_sales_order_status(self.object.sales_order)
            
            messages.success(self.request, f'Delivery {self.object.pk} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            # Print detailed error information
            print("Form errors:", form.errors)
            print("Extra form errors:", extra_form.errors)
            print("Formset errors:", formset.errors)
            if hasattr(formset, 'non_form_errors'):
                print("Formset non-form errors:", formset.non_form_errors())
            
            # Check each form in the formset
            for i, form_instance in enumerate(formset.forms):
                if form_instance.errors:
                    print(f"Formset form {i} errors:", form_instance.errors)
            
            return self.form_invalid(form)
    
    def _update_sales_order_status(self, sales_order):
        """Update the sales order status based on delivery status"""
        # Check if all order lines have been fully delivered
        order_lines = sales_order.lines.all()
        all_delivered = True
        
        for line in order_lines:
            delivered_qty = sum(dl.quantity for dl in line.delivery_lines.all())
            if delivered_qty < line.quantity:
                all_delivered = False
                break
        
        if all_delivered:
            sales_order.status = 'Delivered'
        else:
            # Check if any lines have been delivered
            any_delivered = False
            for line in order_lines:
                if line.delivery_lines.exists():
                    any_delivered = True
                    break
            
            if any_delivered:
                sales_order.status = 'Partially Delivered'
        
        sales_order.save(update_fields=['status'])
    
    def get_success_url(self):
        # Return to update URL after successful update
        return reverse_lazy('Sales:delivery_update', kwargs={'pk': self.object.pk})

class DeliveryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Delivery
    template_name = 'common/formset-form.html'  
    context_object_name = 'delivery'
    permission_required = 'Sales.view_delivery'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delivery Details'
        context['subtitle'] = f'Delivery {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Sales:delivery_list')
        context['update_url'] = reverse_lazy('Sales:delivery_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Sales:delivery_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add conversion buttons if delivery is not cancelled or closed
        if self.object.status not in ['Cancelled', 'Closed']:
            context['action_buttons'] = [
                {
                    'url': reverse_lazy('Sales:convert_delivery_to_return', kwargs={'pk': self.object.pk}),
                    'text': 'Convert to Return',
                    'icon': 'rotate-ccw',
                    'class': 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                },
                {
                    'url': reverse_lazy('Sales:convert_delivery_to_invoice', kwargs={'pk': self.object.pk}),
                    'text': 'Convert to Invoice',
                    'icon': 'file-text',
                    'class': 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }
            ]
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = DeliveryForm(instance=self.object, request=self.request)
        context['extra_form'] = DeliveryExtraInfoForm(instance=self.object)
        
        # সংশোধিত: get_delivery_line_formset ফাংশন ব্যবহার করে ফর্মসেট তৈরি
        formset_class = get_delivery_line_formset(self.request)
        context['formset'] = formset_class(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        for form_field in context['extra_form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        # Make formset fields read-only
        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['disabled'] = 'disabled'
        
        return context
class DeliveryPrintView(DetailView):
    model = Delivery
    template_name = 'sales/delivery_order_print.html'
    context_object_name = 'delivery'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.view_delivery'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delivery'
        context['subtitle'] = f'Order {self.object.pk}'
        return context
        
class DeliveryDeleteView(GenericDeleteView):
    model = Delivery
    success_url = reverse_lazy('Sales:delivery_list')
    permission_required = 'Sales.delete_delivery'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Delivery detail view.
        """
        return reverse_lazy('Sales:delivery_detail', kwargs={'pk': self.object.pk})        

class DeliveryExportView(BaseExportView):
    """
    Export view for Delivery.
    """
    model = Delivery
    filename = "deliveries.csv"
    permission_required = "Sales.view_delivery"
    field_names = ["ID", "Document Date", "Posting Date", "Customer", "Status", "Total Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class DeliveryBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Deliveries.
    """
    model = Delivery
    permission_required = "Sales.delete_delivery"
    display_fields = ["id", "document_date", "customer", "status"]
    cancel_url = reverse_lazy("Sales:delivery_list")
    success_url = reverse_lazy("Sales:delivery_list")