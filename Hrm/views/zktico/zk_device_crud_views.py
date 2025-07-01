# zk_device_crud_views.py
import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.utils.translation import gettext_lazy as _

from config.views import BaseBulkDeleteConfirmView, BaseBulkDeleteView, BaseExportView, GenericDeleteView, GenericFilterView
from Hrm.forms.zk_device_forms import ZKDeviceFilterForm, ZKDeviceForm
from Hrm.models import ZKDevice

# Attempt to import ZK library
try:
    from zk import ZK
    ZK_AVAILABLE = True
except ImportError:
    ZK_AVAILABLE = False
    logging.warning("ZK library not available. Please install it with 'pip install pyzk'")

logger = logging.getLogger(__name__)

# === ZK Device List View ===
class ZKDeviceListView(GenericFilterView):
    """List view for ZK Devices with filtering and pagination."""
    model = ZKDevice
    template_name = 'zk_device/device_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = ZKDeviceFilterForm
    permission_required = 'Hrm.view_zkdevice'

    def apply_filters(self, queryset):
        """Apply filters based on form data."""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(name__icontains=filters['search']) | queryset.filter(ip_address__icontains=filters['search'])
        if filters.get('is_active') is not None:
            queryset = queryset.filter(is_active=filters['is_active'])
        return queryset

    def get_context_data(self, **kwargs):
        """Add additional context data for the template."""
        context = super().get_context_data(**kwargs)
        context.update({
            'create_url': reverse_lazy('hrm:zk_device_create'),
            'can_create': self.request.user.has_perm('Hrm.add_zkdevice'),
            'can_view': self.request.user.has_perm('Hrm.view_zkdevice'),
            'can_update': self.request.user.has_perm('Hrm.change_zkdevice'),
            'can_delete': self.request.user.has_perm('Hrm.delete_zkdevice'),
            'can_export': self.request.user.has_perm('Hrm.view_zkdevice'),
            'can_bulk_delete': self.request.user.has_perm('Hrm.delete_zkdevice'),
            'zk_available': ZK_AVAILABLE,
        })
        return context

# === ZK Device Create View ===
class ZKDeviceCreateView(CreateView):
    """View for creating a new ZK Device."""
    model = ZKDevice
    form_class = ZKDeviceForm
    template_name = 'common/premium-form.html'

    def get_context_data(self, **kwargs):
        """Add title and cancel URL to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Create ZK Device',
            'subtitle': 'Register a new ZKTeco device',
            'cancel_url': reverse_lazy('hrm:zk_device_list'),
        })
        return context

    def form_valid(self, form):
        """Handle valid form submission."""
        self.object = form.save()
        messages.success(self.request, f'Device "{self.object.name}" created successfully.')
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to device detail page after creation."""
        return reverse_lazy('hrm:zk_device_detail', kwargs={'pk': self.object.pk})

# === ZK Device Update View ===
class ZKDeviceUpdateView(UpdateView):
    """View for updating an existing ZK Device."""
    model = ZKDevice
    form_class = ZKDeviceForm
    template_name = 'common/premium-form.html'

    def get_context_data(self, **kwargs):
        """Add title and cancel URL to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Update ZK Device',
            'subtitle': f'Edit device: {self.object.name}',
            'cancel_url': reverse_lazy('hrm:zk_device_detail', kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        """Handle valid form submission."""
        self.object = form.save()
        messages.success(self.request, f'Device "{self.object.name}" updated successfully.')
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to device detail page after update."""
        return reverse_lazy('hrm:zk_device_detail', kwargs={'pk': self.object.pk})

# === ZK Device Detail View ===
class ZKDeviceDetailView(DetailView):
    """View for displaying ZK Device details."""
    model = ZKDevice
    template_name = 'common/premium-form.html'
    context_object_name = 'device'

    def get_context_data(self, **kwargs):
        """Add form and URLs to context."""
        context = super().get_context_data(**kwargs)
        form = ZKDeviceForm(instance=self.object)
        for field in form.fields.values():
            field.widget.attrs.update({'readonly': True, 'disabled': 'disabled'})
        context.update({
            'title': 'ZK Device Details',
            'subtitle': self.object.name,
            'cancel_url': reverse_lazy('hrm:zk_device_list'),
            'update_url': reverse_lazy('hrm:zk_device_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('hrm:zk_device_delete', kwargs={'pk': self.object.pk}),
            'is_detail_view': True,
            'form': form,
        })
        return context

# === ZK Device Delete View ===
class ZKDeviceDeleteView(GenericDeleteView):
    """View for deleting a ZK Device."""
    model = ZKDevice
    success_url = reverse_lazy('hrm:zk_device_list')
    permission_required = 'Hrm.delete_zkdevice'

    def get_cancel_url(self):
        """Return URL to cancel deletion."""
        return reverse_lazy('hrm:zk_device_detail', kwargs={'pk': self.object.pk})

# === ZK Device Export View ===
class ZKDeviceExportView(BaseExportView):
    """View for exporting ZK Device data to CSV."""
    model = ZKDevice
    filename = "zk_devices.csv"
    permission_required = "Hrm.view_zkdevice"
    field_names = ["name", "ip_address", "port", "device_id", "is_active", "timeout", "force_udp", "created_at"]

    def queryset_filter(self, request, queryset):
        """Apply any filters to the queryset."""
        return queryset

# === ZK Device Bulk Delete View ===
class ZKDeviceBulkDeleteView(BaseBulkDeleteConfirmView):
    """View for bulk deleting ZK Devices."""
    model = ZKDevice
    permission_required = "Hrm.delete_zkdevice"
    display_fields = ["name", "ip_address", "is_active", "port"]
    cancel_url = reverse_lazy("hrm:zk_device_list")
    success_url = reverse_lazy("hrm:zk_device_list")