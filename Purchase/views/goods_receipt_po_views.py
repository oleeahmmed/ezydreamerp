from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

from ..models import GoodsReceiptPo, GoodsReceiptPoLine, PurchaseOrder, PurchaseOrderLine
from ..forms import GoodsReceiptPoForm, GoodsReceiptPoExtraInfoForm, GoodsReceiptPoLineFormSet, GoodsReceiptPoFilterForm

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class GoodsReceiptPoListView(GenericFilterView):
    model = GoodsReceiptPo
    template_name = 'purchase/goods_receipt_list.html'
    context_object_name = 'objects'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-document_date')

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                id__icontains=search_query
            ) | queryset.filter(
                vendor__name__icontains=search_query
            ) | queryset.filter(
                remarks__icontains=search_query
            )

        return queryset

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Goods Receipts'
        context['subtitle'] = 'Manage goods receipt documents'
        context['create_url'] = reverse_lazy('Purchase:goods_receipt_create')
        
        context['can_create'] = self.request.user.has_perm('Purchase.add_goodsreceiptpo')
        context['can_view'] = self.request.user.has_perm('Purchase.view_goodsreceiptpo')
        context['can_update'] = self.request.user.has_perm('Purchase.change_goodsreceiptpo')
        context['can_delete'] = self.request.user.has_perm('Purchase.delete_goodsreceiptpo')
        context['can_print'] = self.request.user.has_perm('Purchase.view_goodsreceiptpo')
        context['can_export'] = self.request.user.has_perm('Purchase.view_goodsreceiptpo')
        context['can_bulk_delete'] = self.request.user.has_perm('Purchase.delete_goodsreceiptpo')
        
        return context

class GoodsReceiptPoCreateView(CreateView):
    model = GoodsReceiptPo
    form_class = GoodsReceiptPoForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Goods Receipt'
        context['subtitle'] = 'Create a new goods receipt document'
        context['cancel_url'] = reverse_lazy('Purchase:goods_receipt_list')
        context['submit_text'] = 'Create Goods Receipt'
        
        if self.request.POST:
            context['formset'] = GoodsReceiptPoLineFormSet(self.request.POST)
            context['extra_form'] = GoodsReceiptPoExtraInfoForm(self.request.POST)
        else:
            context['formset'] = GoodsReceiptPoLineFormSet()
            context['extra_form'] = GoodsReceiptPoExtraInfoForm()
            
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
                
                # Update purchase order status if needed
                if self.object.purchase_order:
                    self._update_purchase_order_status(self.object.purchase_order)
            
            messages.success(self.request, f'Goods Receipt {self.object.pk} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            # Print detailed error information
            print("Form errors:", form.errors)
            print("Extra form errors:", extra_form.errors)
            print("Formset errors:", formset.errors)
            if hasattr(formset, 'non_form_errors'):
                print("  formset.errors")
            if hasattr(formset, 'non_form_errors'):
                print("Formset non-form errors:", formset.non_form_errors())
            
            # Check each form in the formset
            for i, form_instance in enumerate(formset.forms):
                if form_instance.errors:
                    print(f"Formset form {i} errors:", form_instance.errors)
            
            return self.form_invalid(form)
    
    def _update_purchase_order_status(self, purchase_order):
        """Update the purchase order status based on goods receipt status"""
        # Check if all order lines have been fully received
        order_lines = purchase_order.lines.all()
        all_received = True
        
        for line in order_lines:
            received_qty = sum(gl.quantity for gl in line.goods_receipt_lines.all())
            if received_qty < line.quantity:
                all_received = False
                break
        
        if all_received:
            purchase_order.status = 'Received'
        else:
            # Check if any lines have been received
            any_received = False
            for line in order_lines:
                if line.goods_receipt_lines.exists():
                    any_received = True
                    break
            
            if any_received:
                purchase_order.status = 'Partially Received'
        
        purchase_order.save(update_fields=['status'])
    
    def get_success_url(self):
        # Return to create URL after successful creation
        return reverse_lazy('Purchase:goods_receipt_create')

class GoodsReceiptPoUpdateView(UpdateView):
    model = GoodsReceiptPo
    form_class = GoodsReceiptPoForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Goods Receipt'
        context['subtitle'] = f'Edit goods receipt {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Purchase:goods_receipt_list')
        context['submit_text'] = 'Update Goods Receipt'
        
        if self.request.POST:
            context['formset'] = GoodsReceiptPoLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = GoodsReceiptPoExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = GoodsReceiptPoLineFormSet(instance=self.object)
            context['extra_form'] = GoodsReceiptPoExtraInfoForm(instance=self.object)
            
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
                
                # Update purchase order status if needed
                if self.object.purchase_order:
                    self._update_purchase_order_status(self.object.purchase_order)
            
            messages.success(self.request, f'Goods Receipt {self.object.pk} updated successfully.')
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
    
    def _update_purchase_order_status(self, purchase_order):
        """Update the purchase order status based on goods receipt status"""
        # Check if all order lines have been fully received
        order_lines = purchase_order.lines.all()
        all_received = True
        
        for line in order_lines:
            received_qty = sum(gl.quantity for gl in line.goods_receipt_lines.all())
            if received_qty < line.quantity:
                all_received = False
                break
        
        if all_received:
            purchase_order.status = 'Received'
        else:
            # Check if any lines have been received
            any_received = False
            for line in order_lines:
                if line.goods_receipt_lines.exists():
                    any_received = True
                    break
            
            if any_received:
                purchase_order.status = 'Partially Received'
        
        purchase_order.save(update_fields=['status'])
    
    def get_success_url(self):
        # Return to update URL after successful update
        return reverse_lazy('Purchase:goods_receipt_update', kwargs={'pk': self.object.pk})

class GoodsReceiptPoDetailView(DetailView):
    model = GoodsReceiptPo
    template_name = 'common/formset-form.html'  
    context_object_name = 'goods_receipt'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Goods Receipt Details'
        context['subtitle'] = f'Goods Receipt {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Purchase:goods_receipt_list')
        context['update_url'] = reverse_lazy('Purchase:goods_receipt_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Purchase:goods_receipt_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = GoodsReceiptPoForm(instance=self.object)
        context['extra_form'] = GoodsReceiptPoExtraInfoForm(instance=self.object)
        context['formset'] = GoodsReceiptPoLineFormSet(instance=self.object)
        
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

class GoodsReceiptPoDeleteView(GenericDeleteView):
    model = GoodsReceiptPo
    success_url = reverse_lazy('Purchase:goods_receipt_list')
    permission_required = 'Purchase.delete_goodsreceiptpo'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Goods Receipt detail view.
        """
        return reverse_lazy('Purchase:goods_receipt_detail', kwargs={'pk': self.object.pk})        

class GoodsReceiptPoExportView(BaseExportView):
    """
    Export view for Goods Receipt.
    """
    model = GoodsReceiptPo
    filename = "goods_receipts.csv"
    permission_required = "Purchase.view_goodsreceiptpo"
    field_names = ["ID", "Document Date", "Posting Date", "Vendor", "Status", "Total Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class GoodsReceiptPoBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Goods Receipts.
    """
    model = GoodsReceiptPo
    permission_required = "Purchase.delete_goodsreceiptpo"
    display_fields = ["id", "document_date", "vendor", "status"]
    cancel_url = reverse_lazy("Purchase:goods_receipt_list")
    success_url = reverse_lazy("Purchase:goods_receipt_list")

