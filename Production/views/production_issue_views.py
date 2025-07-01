from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

from ..models import ProductionIssue, ProductionIssueLine, ProductionOrder, ProductionOrderComponent
from ..forms.production_issue_forms import (
    ProductionIssueForm, ProductionIssueLineFormSet, ProductionIssueFilterForm
)
from config.views import (
    GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView
)

class ProductionIssueListView(GenericFilterView):
    model = ProductionIssue
    template_name = 'production/production_issue_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = ProductionIssueFilterForm
    permission_required = 'Production.view_productionissue'
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-document_date')

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                issue_number__icontains=search_query
            ) | queryset.filter(
                production_order__order_number__icontains=search_query
            ) | queryset.filter(
                production_order__product__name__icontains=search_query
            )

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Issues'
        context['subtitle'] = 'Manage production issues'
        context['create_url'] = reverse_lazy('Production:production_issue_create')
        context['list_url'] = reverse_lazy('Production:production_issue_list')
        context['print_url'] = reverse_lazy('Production:production_issue_export')
        context['model_name'] = 'Production Issue'
        
        context['can_create'] = self.request.user.has_perm('Production.add_productionissue')
        context['can_view'] = self.request.user.has_perm('Production.view_productionissue')
        context['can_update'] = self.request.user.has_perm('Production.change_productionissue')
        context['can_delete'] = self.request.user.has_perm('Production.delete_productionissue')
        context['can_print'] = self.request.user.has_perm('Production.view_productionissue')
        context['can_export'] = self.request.user.has_perm('Production.view_productionissue')
        
        return context

class ProductionIssueCreateView(CreateView):
    model = ProductionIssue
    form_class = ProductionIssueForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Production Issue'
        context['subtitle'] = 'Create a new production issue'
        context['cancel_url'] = reverse_lazy('Production:production_issue_list')
        context['submit_text'] = 'Create Issue'
        
        # Check if we're creating from a production order
        production_order_id = self.request.GET.get('production_order')
        
        if self.request.POST:
            context['formset'] = ProductionIssueLineFormSet(self.request.POST)
        else:
            context['formset'] = ProductionIssueLineFormSet()
            
            # If we have a production order, pre-populate the form
            if production_order_id and not self.request.POST:
                try:
                    production_order = ProductionOrder.objects.get(pk=production_order_id)
                    # Pre-populate the form with production order data
                    form = context['form']
                    form.initial['production_order'] = production_order
                    form.initial['warehouse'] = production_order.warehouse
                    
                    # Pre-populate the formset with production order components
                    components = production_order.components.all()
                    if components.exists():
                        # Clear the formset and add a form for each component
                        context['formset'] = ProductionIssueLineFormSet(
                            initial=[{
                                'component': component.pk,
                                'item_code': component.item_code,
                                'item_name': component.item_name,
                                'quantity': component.planned_quantity - component.issued_quantity
                            } for component in components]
                        )
                except ProductionOrder.DoesNotExist:
                    pass
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            with transaction.atomic():
                # Save the main form
                self.object = form.save()
                
                # Save the formset
                formset.instance = self.object
                formset.save()
            
            messages.success(self.request, f'Production Issue {self.object.issue_number} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Production:production_issue_detail', kwargs={'pk': self.object.pk})

class ProductionIssueUpdateView(UpdateView):
    model = ProductionIssue
    form_class = ProductionIssueForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Production Issue'
        context['subtitle'] = f'Edit issue {self.object.issue_number}'
        context['cancel_url'] = reverse_lazy('Production:production_issue_detail', kwargs={'pk': self.object.pk})
        context['submit_text'] = 'Update Issue'
        
        if self.request.POST:
            context['formset'] = ProductionIssueLineFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = ProductionIssueLineFormSet(instance=self.object)
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            with transaction.atomic():
                # Save the main form
                self.object = form.save()
                
                # Save the formset
                formset.instance = self.object
                formset.save()
            
            messages.success(self.request, f'Production Issue {self.object.issue_number} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Production:production_issue_detail', kwargs={'pk': self.object.pk})

class ProductionIssueDetailView(DetailView):
    model = ProductionIssue
    template_name = 'common/premium-form.html'
    context_object_name = 'production_issue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Issue Details'
        context['subtitle'] = f'Issue {self.object.issue_number}'
        context['cancel_url'] = reverse_lazy('Production:production_issue_list')
        context['update_url'] = reverse_lazy('Production:production_issue_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Production:production_issue_delete', kwargs={'pk': self.object.pk})
        context['print_url'] = reverse_lazy('Production:production_issue_print', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = ProductionIssueForm(instance=self.object)
        context['formset'] = ProductionIssueLineFormSet(instance=self.object)
        
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

class ProductionIssueDeleteView(GenericDeleteView):
    model = ProductionIssue
    success_url = reverse_lazy('Production:production_issue_list')
    permission_required = 'Production.delete_productionissue'
    template_name = 'common/delete_confirm.html'

    def get_cancel_url(self):
        return reverse_lazy('Production:production_issue_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = 'Production Issue'
        return context

class ProductionIssueExportView(BaseExportView):
    model = ProductionIssue
    filename = "production_issues.csv"
    permission_required = "Production.view_productionissue"
    field_names = ["Issue Number", "Document Date", "Production Order", "Warehouse", "Status"]

class ProductionIssueBulkDeleteView(BaseBulkDeleteConfirmView):
    model = ProductionIssue
    permission_required = "Production.delete_productionissue"
    display_fields = ["issue_number", "document_date", "production_order", "status"]
    cancel_url = reverse_lazy("Production:production_issue_list")
    success_url = reverse_lazy("Production:production_issue_list")

class ProductionIssuePrintView(DetailView):
    model = ProductionIssue
    template_name = 'production/production_issue_print.html'
    context_object_name = 'production_issue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Print Production Issue'
        context['subtitle'] = f'Issue {self.object.issue_number}'
        return context
