from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings

from ..models import ItemGroup
from ..forms import ItemGroupForm

from config.views import GenericFilterView, GenericDeleteView

class ItemGroupAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class ItemGroupListView(ItemGroupAccessMixin, GenericFilterView):
    model = ItemGroup
    template_name = 'inventory/item_group_list.html'
    context_object_name = 'objects'
    permission_required = 'Inventory.view_itemgroup'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Add any custom filtering logic here
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Item Groups",
            'subtitle': "Manage item groups",
            'create_url': reverse_lazy('Inventory:item_group_create'),
            'model_name': "item group",
            'can_create': self.request.user.has_perm('Inventory.add_itemgroup'),
            'can_delete': self.request.user.has_perm('Inventory.delete_itemgroup'),
        })
        return context

class ItemGroupCreateView(ItemGroupAccessMixin, SuccessMessageMixin, CreateView):
    model = ItemGroup
    form_class = ItemGroupForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Inventory:item_group_list')
    success_message = "Item Group %(name)s was created successfully"
    permission_required = 'Inventory.add_itemgroup'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Item Group",
            'subtitle': "Add a new item group",
            'cancel_url': reverse_lazy('Inventory:item_group_list'),
        })
        return context

class ItemGroupUpdateView(ItemGroupAccessMixin, SuccessMessageMixin, UpdateView):
    model = ItemGroup
    form_class = ItemGroupForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Inventory:item_group_list')
    success_message = "Item Group %(name)s was updated successfully"
    permission_required = 'Inventory.change_itemgroup'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Item Group",
            'subtitle': f"Edit details for {self.object.name}",
            'cancel_url': reverse_lazy('Inventory:item_group_detail', kwargs={'pk': self.object.pk}),
        })
        return context

class ItemGroupDeleteView(ItemGroupAccessMixin, GenericDeleteView):
    model = ItemGroup
    success_url = reverse_lazy('Inventory:item_group_list')
    permission_required = 'Inventory.delete_itemgroup'

    def get_cancel_url(self):
        return reverse_lazy('Inventory:item_group_detail', kwargs={'pk': self.object.pk})

class ItemGroupDetailView(ItemGroupAccessMixin, DetailView):
    model = ItemGroup
    template_name = 'common/premium-form.html'
    permission_required = 'Inventory.view_itemgroup'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Item Group Details",
            'subtitle': f"View details for {self.object.name}",
            'form': ItemGroupForm(instance=self.object),
            'readonly': True,
            'print_url': reverse_lazy('Inventory:item_group_print', kwargs={'pk': self.object.pk}),
            'update_url': reverse_lazy('Inventory:item_group_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('Inventory:item_group_delete', kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('Inventory:item_group_list'),
            'can_update': self.request.user.has_perm('Inventory.change_itemgroup'),
            'can_delete': self.request.user.has_perm('Inventory.delete_itemgroup'),
        })
        return context

class ItemGroupPrintView(ItemGroupAccessMixin, View):
    permission_required = 'Inventory.view_itemgroup'
    template_name = 'inventory/item_group_print.html'

    def get(self, request, *args, **kwargs):
        item_group = ItemGroup.objects.get(pk=kwargs['pk'])
        context = {
            'item_group': item_group,
            'user': request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        return render(request, self.template_name, context)