from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect

from ..models import ProductionReceipt
from ..forms.production_receipt_forms import (
    ProductionReceiptForm,
    ProductionReceiptExtraInfoForm,
    get_production_receipt_line_formset,
)
from config.views import (
    GenericFilterView,
    GenericDeleteView,
    BaseExportView,
    BaseBulkDeleteConfirmView,
)

class ProductionReceiptListView(GenericFilterView):
    model = ProductionReceipt
    template_name = 'production/production_receipt_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Production.view_productionreceipt'

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-document_date', '-id')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                id__icontains=search_query
            ) | queryset.filter(
                receipt_number__icontains=search_query
            ) | queryset.filter(
                remarks__icontains=search_query
            ) | queryset.filter(
                status__icontains=search_query
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Receipts'
        context['subtitle'] = 'Manage production receipts'
        context['create_url'] = reverse_lazy('Production:production_receipt_create')
        context['can_create'] = self.request.user.has_perm('Production.add_productionreceipt')
        context['can_view'] = self.request.user.has_perm('Production.view_productionreceipt')
        context['can_update'] = self.request.user.has_perm('Production.change_productionreceipt')
        context['can_delete'] = self.request.user.has_perm('Production.delete_productionreceipt')
        context['can_print'] = self.request.user.has_perm('Production.view_productionreceipt')
        context['can_export'] = self.request.user.has_perm('Production.view_productionreceipt')
        context['can_bulk_delete'] = self.request.user.has_perm('Production.delete_productionreceipt')
        return context

class ProductionReceiptCreateView(CreateView):
    model = ProductionReceipt
    form_class = ProductionReceiptForm
    template_name = 'common/formset-form.html'
    permission_required = 'Production.add_productionreceipt'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Production Receipt'
        context['subtitle'] = 'Create a new production receipt'
        context['cancel_url'] = reverse_lazy('Production:production_receipt_list')
        context['submit_text'] = 'Create Receipt'

        if self.request.POST:
            context['formset'] = get_production_receipt_line_formset(self.request, data=self.request.POST)
            context['extra_form'] = ProductionReceiptExtraInfoForm(self.request.POST)
        else:
            context['formset'] = get_production_receipt_line_formset(self.request)
            context['extra_form'] = ProductionReceiptExtraInfoForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']

        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                self.object = form.save()
                for field, value in extra_form.cleaned_data.items():
                    if hasattr(self.object, field):
                        setattr(self.object, field, value)
                self.object.save()
                formset.instance = self.object
                formset.save()

            messages.success(self.request, f"Production Receipt {self.object.pk} created successfully.")
            return HttpResponseRedirect(self.get_success_url())

        return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('Production:production_receipt_update', kwargs={'pk': self.object.pk})

class ProductionReceiptUpdateView(UpdateView):
    model = ProductionReceipt
    form_class = ProductionReceiptForm
    template_name = 'common/formset-form.html'
    permission_required = 'Production.change_productionreceipt'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Production Receipt'
        context['subtitle'] = f'Edit receipt {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Production:production_receipt_list')
        context['submit_text'] = 'Update Receipt'

        if self.request.POST:
            context['formset'] = get_production_receipt_line_formset(self.request, data=self.request.POST, instance=self.object)
            context['extra_form'] = ProductionReceiptExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = get_production_receipt_line_formset(self.request, instance=self.object)
            context['extra_form'] = ProductionReceiptExtraInfoForm(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']

        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                self.object = form.save()
                for field, value in extra_form.cleaned_data.items():
                    if hasattr(self.object, field):
                        setattr(self.object, field, value)
                self.object.save()
                formset.instance = self.object
                formset.save()

            messages.success(self.request, f"Production Receipt {self.object.pk} updated successfully.")
            return HttpResponseRedirect(self.get_success_url())

        return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('Production:production_receipt_update', kwargs={'pk': self.object.pk})

class ProductionReceiptDetailView(DetailView):
    model = ProductionReceipt
    template_name = 'common/formset-form.html'
    context_object_name = 'production_receipt'
    permission_required = 'Production.view_productionreceipt'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Receipt Details'
        context['subtitle'] = f'Receipt {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Production:production_receipt_list')
        context['update_url'] = reverse_lazy('Production:production_receipt_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Production:production_receipt_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True

        context['form'] = ProductionReceiptForm(instance=self.object, request=self.request)
        context['extra_form'] = ProductionReceiptExtraInfoForm(instance=self.object)
        context['formset'] = get_production_receipt_line_formset(self.request, instance=self.object)

        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'

        for form_field in context['extra_form'].fields.values():
            form_field.widget.attrs['readonly'] = True

        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True

        return context

class ProductionReceiptDeleteView(GenericDeleteView):
    model = ProductionReceipt
    success_url = reverse_lazy('Production:production_receipt_list')
    permission_required = 'Production.delete_productionreceipt'

    def get_cancel_url(self):
        return reverse_lazy('Production:production_receipt_detail', kwargs={'pk': self.object.pk})

class ProductionReceiptExportView(BaseExportView):
    model = ProductionReceipt
    filename = "production_receipts.csv"
    permission_required = "Production.view_productionreceipt"
    field_names = ["ID", "Receipt Number", "Document Date", "Production Order", "Warehouse", "Status"]

    def queryset_filter(self, request, queryset):
        return queryset

class ProductionReceiptPrintView(DetailView):
    model = ProductionReceipt
    template_name = 'production/production_receipt_print.html'
    context_object_name = 'production_receipt'
    permission_required = 'Production.view_productionreceipt'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Receipt'
        context['subtitle'] = f'Receipt {self.object.pk}'
        return context

class ProductionReceiptBulkDeleteView(BaseBulkDeleteConfirmView):
    model = ProductionReceipt
    permission_required = "Production.delete_productionreceipt"
    display_fields = ["id", "receipt_number", "document_date", "status"]
    cancel_url = reverse_lazy("Production:production_receipt_list")
    success_url = reverse_lazy("Production:production_receipt_list")
