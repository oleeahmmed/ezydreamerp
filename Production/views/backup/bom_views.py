from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
import csv
from decimal import Decimal

from ..models import BillOfMaterials, BOMComponent
from ..forms.bom_forms import BillOfMaterialsForm, BOMComponentFormSet, BillOfMaterialsFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class BillOfMaterialsListView(GenericFilterView):
    model = BillOfMaterials
    template_name = 'production/bill_of_materials_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = BillOfMaterialsFilterForm
    permission_required = 'Production.view_billofmaterials'
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(code__icontains=search_query) | queryset.filter(name__icontains=search_query) | queryset.filter(product__name__icontains=search_query)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Bills of Materials'
        context['subtitle'] = 'Manage bills of materials'
        context['create_url'] = reverse_lazy('Production:bill_of_materials_create')
        context['bulk_delete_url'] = reverse_lazy('Production:bill_of_materials_bulk_delete')
        context['can_create'] = self.request.user.has_perm('Production.add_billofmaterials')
        context['can_view'] = self.request.user.has_perm('Production.view_billofmaterials')
        context['can_update'] = self.request.user.has_perm('Production.change_billofmaterials')
        context['can_delete'] = self.request.user.has_perm('Production.delete_billofmaterials')
        context['can_export'] = self.request.user.has_perm('Production.view_billofmaterials')
        context['can_bulk_delete'] = self.request.user.has_perm('Production.delete_billofmaterials')
        return context

class BillOfMaterialsCreateView(CreateView):
    model = BillOfMaterials
    form_class = BillOfMaterialsForm
    template_name = 'production/bom_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Bill of Materials'
        context['subtitle'] = 'Create a new bill of materials'
        context['cancel_url'] = reverse_lazy('Production:bill_of_materials_list')
        context['submit_text'] = 'Create BOM'
        if self.request.POST:
            context['formset'] = BOMComponentFormSet(self.request.POST)
        else:
            context['formset'] = BOMComponentFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                formset.instance = self.object
                formset.save()
                self.object.calculate_totals()
            messages.success(self.request, f'Bill of Materials {self.object.code} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)
            if hasattr(formset, 'non_form_errors'):
                print("Formset non-form errors:", formset.non_form_errors())
            for i, form_instance in enumerate(formset.forms):
                if form_instance.errors:
                    print(f"Formset form {i} errors:", form_instance.errors)
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Production:bill_of_materials_detail', kwargs={'pk': self.object.pk})

class BillOfMaterialsUpdateView(UpdateView):
    model = BillOfMaterials
    form_class = BillOfMaterialsForm
    template_name = 'production/bom_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Bill of Materials'
        context['subtitle'] = f'Edit BOM {self.object.code}'
        context['cancel_url'] = reverse_lazy('Production:bill_of_materials_detail', kwargs={'pk': self.object.pk})
        context['submit_text'] = 'Update BOM'
        if self.request.POST:
            context['formset'] = BOMComponentFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = BOMComponentFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                formset.instance = self.object
                formset.save()
                self.object.calculate_totals()
            messages.success(self.request, f'Bill of Materials {self.object.code} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)
            if hasattr(formset, 'non_form_errors'):
                print("Formset non-form errors:", formset.non_form_errors())
            for i, form_instance in enumerate(formset.forms):
                if form_instance.errors:
                    print(f"Formset form {i} errors:", form_instance.errors)
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Production:bill_of_materials_detail', kwargs={'pk': self.object.pk})

class BillOfMaterialsDetailView(DetailView):
    model = BillOfMaterials
    template_name = 'production/bom_form.html'
    context_object_name = 'bill_of_materials'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Bill of Materials Details'
        context['subtitle'] = f'BOM {self.object.code}'
        context['cancel_url'] = reverse_lazy('Production:bill_of_materials_list')
        context['update_url'] = reverse_lazy('Production:bill_of_materials_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Production:bill_of_materials_delete', kwargs={'pk': self.object.pk})
        context['is_detail'] = True
        context['form'] = BillOfMaterialsForm(instance=self.object)
        context['formset'] = BOMComponentFormSet(instance=self.object)
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = True
        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['disabled'] = True
        return context

class BillOfMaterialsDeleteView(GenericDeleteView):
    model = BillOfMaterials
    success_url = reverse_lazy('Production:bill_of_materials_list')
    permission_required = 'Production.delete_billofmaterials'

    def get_cancel_url(self):
        return reverse_lazy('Production:bill_of_materials_detail', kwargs={'pk': self.object.pk})

class BillOfMaterialsExportView(BaseExportView):
    model = BillOfMaterials
    filename = "bills_of_materials.csv"
    permission_required = "Production.view_billofmaterials"
    field_names = ["Code", "Name", "Product", "BOM Type", "UOM", "X Quantity", "Project", "Status", "Total Component Value", "Other Cost %", "Additional Cost", "Total After Discount", "Created At"]

    def queryset_filter(self, request, queryset):
        return queryset

class BillOfMaterialsBulkDeleteView(BaseBulkDeleteConfirmView):
    model = BillOfMaterials
    permission_required = "Production.delete_billofmaterials"
    display_fields = ["code", "name", "product", "status"]
    cancel_url = reverse_lazy("Production:bill_of_materials_list")
    success_url = reverse_lazy("Production:bill_of_materials_list")