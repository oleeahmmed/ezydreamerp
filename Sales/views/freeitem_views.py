from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from Sales.models import FreeItemDiscount
from Sales.forms import FreeItemDiscountForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class FreeItemDiscountListView(GenericFilterView):
    model = FreeItemDiscount
    template_name = 'sales/freeitemdiscount_list.html'
    context_object_name = 'objects'
    permission_required = 'Sales.view_freeitemdiscount'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Free Item Discounts',
            'subtitle': 'Manage free item discount rules',
            'create_url': reverse_lazy('Sales:freeitemdiscount_create'),
            'can_create': self.request.user.has_perm('Sales.add_freeitemdiscount'),
            'can_view': self.request.user.has_perm('Sales.view_freeitemdiscount'),
            'can_update': self.request.user.has_perm('Sales.change_freeitemdiscount'),
            'can_delete': self.request.user.has_perm('Sales.delete_freeitemdiscount'),
        })
        return context

class FreeItemDiscountCreateView(CreateView):
    model = FreeItemDiscount
    form_class = FreeItemDiscountForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('Sales:freeitemdiscount_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Create Free Item Discount',
            'submit_text': 'Create Discount',
            'cancel_url': reverse_lazy('Sales:freeitemdiscount_list')
        })
        return context

    def form_valid(self, form):
        messages.success(self.request, "Free item discount created successfully.")
        return super().form_valid(form)

class FreeItemDiscountUpdateView(UpdateView):
    model = FreeItemDiscount
    form_class = FreeItemDiscountForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('Sales:freeitemdiscount_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'Edit Free Discount #{self.object.pk}',
            'submit_text': 'Update Discount',
            'cancel_url': reverse_lazy('Sales:freeitemdiscount_list')
        })
        return context

    def form_valid(self, form):
        messages.success(self.request, "Free item discount updated successfully.")
        return super().form_valid(form)

class FreeItemDiscountDetailView(DetailView):
    model = FreeItemDiscount
    template_name = 'sales/freeitemdiscount_detail.html'
    context_object_name = 'discount'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'Discount Details #{self.object.pk}',
            'cancel_url': reverse_lazy('Sales:freeitemdiscount_list'),
            'update_url': reverse_lazy('Sales:freeitemdiscount_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('Sales:freeitemdiscount_delete', kwargs={'pk': self.object.pk}),
        })
        return context

class FreeItemDiscountDeleteView(GenericDeleteView):
    model = FreeItemDiscount
    success_url = reverse_lazy('Sales:freeitemdiscount_list')
    permission_required = 'Sales.delete_freeitemdiscount'

    def get_cancel_url(self):
        return reverse_lazy('Sales:freeitemdiscount_detail', kwargs={'pk': self.object.pk})

class FreeItemDiscountExportView(BaseExportView):
    model = FreeItemDiscount
    filename = "free_item_discounts.csv"
    permission_required = "Sales.view_freeitemdiscount"
    field_names = ["ID", "Item", "Buy Quantity", "Free Quantity", "Free Item"]

    def queryset_filter(self, request, queryset):
        return queryset

class FreeItemDiscountBulkDeleteView(BaseBulkDeleteConfirmView):
    model = FreeItemDiscount
    permission_required = "Sales.delete_freeitemdiscount"
    display_fields = ["id", "item", "buy_quantity", "free_quantity", "free_item"]
    cancel_url = reverse_lazy("Sales:freeitemdiscount_list")
    success_url = reverse_lazy("Sales:freeitemdiscount_list")
