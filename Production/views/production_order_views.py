from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q

from ..models import ProductionOrder, ProductionOrderComponent, BillOfMaterials, BOMComponent
from Inventory.models import Item, Warehouse
from ..forms.production_order_forms import (
    ProductionOrderForm, ProductionOrderComponentFormSet, ProductionOrderFilterForm
)
from config.views import (
    GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView
)

class ProductionOrderListView(GenericFilterView):
    model = ProductionOrder
    template_name = 'production/production_order_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = ProductionOrderFilterForm
    permission_required = 'Production.view_productionorder'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('product', 'bom', 'warehouse').order_by('-document_date')

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(order_number__icontains=search_query) |
                Q(product__name__icontains=search_query) |
                Q(bom__name__icontains=search_query)
            )

        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        product = self.request.GET.get('product')
        if product:
            queryset = queryset.filter(product_id=product)
            
        warehouse = self.request.GET.get('warehouse')
        if warehouse:
            queryset = queryset.filter(warehouse_id=warehouse)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Orders'
        context['subtitle'] = 'Manage production orders'
        context['create_url'] = reverse_lazy('Production:production_order_create')
        context['list_url'] = reverse_lazy('Production:production_order_list')
        context['print_url'] = reverse_lazy('Production:production_order_export')
        context['model_name'] = 'Production Order'
        
        context['can_create'] = self.request.user.has_perm('Production.add_productionorder')
        context['can_view'] = self.request.user.has_perm('Production.view_productionorder')
        context['can_update'] = self.request.user.has_perm('Production.change_productionorder')
        context['can_delete'] = self.request.user.has_perm('Production.delete_productionorder')
        context['can_print'] = self.request.user.has_perm('Production.view_productionorder')
        context['can_export'] = self.request.user.has_perm('Production.view_productionorder')
        
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
        context['submit_text'] = 'Create Order'
        
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
                # Save the main form
                self.object = form.save(commit=False)
                self.object.created_by = self.request.user
                self.object.save()
                
                # Save the formset
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
        context['subtitle'] = f'Edit order {self.object.order_number}'
        context['cancel_url'] = reverse_lazy('Production:production_order_detail', kwargs={'pk': self.object.pk})
        context['submit_text'] = 'Update Order'
        
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
                # Save the main form
                self.object = form.save(commit=False)
                self.object.updated_by = self.request.user
                self.object.save()
                
                # Save the formset
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
        context['subtitle'] = f'Order {self.object.order_number}'
        context['cancel_url'] = reverse_lazy('Production:production_order_list')
        context['update_url'] = reverse_lazy('Production:production_order_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Production:production_order_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add conversion buttons if order is in appropriate status
        if self.object.status in ['Released', 'In Process']:
            context['action_buttons'] = [
                {
                    'url': reverse_lazy('Production:production_receipt_create') + f'?production_order={self.object.pk}',
                    'text': 'Create Receipt',
                    'icon': 'package',
                    'class': 'bg-green-100 text-green-700 hover:bg-green-200'
                },
                {
                    'url': reverse_lazy('Production:production_issue_create') + f'?production_order={self.object.pk}',
                    'text': 'Create Issue',
                    'icon': 'send',
                    'class': 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }
            ]
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = ProductionOrderForm(instance=self.object)
        context['formset'] = ProductionOrderComponentFormSet(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        # Make formset fields read-only
        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['disabled'] = 'disabled'
        
        return context

class ProductionOrderDeleteView(GenericDeleteView):
    model = ProductionOrder
    success_url = reverse_lazy('Production:production_order_list')
    permission_required = 'Production.delete_productionorder'
    template_name = 'common/delete_confirm.html'

    def get_cancel_url(self):
        return reverse_lazy('Production:production_order_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = 'Production Order'
        return context

class ProductionOrderExportView(BaseExportView):
    model = ProductionOrder
    filename = "production_orders.csv"
    permission_required = "Production.view_productionorder"
    field_names = ["Order Number", "Document Date", "Product", "BOM", "Warehouse", "Planned Quantity", "Produced Quantity", "Status"]

class ProductionOrderBulkDeleteView(BaseBulkDeleteConfirmView):
    model = ProductionOrder
    permission_required = "Production.delete_productionorder"
    display_fields = ["order_number", "document_date", "product", "status"]
    cancel_url = reverse_lazy("Production:production_order_list")
    success_url = reverse_lazy("Production:production_order_list")

# API Views for auto-fill functionality
class BOMComponentsAPIView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'Production.view_bomcomponent'
    
    def get(self, request, bom_id):
        try:
            bom = get_object_or_404(BillOfMaterials, id=bom_id)
            components = BOMComponent.objects.filter(bom=bom)
            
            component_data = []
            for component in components:
                component_data.append({
                    'item_code': component.item_code,
                    'item_name': component.item_name,
                    'quantity': float(component.quantity),
                    'unit': component.unit,
                })
            
            return JsonResponse({
                'success': True,
                'components': component_data,
                'x_quantity': float(bom.x_quantity) if bom.x_quantity else 1.0
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

class ProductBOMsAPIView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'Production.view_billofmaterials'
    
    def get(self, request, product_id):
        try:
            product = get_object_or_404(Item, id=product_id)
            boms = BillOfMaterials.objects.filter(product=product, status='Active')
            
            bom_data = []
            for bom in boms:
                bom_data.append({
                    'id': bom.id,
                    'code': bom.code,
                    'name': bom.name,
                    'bom_type': bom.bom_type,
                    'x_quantity': float(bom.x_quantity) if bom.x_quantity else 1.0,
                })
            
            return JsonResponse({
                'success': True,
                'boms': bom_data
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

class ProductInfoAPIView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'Production.view_productionorder'
    
    def get(self, request, product_id):
        try:
            product = get_object_or_404(Item, id=product_id)
            
            product_data = {
                'id': product.id,
                'code': product.code,
                'name': product.name,
                'sales_uom': product.sales_uom.name if product.sales_uom else '',
                'description': product.description if hasattr(product, 'description') else '',
            }
            
            return JsonResponse({
                'success': True,
                'product': product_data
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
