from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from django.db.models import Q

from ..models import UnitOfMeasure
from ..forms import UnitOfMeasureForm

from config.views import GenericFilterView, GenericDeleteView

class UnitOfMeasureAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class UnitOfMeasureListView(UnitOfMeasureAccessMixin, GenericFilterView):
    model = UnitOfMeasure
    template_name = 'inventory/uom_list.html'
    context_object_name = 'objects'
    permission_required = 'Inventory.view_unitofmeasure'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Add any custom filtering logic here
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )
            
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Units of Measure",
            'subtitle': "Manage units of measure",
            'create_url': reverse_lazy('Inventory:uom_create'),
            'model_name': "unit of measure",
            'can_create': self.request.user.has_perm('Inventory.add_unitofmeasure'),
            'can_delete': self.request.user.has_perm('Inventory.delete_unitofmeasure'),
        })
        return context

class UnitOfMeasureCreateView(UnitOfMeasureAccessMixin, SuccessMessageMixin, CreateView):
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Inventory:uom_list')
    success_message = "Unit of Measure %(name)s was created successfully"
    permission_required = 'Inventory.add_unitofmeasure'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Unit of Measure",
            'subtitle': "Add a new unit of measure",
            'cancel_url': reverse_lazy('Inventory:uom_list'),
        })
        return context

class UnitOfMeasureUpdateView(UnitOfMeasureAccessMixin, SuccessMessageMixin, UpdateView):
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Inventory:uom_list')
    success_message = "Unit of Measure %(name)s was updated successfully"
    permission_required = 'Inventory.change_unitofmeasure'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Unit of Measure",
            'subtitle': f"Edit details for {self.object.name}",
            'cancel_url': reverse_lazy('Inventory:uom_detail', kwargs={'pk': self.object.pk}),
        })
        return context

class UnitOfMeasureDeleteView(UnitOfMeasureAccessMixin, GenericDeleteView):
    model = UnitOfMeasure
    success_url = reverse_lazy('Inventory:uom_list')
    permission_required = 'Inventory.delete_unitofmeasure'

    def get_cancel_url(self):
        return reverse_lazy('Inventory:uom_detail', kwargs={'pk': self.object.pk})

class UnitOfMeasureDetailView(UnitOfMeasureAccessMixin, DetailView):
    model = UnitOfMeasure
    template_name = 'common/premium-form.html'
    permission_required = 'Inventory.view_unitofmeasure'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Unit of Measure Details",
            'subtitle': f"View details for {self.object.name}",
            'form': UnitOfMeasureForm(instance=self.object),
            'readonly': True,
            'print_url': reverse_lazy('Inventory:uom_print', kwargs={'pk': self.object.pk}),
            'update_url': reverse_lazy('Inventory:uom_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('Inventory:uom_delete', kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('Inventory:uom_list'),
            'can_update': self.request.user.has_perm('Inventory.change_unitofmeasure'),
            'can_delete': self.request.user.has_perm('Inventory.delete_unitofmeasure'),
        })
        return context

class UnitOfMeasurePrintView(UnitOfMeasureAccessMixin, View):
    permission_required = 'Inventory.view_unitofmeasure'
    template_name = 'inventory/uom_print.html'

    def get(self, request, *args, **kwargs):
        uom = UnitOfMeasure.objects.get(pk=kwargs['pk'])
        context = {
            'uom': uom,
            'user': request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        return render(request, self.template_name, context)