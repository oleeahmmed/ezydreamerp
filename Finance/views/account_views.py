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

from ..models import ChartOfAccounts
from ..forms import AccountForm, AccountFilterForm

class AccountAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class AccountListView(AccountAccessMixin, ListView):
    model = ChartOfAccounts
    template_name = 'finance/account_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Finance.view_chartofaccounts'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get filter parameters from request
        search = self.request.GET.get('search', '')
        account_type = self.request.GET.get('account_type', '')
        is_active = self.request.GET.get('is_active', '')
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )
        
        # Apply account type filter
        if account_type:
            queryset = queryset.filter(account_type_id=account_type)
            
        # Apply active status filter
        if is_active:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'filter_form': AccountFilterForm(self.request.GET) if hasattr(self, 'request') else None,
            'title': "Chart of Accounts",
            'subtitle': "Manage accounts",
            'create_url': reverse_lazy('Finance:account_create'),
            'print_url': reverse_lazy('Finance:account_print_list'),
            'export_url': reverse_lazy('Finance:account_export'),
            'model_name': "account",
            'can_create': self.request.user.has_perm('Finance.add_chartofaccounts'),
            'can_delete': self.request.user.has_perm('Finance.delete_chartofaccounts'),
        })
        return context

class AccountCreateView(AccountAccessMixin, SuccessMessageMixin, CreateView):
    model = ChartOfAccounts
    form_class = AccountForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Finance:account_list')
    success_message = "Account %(name)s was created successfully"
    permission_required = 'Finance.add_chartofaccounts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Account",
            'subtitle': "Add a new account",
            'cancel_url': reverse_lazy('Finance:account_list'),
        })
        return context

class AccountUpdateView(AccountAccessMixin, SuccessMessageMixin, UpdateView):
    model = ChartOfAccounts
    form_class = AccountForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Finance:account_list')
    success_message = "Account %(name)s was updated successfully"
    permission_required = 'Finance.change_chartofaccounts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Account",
            'subtitle': f"Edit details for {self.object.name}",
            'cancel_url': reverse_lazy('Finance:account_detail', kwargs={'pk': self.object.pk}),
        })
        return context

class AccountDeleteView(AccountAccessMixin, SuccessMessageMixin, DeleteView):
    model = ChartOfAccounts
    template_name = 'common/delete_confirm.html'
    success_url = reverse_lazy('Finance:account_list')
    success_message = "Account was deleted successfully"
    permission_required = 'Finance.delete_chartofaccounts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Delete Account",
            'subtitle': f"Delete account {self.object.name}",
            'cancel_url': reverse_lazy('Finance:account_detail', kwargs={'pk': self.object.pk}),
        })
        return context

class AccountDetailView(AccountAccessMixin, DetailView):
    model = ChartOfAccounts
    template_name = 'common/premium-form.html'
    permission_required = 'Finance.view_chartofaccounts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Account Details",
            'subtitle': f"View details for {self.object.name}",
            'form': AccountForm(instance=self.object),
            'readonly': True,
            'print_url': reverse_lazy('Finance:account_print_detail', kwargs={'pk': self.object.pk}),
            'update_url': reverse_lazy('Finance:account_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('Finance:account_delete', kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('Finance:account_list'),
            'can_update': self.request.user.has_perm('Finance.change_chartofaccounts'),
            'can_delete': self.request.user.has_perm('Finance.delete_chartofaccounts'),
        })
        return context

class AccountPrintDetailView(AccountAccessMixin, View):
    permission_required = 'Finance.view_chartofaccounts'
    template_name = 'finance/account_print_detail.html'

    def get(self, request, *args, **kwargs):
        account = get_object_or_404(ChartOfAccounts, pk=kwargs['pk'])
        context = {
            'account': account,
            'title': f'Account: {account.code}',
            'user': request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        return render(request, self.template_name, context)

class AccountPrintView(AccountAccessMixin, View):
    permission_required = 'Finance.view_chartofaccounts'
    template_name = 'finance/account_print_list.html'

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
            # Single account print view
            account = get_object_or_404(ChartOfAccounts, pk=kwargs['pk'])
            
            context.update({
                'account': account,
                'title': f'Account: {account.code}',
            })
            template_name = 'finance/account_print_detail.html'
        else:
            # List print view
            accounts = ChartOfAccounts.objects.all()
            
            context.update({
                'accounts': accounts,
                'title': 'Chart of Accounts',
            })
            template_name = 'finance/account_print_list.html'
        
        return render(request, template_name, context)

class AccountExportView(AccountAccessMixin, View):
    permission_required = 'Finance.view_chartofaccounts'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="accounts.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Code', 'Name', 'Account Type', 'Parent', 'Is Active', 'Currency'
        ])

        accounts = ChartOfAccounts.objects.all()
        
        for account in accounts:
            writer.writerow([
                account.code,
                account.name,
                account.account_type.name if account.account_type else '',
                account.parent.code if account.parent else '',
                account.is_active,
                account.currency.code if account.currency else ''
            ])

        return response

class AccountBulkDeleteView(AccountAccessMixin, View):
    permission_required = 'Finance.delete_chartofaccounts'
    template_name = 'common/bulk_delete_confirm.html'

    def get(self, request, *args, **kwargs):
        # Get the selected account IDs from the query parameters
        selected_ids = request.GET.getlist('ids')
        
        if not selected_ids:
            messages.error(request, "No accounts selected for deletion.")
            return redirect('Finance:account_list')
        
        # Get the accounts to be deleted
        accounts = ChartOfAccounts.objects.filter(id__in=selected_ids)
        
        if not accounts.exists():
            messages.error(request, "No valid accounts found for deletion.")
            return redirect('Finance:account_list')
        
        context = {
            'objects': accounts,
            'selected_ids': selected_ids,
            'title': 'Confirm Bulk Delete',
            'subtitle': f'Delete {len(selected_ids)} selected accounts',
            'model_name': 'account',
            'delete_url': reverse_lazy('Finance:account_bulk_delete'),
            'cancel_url': reverse_lazy('Finance:account_list'),
        }
        
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        try:
            ids = request.POST.getlist('ids')
            if not ids:
                messages.error(request, "No accounts selected for deletion.")
                return redirect('Finance:account_list')
            
            deleted_count = ChartOfAccounts.objects.filter(id__in=ids).delete()[0]
            
            if deleted_count > 0:
                messages.success(request, f"{deleted_count} account(s) deleted successfully.")
            else:
                messages.warning(request, "No accounts were deleted.")
                
            return redirect('Finance:account_list')
            
        except Exception as e:
            messages.error(request, f"Error deleting accounts: {str(e)}")
            return redirect('Finance:account_list')

