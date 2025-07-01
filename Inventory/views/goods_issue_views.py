from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied

from ..models import GoodsIssue
from ..forms import GoodsIssueForm, GoodsIssueExtraInfoForm, GoodsIssueLineFormSet

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class GoodsIssueAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class GoodsIssueListView(GoodsIssueAccessMixin, GenericFilterView):
    model = GoodsIssue
    template_name = 'inventory/goods_issue_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Inventory.view_goodsissue'
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-posting_date')
        
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                id__icontains=search_query
            ) | queryset.filter(
                remarks__icontains=search_query
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Goods Issues'
        context['subtitle'] = 'Manage inventory issues'
        context['create_url'] = reverse_lazy('Inventory:goods_issue_create')
        
        context['can_create'] = self.request.user.has_perm('Inventory.add_goodsissue')
        context['can_view'] = self.request.user.has_perm('Inventory.view_goodsissue')
        context['can_update'] = self.request.user.has_perm('Inventory.change_goodsissue')
        context['can_delete'] = self.request.user.has_perm('Inventory.delete_goodsissue')
        context['can_print'] = self.request.user.has_perm('Inventory.view_goodsissue')
        context['can_export'] = self.request.user.has_perm('Inventory.view_goodsissue')
        context['can_bulk_delete'] = self.request.user.has_perm('Inventory.delete_goodsissue')
        
        return context

class GoodsIssueCreateView(GoodsIssueAccessMixin, CreateView):
    model = GoodsIssue
    form_class = GoodsIssueForm
    template_name = 'common/formset-form.html'
    permission_required = 'Inventory.add_goodsissue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Goods Issue'
        context['subtitle'] = 'Record new inventory issue'
        context['cancel_url'] = reverse_lazy('Inventory:goods_issue_list')
        context['submit_text'] = 'Create Issue'
        
        if self.request.POST:
            context['formset'] = GoodsIssueLineFormSet(self.request.POST)
            context['extra_form'] = GoodsIssueExtraInfoForm(self.request.POST)
        else:
            context['formset'] = GoodsIssueLineFormSet()
            context['extra_form'] = GoodsIssueExtraInfoForm()
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']
        
        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                self.object = form.save()
                
                for field in extra_form.cleaned_data:
                    if hasattr(self.object, field):
                        setattr(self.object, field, extra_form.cleaned_data[field])
                self.object.save()
                
                formset.instance = self.object
                formset.save()
            
            messages.success(self.request, f'Goods Issue {self.object.pk} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Inventory:goods_issue_detail', kwargs={'pk': self.object.pk})

class GoodsIssueUpdateView(GoodsIssueAccessMixin, UpdateView):
    model = GoodsIssue
    form_class = GoodsIssueForm
    template_name = 'common/formset-form.html'
    permission_required = 'Inventory.change_goodsissue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Goods Issue'
        context['subtitle'] = f'Edit issue {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Inventory:goods_issue_list')
        context['submit_text'] = 'Update Issue'
        
        if self.request.POST:
            context['formset'] = GoodsIssueLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = GoodsIssueExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = GoodsIssueLineFormSet(instance=self.object)
            context['extra_form'] = GoodsIssueExtraInfoForm(instance=self.object)
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']
        
        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                self.object = form.save()
                
                for field in extra_form.cleaned_data:
                    if hasattr(self.object, field):
                        setattr(self.object, field, extra_form.cleaned_data[field])
                self.object.save()
                
                formset.instance = self.object
                formset.save()
            
            messages.success(self.request, f'Goods Issue {self.object.pk} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Inventory:goods_issue_detail', kwargs={'pk': self.object.pk})

class GoodsIssueDetailView(GoodsIssueAccessMixin, DetailView):
    model = GoodsIssue
    template_name = 'common/formset-form.html'  
    context_object_name = 'goods_issue'
    permission_required = 'Inventory.view_goodsissue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Goods Issue Details'
        context['subtitle'] = f'Issue {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Inventory:goods_issue_list')
        context['update_url'] = reverse_lazy('Inventory:goods_issue_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Inventory:goods_issue_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        context['form'] = GoodsIssueForm(instance=self.object)
        context['extra_form'] = GoodsIssueExtraInfoForm(instance=self.object)
        context['formset'] = GoodsIssueLineFormSet(instance=self.object)
        
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        for form_field in context['extra_form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['disabled'] = 'disabled'
        
        return context

class GoodsIssueDeleteView(GoodsIssueAccessMixin, GenericDeleteView):
    model = GoodsIssue
    success_url = reverse_lazy('Inventory:goods_issue_list')
    permission_required = 'Inventory.delete_goodsissue'

    def get_cancel_url(self):
        return reverse_lazy('Inventory:goods_issue_detail', kwargs={'pk': self.object.pk})        

class GoodsIssueExportView(GoodsIssueAccessMixin, BaseExportView):
    model = GoodsIssue
    filename = "goods_issues.csv"
    permission_required = "Inventory.view_goodsissue"
    field_names = ["Document Number", "Posting Date", "Status", "Total Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        return queryset

class GoodsIssuePrintView(GoodsIssueAccessMixin, DetailView):
    model = GoodsIssue
    template_name = 'inventory/goods_issue_print.html'
    context_object_name = 'goods_issue'
    permission_required = 'Inventory.view_goodsissue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Goods Issue'
        context['subtitle'] = f'Issue {self.object.document_number}'
        return context

class GoodsIssueBulkDeleteView(GoodsIssueAccessMixin, BaseBulkDeleteConfirmView):
    model = GoodsIssue
    permission_required = "Inventory.delete_goodsissue"
    display_fields = ["id", "posting_date", "status"]
    cancel_url = reverse_lazy("Inventory:goods_issue_list")
    success_url = reverse_lazy("Inventory:goods_issue_list")