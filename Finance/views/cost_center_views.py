from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse, Http404
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
import csv

from ..models import CostCenter
from ..forms import CostCenterForm, CostCenterFilterForm

class CostCenterAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class CostCenterListView(CostCenterAccessMixin, ListView):
    model = CostCenter
    template_name = 'finance/cost_center_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Finance.view_costcenter'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get filter parameters from request
        search = self.request.GET.get('search', '')
        is_active = self.request.GET.get('is_active', '')
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )
        
        # Apply status filter
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'filter_form': CostCenterFilterForm(self.request.GET) if hasattr(self, 'request') else None,
            'title': "Cost Centers",
            'subtitle': "Manage cost centers for cost accounting",
            'create_url': reverse_lazy('Finance:cost_center_create'),
            'print_url': reverse_lazy('Finance:cost_center_print_list'),
            'export_url': reverse_lazy('Finance:cost_center_export'),
            'model_name': "cost center",
            'can_create': self.request.user.has_perm('Finance.add_costcenter'),
            'can_delete': self.request.user.has_perm('Finance.delete_costcenter'),
            'can_print': self.request.user.has_perm('Finance.view_costcenter'),
            'can_export': self.request.user.has_perm('Finance.view_costcenter'),
        })
        return context

class CostCenterCreateView(CostCenterAccessMixin, SuccessMessageMixin, CreateView):
    model = CostCenter
    form_class = CostCenterForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Finance:cost_center_list')
    success_message = "Cost Center %(name)s was created successfully"
    permission_required = 'Finance.add_costcenter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Cost Center",
            'subtitle': "Add a new cost center",
            'cancel_url': reverse_lazy('Finance:cost_center_list'),
        })
        return context

class CostCenterUpdateView(CostCenterAccessMixin, SuccessMessageMixin, UpdateView):
    model = CostCenter
    form_class = CostCenterForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Finance:cost_center_list')
    success_message = "Cost Center %(name)s was updated successfully"
    permission_required = 'Finance.change_costcenter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Cost Center",
            'subtitle': f"Edit details for {self.object.name}",
            'cancel_url': reverse_lazy('Finance:cost_center_detail', kwargs={'pk': self.object.pk}),
        })
        return context

class CostCenterDeleteView(CostCenterAccessMixin, SuccessMessageMixin, DeleteView):
    model = CostCenter
    template_name = 'common/delete_confirm.html'
    success_url = reverse_lazy('Finance:cost_center_list')
    success_message = "Cost Center was deleted successfully"
    permission_required = 'Finance.delete_costcenter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Delete Cost Center",
            'subtitle': f"Delete cost center {self.object.name}",
            'cancel_url': reverse_lazy('Finance:cost_center_detail', kwargs={'pk': self.object.pk}),
        })
        return context

class CostCenterDetailView(CostCenterAccessMixin, DetailView):
    model = CostCenter
    template_name = 'common/premium-form.html'
    permission_required = 'Finance.view_costcenter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Cost Center Details",
            'subtitle': f"View details for {self.object.name}",
            'form': CostCenterForm(instance=self.object),
            'readonly': True,
            'print_url': reverse_lazy('Finance:cost_center_print_detail', kwargs={'pk': self.object.pk}),
            'update_url': reverse_lazy('Finance:cost_center_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('Finance:cost_center_delete', kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('Finance:cost_center_list'),
            'can_update': self.request.user.has_perm('Finance.change_costcenter'),
            'can_delete': self.request.user.has_perm('Finance.delete_costcenter'),
        })
        return context

class CostCenterPrintDetailView(CostCenterAccessMixin, View):
    permission_required = 'Finance.view_costcenter'
    template_name = 'finance/cost_center_print_detail.html'

    def get(self, request, *args, **kwargs):
        cost_center = get_object_or_404(CostCenter, pk=kwargs['pk'])
        context = {
            'cost_center': cost_center,
            'title': f'Cost Center: {cost_center.code}',
            'user': request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        return render(request, self.template_name, context)

class CostCenterPrintView(CostCenterAccessMixin, View):
    permission_required = 'Finance.view_costcenter'
    template_name = 'finance/cost_center_print_list.html'

    def get(self, request, *args, **kwargs):
        queryset = CostCenter.objects.all()
        
        # Apply filters from request if any
        search = request.GET.get('search', '')
        is_active = request.GET.get('is_active', '')
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )
            
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        context = {
            'cost_centers': queryset,
            'title': 'Cost Centers List',
            'user': request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        return render(request, self.template_name, context)

class CostCenterExportView(CostCenterAccessMixin, View):
    permission_required = 'Finance.view_costcenter'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="cost_centers.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Code', 'Name', 'Parent', 'Is Active'
        ])

        queryset = CostCenter.objects.all()
        
        # Apply filters from request if any
        search = request.GET.get('search', '')
        is_active = request.GET.get('is_active', '')
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )
            
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        for cost_center in queryset:
            parent_name = cost_center.parent.name if cost_center.parent else ''
            writer.writerow([
                cost_center.code,
                cost_center.name,
                parent_name,
                'Yes' if cost_center.is_active else 'No'
            ])

        return response

class CostCenterBulkDeleteView(CostCenterAccessMixin, View):
    permission_required = 'Finance.delete_costcenter'
    template_name = 'common/bulk_delete_confirm.html'

    def get(self, request, *args, **kwargs):
        # Get the selected cost center IDs from the query parameters
        selected_ids = request.GET.getlist('ids')
        
        if not selected_ids:
            messages.error(request, "No cost centers selected for deletion.")
            return redirect('Finance:cost_center_list')
        
        # Get the cost centers to be deleted
        cost_centers = CostCenter.objects.filter(id__in=selected_ids)
        
        if not cost_centers.exists():
            messages.error(request, "No valid cost centers found for deletion.")
            return redirect('Finance:cost_center_list')
        
        context = {
            'objects': cost_centers,
            'selected_ids': selected_ids,
            'title': 'Confirm Bulk Delete',
            'subtitle': f'Delete {len(selected_ids)} selected cost centers',
            'model_name': 'cost center',
            'delete_url': reverse_lazy('Finance:cost_center_bulk_delete'),
            'cancel_url': reverse_lazy('Finance:cost_center_list'),
        }
        
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        try:
            ids = request.POST.getlist('ids')
            if not ids:
                messages.error(request, "No cost centers selected for deletion.")
                return redirect('Finance:cost_center_list')
            
            deleted_count = CostCenter.objects.filter(id__in=ids).delete()[0]
            
            if deleted_count > 0:
                messages.success(request, f"{deleted_count} cost center(s) deleted successfully.")
            else:
                messages.warning(request, "No cost centers were deleted.")
                
            return redirect('Finance:cost_center_list')
            
        except Exception as e:
            messages.error(request, f"Error deleting cost centers: {str(e)}")
            return redirect('Finance:cost_center_list')