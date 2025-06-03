from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

from ..models import GoodsReturn, GoodsReturnLine, GoodsReceiptPo, GoodsReceiptPoLine
from ..forms import GoodsReturnForm, GoodsReturnExtraInfoForm, GoodsReturnLineFormSet, GoodsReturnFilterForm

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class GoodsReturnListView(GenericFilterView):
    model = GoodsReturn
    template_name = 'purchase/goods_return_list.html'
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
        context['title'] = 'Goods Returns'
        context['subtitle'] = 'Manage goods return documents'
        context['create_url'] = reverse_lazy('Purchase:goods_return_create')
        
        context['can_create'] = self.request.user.has_perm('Purchase.add_goodsreturn')
        context['can_view'] = self.request.user.has_perm('Purchase.view_goodsreturn')
        context['can_update'] = self.request.user.has_perm('Purchase.change_goodsreturn')
        context['can_delete'] = self.request.user.has_perm('Purchase.delete_goodsreturn')
        context['can_print'] = self.request.user.has_perm('Purchase.view_goodsreturn')
        context['can_export'] = self.request.user.has_perm('Purchase.view_goodsreturn')
        context['can_bulk_delete'] = self.request.user.has_perm('Purchase.delete_goodsreturn')
        
        return context

class GoodsReturnCreateView(CreateView):
    model = GoodsReturn
    form_class = GoodsReturnForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Goods Return'
        context['subtitle'] = 'Create a new goods return document'
        context['cancel_url'] = reverse_lazy('Purchase:goods_return_list')
        context['submit_text'] = 'Create Goods Return'
        
        if self.request.POST:
            context['formset'] = GoodsReturnLineFormSet(self.request.POST)
            context['extra_form'] = GoodsReturnExtraInfoForm(self.request.POST)
        else:
            context['formset'] = GoodsReturnLineFormSet()
            context['extra_form'] = GoodsReturnExtraInfoForm()
            
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
            
            messages.success(self.request, f'Goods Return {self.object.pk} created successfully.')
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
    
    def get_success_url(self):
        # Return to create URL after successful creation
        return reverse_lazy('Purchase:goods_return_create')

class GoodsReturnUpdateView(UpdateView):
    model = GoodsReturn
    form_class = GoodsReturnForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Goods Return'
        context['subtitle'] = f'Edit goods return {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Purchase:goods_return_list')
        context['submit_text'] = 'Update Goods Return'
        
        if self.request.POST:
            context['formset'] = GoodsReturnLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = GoodsReturnExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = GoodsReturnLineFormSet(instance=self.object)
            context['extra_form'] = GoodsReturnExtraInfoForm(instance=self.object)
            
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
            
            messages.success(self.request, f'Goods Return {self.object.pk} updated successfully.')
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
    
    def get_success_url(self):
        # Return to update URL after successful update
        return reverse_lazy('Purchase:goods_return_update', kwargs={'pk': self.object.pk})

class GoodsReturnDetailView(DetailView):
    model = GoodsReturn
    template_name = 'common/formset-form.html'  
    context_object_name = 'goods_return'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Goods Return Details'
        context['subtitle'] = f'Goods Return {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Purchase:goods_return_list')
        context['update_url'] = reverse_lazy('Purchase:goods_return_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Purchase:goods_return_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = GoodsReturnForm(instance=self.object)
        context['extra_form'] = GoodsReturnExtraInfoForm(instance=self.object)
        context['formset'] = GoodsReturnLineFormSet(instance=self.object)
        
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

class GoodsReturnDeleteView(GenericDeleteView):
    model = GoodsReturn
    success_url = reverse_lazy('Purchase:goods_return_list')
    permission_required = 'Purchase.delete_goodsreturn'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Goods Return detail view.
        """
        return reverse_lazy('Purchase:goods_return_detail', kwargs={'pk': self.object.pk})        

class GoodsReturnExportView(BaseExportView):
    """
    Export view for Goods Return.
    """
    model = GoodsReturn
    filename = "goods_returns.csv"
    permission_required = "Purchase.view_goodsreturn"
    field_names = ["ID", "Document Date", "Posting Date", "Vendor", "Status", "Total Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class GoodsReturnBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Goods Returns.
    """
    model = GoodsReturn
    permission_required = "Purchase.delete_goodsreturn"
    display_fields = ["id", "document_date", "vendor", "status"]
    cancel_url = reverse_lazy("Purchase:goods_return_list")
    success_url = reverse_lazy("Purchase:goods_return_list")

