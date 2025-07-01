from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from ..models import ProductionOrder, ProductionOrderComponent
from ..forms.production_order_forms import ProductionOrderForm, ProductionOrderComponentFormSet, ProductionOrderFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class ProductionOrderListView(GenericFilterView):
    model = ProductionOrder
    template_name = 'production/production_order_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = ProductionOrderFilterForm
    permission_required = 'Production.view_productionorder'

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                order_number__icontains=search_query
            ) | queryset.filter(
                product__name__icontains=search_query
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Orders'
        context['subtitle'] = 'Manage production orders'
        context['create_url'] = reverse_lazy('Production:production_order_create')
        context['bulk_delete_url'] = reverse_lazy('Production:production_order_bulk_delete')
        context['can_create'] = self.request.user.has_perm('Production.add_productionorder')
        context['can_view'] = self.request.user.has_perm('Production.view_productionorder')
        context['can_update'] = self.request.user.has_perm('Production.change_productionorder')
        context['can_delete'] = self.request.user.has_perm('Production.delete_productionorder')
        context['can_export'] = self.request.user.has_perm('Production.view_productionorder')
        context['can_bulk_delete'] = self.request.user.has_perm('Production.delete_productionorder')
        return context

class ProductionOrderCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ProductionOrder
    form_class = ProductionOrderForm
    template_name = 'production/production_order_form.html'
    permission_required = 'Production.add_productionorder'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Production Order'
        context['subtitle'] = 'Create a new production order'
        context['cancel_url'] = reverse_lazy('Production:production_order_list')
        context['submit_text'] = 'Create Production Order'
        if self.request.POST:
            context['formset'] = ProductionOrderComponentFormSet(self.request.POST)
        else:
            context['formset'] = ProductionOrderComponentFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                formset.instance = self.object
                formset.save()
            messages.success(self.request, f'Production Order {self.object.order_number} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('Production:production_order_detail', kwargs={'pk': self.object.pk})

class ProductionOrderUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ProductionOrder
    form_class = ProductionOrderForm
    template_name = 'production/production_order_form.html'
    permission_required = 'Production.change_productionorder'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Production Order'
        context['subtitle'] = f'Edit Production Order {self.object.order_number}'
        context['cancel_url'] = reverse_lazy('Production:production_order_detail', kwargs={'pk': self.object.pk})
        context['submit_text'] = 'Update Production Order'
        if self.request.POST:
            context['formset'] = ProductionOrderComponentFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = ProductionOrderComponentFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                formset.instance = self.object
                formset.save()
            messages.success(self.request, f'Production Order {self.object.order_number} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('Production:production_order_detail', kwargs={'pk': self.object.pk})

class ProductionOrderDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ProductionOrder
    template_name = 'production/production_order_form.html'
    context_object_name = 'production_order'
    permission_required = 'Production.view_productionorder'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Order Details'
        context['subtitle'] = f'Production Order {self.object.order_number}'
        context['cancel_url'] = reverse_lazy('Production:production_order_list')
        context['update_url'] = reverse_lazy('Production:production_order_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Production:production_order_delete', kwargs={'pk': self.object.pk})
        context['is_detail'] = True
        context['form'] = ProductionOrderForm(instance=self.object)
        context['formset'] = ProductionOrderComponentFormSet(instance=self.object)
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = True
        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['disabled'] = True
        return context

class ProductionOrderDeleteView(GenericDeleteView):
    model = ProductionOrder
    template_name = 'production/production_order_confirm_delete.html'
    permission_required = 'Production.delete_productionorder'
    success_url = reverse_lazy('Production:production_order_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Production Order'
        context['subtitle'] = f'Are you sure you want to delete Production Order {self.object.order_number}?'
        context['cancel_url'] = reverse_lazy('Production:production_order_detail', kwargs={'pk': self.object.pk})
        return context

class ProductionOrderExportView(BaseExportView):
    model = ProductionOrder
    permission_required = 'Production.view_productionorder'
    field_names = ['Order Number', 'Document Date', 'Product Name', 'BOM Code', 'Warehouse Name', 'Planned Quantity', 'Status', 'Remarks']
    filename = 'production_orders.csv'

    def get_queryset(self, request):
        queryset = self.model.objects.all()
        if self.request.GET:
            form = ProductionOrderFilterForm(self.request.GET)
            if form.is_valid():
                if form.cleaned_data['order_number']:
                    queryset = queryset.filter(order_number__icontains=form.cleaned_data['order_number'])
                if form.cleaned_data['product']:
                    queryset = queryset.filter(product=form.cleaned_data['product'])
                if form.cleaned_data['bom']:
                    queryset = queryset.filter(bom=form.cleaned_data['bom'])
                if form.cleaned_data['warehouse']:
                    queryset = queryset.filter(warehouse=form.cleaned_data['warehouse'])
                if form.cleaned_data['status']:
                    queryset = queryset.filter(status=form.cleaned_data['status'])
        return queryset

class ProductionOrderBulkDeleteView(BaseBulkDeleteConfirmView):
    model = ProductionOrder
    permission_required = 'Production.delete_productionorder'
    display_fields = ['order_number', 'product__name', 'status']
    cancel_url = reverse_lazy('Production:production_order_list')
    success_url = reverse_lazy('Production:production_order_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Bulk Delete Production Orders'
        context['subtitle'] = 'Are you sure you want to delete the selected production orders?'
        return context