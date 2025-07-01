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

from ..models import AccountType
from ..forms import AccountTypeForm, AccountTypeFilterForm

class AccountTypeAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class AccountTypeListView(AccountTypeAccessMixin, ListView):
    model = AccountType
    template_name = 'finance/account_type_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Finance.view_accounttype'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get filter parameters from request
        search = self.request.GET.get('search', '')
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'filter_form': AccountTypeFilterForm(self.request.GET) if hasattr(self, 'request') else None,
            'title': "Account Types",
            'subtitle': "Manage account types",
            'create_url': reverse_lazy('Finance:account_type_create'),
            'print_url': reverse_lazy('Finance:account_type_print_list'),
            'export_url': reverse_lazy('Finance:account_type_export'),
            'model_name': "account type",
            'can_create': self.request.user.has_perm('Finance.add_accounttype'),
            'can_delete': self.request.user.has_perm('Finance.delete_accounttype'),
        })
        return context

class AccountTypeCreateView(AccountTypeAccessMixin, SuccessMessageMixin, CreateView):
    model = AccountType
    form_class = AccountTypeForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Finance:account_type_list')
    success_message = "Account Type %(name)s was created successfully"
    permission_required = 'Finance.add_accounttype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Account Type",
            'subtitle': "Add a new account type",
            'cancel_url': reverse_lazy('Finance:account_type_list'),
        })
        return context

class AccountTypeUpdateView(AccountTypeAccessMixin, SuccessMessageMixin, UpdateView):
    model = AccountType
    form_class = AccountTypeForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Finance:account_type_list')
    success_message = "Account Type %(name)s was updated successfully"
    permission_required = 'Finance.change_accounttype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Account Type",
            'subtitle': f"Edit details for {self.object.name}",
            'cancel_url': reverse_lazy('Finance:account_type_detail', kwargs={'pk': self.object.pk}),
        })
        return context

class AccountTypeDeleteView(AccountTypeAccessMixin, SuccessMessageMixin, DeleteView):
    model = AccountType
    template_name = 'common/delete_confirm.html'
    success_url = reverse_lazy('Finance:account_type_list')
    success_message = "Account Type was deleted successfully"
    permission_required = 'Finance.delete_accounttype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Delete Account Type",
            'subtitle': f"Delete account type {self.object.name}",
            'cancel_url': reverse_lazy('Finance:account_type_detail', kwargs={'pk': self.object.pk}),
        })
        return context

class AccountTypeDetailView(AccountTypeAccessMixin, DetailView):
    model = AccountType
    template_name = 'common/premium-form.html'
    permission_required = 'Finance.view_accounttype'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Account Type Details",
            'subtitle': f"View details for {self.object.name}",
            'form': AccountTypeForm(instance=self.object),
            'readonly': True,
            'print_url': reverse_lazy('Finance:account_type_print_detail', kwargs={'pk': self.object.pk}),
            'update_url': reverse_lazy('Finance:account_type_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('Finance:account_type_delete', kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('Finance:account_type_list'),
            'can_update': self.request.user.has_perm('Finance.change_accounttype'),
            'can_delete': self.request.user.has_perm('Finance.delete_accounttype'),
        })
        return context

class AccountTypePrintDetailView(AccountTypeAccessMixin, View):
    permission_required = 'Finance.view_accounttype'
    template_name = 'finance/account_type_print_detail.html'

    def get(self, request, *args, **kwargs):
        account_type = get_object_or_404(AccountType, pk=kwargs['pk'])
        context = {
            'account_type': account_type,
            'title': f'Account Type: {account_type.code}',
            'user': request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        return render(request, self.template_name, context)

class AccountTypePrintView(AccountTypeAccessMixin, View):
    permission_required = 'Finance.view_accounttype'
    template_name = 'finance/account_type_print_list.html'

    def get_context_data(self, **kwargs):
        context = {
            'user': self.request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        
        if 'pk' in kwargs:
            # Single account type print view
            account_type = get_object_or_404(AccountType, pk=kwargs['pk'])
            
            context.update({
                'account_type': account_type,
                'title': f'Account Type: {account_type.code}',
            })
            template_name = 'finance/account_type_print_detail.html'
        else:
            # List print view
            account_types = AccountType.objects.all()
            
            context.update({
                'account_types': account_types,
                'title': 'Account Types List',
            })
            template_name = 'finance/account_type_print_list.html'
        
        return render(request, template_name, context)

class AccountTypeExportView(AccountTypeAccessMixin, View):
    permission_required = 'Finance.view_accounttype'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="account_types.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Code', 'Name', 'Is Debit'
        ])

        account_types = AccountType.objects.values_list(
            'code', 'name', 'is_debit'
        )
        
        for account_type in account_types:
            writer.writerow(account_type)

        return response

class AccountTypeBulkDeleteView(AccountTypeAccessMixin, View):
    permission_required = 'Finance.delete_accounttype'
    template_name = 'common/bulk_delete_confirm.html'

    def get(self, request, *args, **kwargs):
        # Get the selected account type IDs from the query parameters
        selected_ids = request.GET.getlist('ids')
        
        if not selected_ids:
            messages.error(request, "No account types selected for deletion.")
            return redirect('Finance:account_type_list')
        
        # Get the account types to be deleted
        account_types = AccountType.objects.filter(id__in=selected_ids)
        
        if not account_types.exists():
            messages.error(request, "No valid account types found for deletion.")
            return redirect('Finance:account_type_list')
        
        context = {
            'objects': account_types,
            'selected_ids': selected_ids,
            'title': 'Confirm Bulk Delete',
            'subtitle': f'Delete {len(selected_ids)} selected account types',
            'model_name': 'account type',
            'delete_url': reverse_lazy('Finance:account_type_bulk_delete'),
            'cancel_url': reverse_lazy('Finance:account_type_list'),
        }
        
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        try:
            ids = request.POST.getlist('ids')
            if not ids:
                messages.error(request, "No account types selected for deletion.")
                return redirect('Finance:account_type_list')
            
            deleted_count = AccountType.objects.filter(id__in=ids).delete()[0]
            
            if deleted_count > 0:
                messages.success(request, f"{deleted_count} account type(s) deleted successfully.")
            else:
                messages.warning(request, "No account types were deleted.")
                
            return redirect('Finance:account_type_list')
            
        except Exception as e:
            messages.error(request, f"Error deleting account types: {str(e)}")
            return redirect('Finance:account_type_list')