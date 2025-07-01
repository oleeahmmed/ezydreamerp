from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

from ..models import ProductionIssue, ProductionIssueLine, ProductionOrder, ProductionOrderComponent, InventoryTransaction
from ..forms.production_issue_forms import ProductionIssueForm, ProductionIssueLineFormSet, ProductionIssueFilterForm

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class ProductionIssueListView(GenericFilterView):
    model = ProductionIssue
    template_name = 'production/production_issue_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Production.view_productionissue'
    filter_form_class = ProductionIssueFilterForm

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-document_date')

        # Apply search filter if any
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                issue_number__icontains=search_query
            ) | queryset.filter(
                production_order__order_number__icontains=search_query
            ) | queryset.filter(
                remarks__icontains=search_query
            )
        
        # Apply production order filter if any
        production_order_id = self.request.GET.get('production_order', '')
        if production_order_id:
            queryset = queryset.filter(production_order_id=production_order_id)
            
        # Apply warehouse filter if any
        warehouse_id = self.request.GET.get('warehouse', '')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
            
        # Apply status filter if any
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
            
        # Apply date filters if any
        date_from = self.request.GET.get('date_from', '')
        if date_from:
            queryset = queryset.filter(document_date__gte=date_from)
            
        date_to = self.request.GET.get('date_to', '')
        if date_to:
            queryset = queryset.filter(document_date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Issues'
        context['subtitle'] = 'Manage production issues'
        context['create_url'] = reverse_lazy('Production:production_issue_create')
        
        context['can_create'] = self.request.user.has_perm('Production.add_productionissue')
        context['can_view'] = self.request.user.has_perm('Production.view_productionissue')
        context['can_update'] = self.request.user.has_perm('Production.change_productionissue')
        context['can_delete'] = self.request.user.has_perm('Production.delete_productionissue')
        context['can_print'] = self.request.user.has_perm('Production.view_productionissue')
        context['can_export'] = self.request.user.has_perm('Production.view_productionissue')
        context['can_bulk_delete'] = self.request.user.has_perm('Production.delete_productionissue')
        
        return context

class ProductionIssueCreateView(CreateView):
    model = ProductionIssue
    form_class = ProductionIssueForm
    template_name = 'common/formset-form.html'
    permission_required = 'Production.add_productionissue'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Production Issue'
        context['subtitle'] = 'Create a new production issue'
        context['cancel_url'] = reverse_lazy('Production:production_issue_list')
        context['submit_text'] = 'Create Issue'

        if self.request.POST:
            context['formset'] = ProductionIssueLineFormSet(self.request.POST)
        else:
            context['formset'] = ProductionIssueLineFormSet()
            
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                
                formset.instance = self.object
                formset.save()
                
                # If status is Posted, update inventory
                if self.object.status == 'Posted':
                    for line in self.object.lines.all():
                        # Get the item from the component
                        item = line.component.item
                        
                        # Create inventory transaction for the issue
                        InventoryTransaction.objects.create(
                            item_code=item.code,
                            item_name=item.name,
                            warehouse=self.object.warehouse,
                            transaction_type='ISSUE',
                            quantity=-line.quantity,  # Negative for issue
                            unit_price=line.unit_cost,
                            reference=f"PI {self.object.issue_number}",
                            transaction_date=self.object.posting_date,
                            notes=line.remarks or self.object.remarks
                        )
                        
                        # Update component issued quantity
                        component = line.component
                        component.issued_quantity += line.quantity
                        component.save()
                    
                    # Update production order status if needed
                    production_order = self.object.production_order
                    if production_order.status == 'Released':
                        production_order.status = 'In Process'
                        production_order.save()

            messages.success(self.request, f"Production Issue {self.object.issue_number} created successfully.")
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('Production:production_issue_detail', kwargs={'pk': self.object.pk})

class ProductionIssueUpdateView(UpdateView):
    model = ProductionIssue
    form_class = ProductionIssueForm
    template_name = 'common/formset-form.html'
    permission_required = 'Production.change_productionissue'
    
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
            
        # Disable editing if status is Posted
        if self.object.status == 'Posted':
            for field in context['form'].fields.values():
                field.widget.attrs['readonly'] = True
                field.disabled = True
                
            for form in context['formset'].forms:
                for field in form.fields.values():
                    field.widget.attrs['readonly'] = True
                    field.disabled = True
            
            context['form_message'] = 'This issue has been posted and cannot be edited.'
            
        return context
    
    def form_valid(self, form):
        # Don't allow updating if status is Posted
        if self.object.status == 'Posted':
            messages.error(self.request, 'This issue has been posted and cannot be edited.')
            return HttpResponseRedirect(self.get_success_url())
            
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            with transaction.atomic():
                old_status = self.object.status
                
                self.object = form.save()
                
                formset.instance = self.object
                formset.save()
                
                # If status changed to Posted, update inventory
                if old_status != 'Posted' and self.object.status == 'Posted':
                    for line in self.object.lines.all():
                        # Get the item from the component
                        item = line.component.item
                        
                        # Create inventory transaction for the issue
                        InventoryTransaction.objects.create(
                            item_code=item.code,
                            item_name=item.name,
                            warehouse=self.object.warehouse,
                            transaction_type='ISSUE',
                            quantity=-line.quantity,  # Negative for issue
                            unit_price=line.unit_cost,
                            reference=f"PI {self.object.issue_number}",
                            transaction_date=self.object.posting_date,
                            notes=line.remarks or self.object.remarks
                        )
                        
                        # Update component issued quantity
                        component = line.component
                        component.issued_quantity += line.quantity
                        component.save()
                    
                    # Update production order status if needed
                    production_order = self.object.production_order
                    if production_order.status == 'Released':
                        production_order.status = 'In Process'
                        production_order.save()
            
            messages.success(self.request, f'Production Issue {self.object.issue_number} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Production:production_issue_detail', kwargs={'pk': self.object.pk})

class ProductionIssueDetailView(DetailView):
    model = ProductionIssue
    template_name = 'production/production_issue_detail.html'
    context_object_name = 'production_issue'
    permission_required = 'Production.view_productionissue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Issue Details'
        context['subtitle'] = f'Issue {self.object.issue_number}'
        context['cancel_url'] = reverse_lazy('Production:production_issue_list')
        context['update_url'] = reverse_lazy('Production:production_issue_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Production:production_issue_delete', kwargs={'pk': self.object.pk})
        context['print_url'] = reverse_lazy('Production:production_issue_print', kwargs={'pk': self.object.pk})
        
        # Get lines
        context['lines'] = self.object.lines.all()
        
        # Get production order details
        context['production_order'] = self.object.production_order
        
        return context

class ProductionIssueDeleteView(GenericDeleteView):
    model = ProductionIssue
    success_url = reverse_lazy('Production:production_issue_list')
    permission_required = 'Production.delete_productionissue'

    def get_cancel_url(self):
        return reverse_lazy('Production:production_issue_detail', kwargs={'pk': self.object.pk})
        
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Don't allow deleting if status is Posted
        if self.object.status == 'Posted':
            messages.error(request, 'This issue has been posted and cannot be deleted.')
            return HttpResponseRedirect(self.get_cancel_url())
            
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f"Production Issue deleted successfully.")
        return HttpResponseRedirect(success_url)

class ProductionIssueExportView(BaseExportView):
    model = ProductionIssue
    filename = "production_issues.csv"
    permission_required = "Production.view_productionissue"
    field_names = ["Issue Number", "Document Date", "Production Order", "Warehouse", "Status", "Created At"]

class ProductionIssueBulkDeleteView(BaseBulkDeleteConfirmView):
    model = ProductionIssue
    permission_required = "Production.delete_productionissue"
    display_fields = ["issue_number", "document_date", "production_order", "status"]
    cancel_url = reverse_lazy("Production:production_issue_list")
    success_url = reverse_lazy("Production:production_issue_list")
    
    def post(self, request, *args, **kwargs):
        try:
            ids = request.POST.getlist("ids")
            queryset = self.get_queryset(request, ids)
            
            # Filter out Posted issues
            posted_issues = queryset.filter(status='Posted')
            if posted_issues.exists():
                messages.error(request, f"{posted_issues.count()} posted issues cannot be deleted.")
                
            # Delete only non-Posted issues
            deletable_issues = queryset.exclude(status='Posted')
            deleted_count = deletable_issues.count()
            deletable_issues.delete()
            
            messages.success(request, f"{deleted_count} production issues deleted successfully.")
            
            return HttpResponseRedirect(self.success_url)
            
        except Exception as e:
            messages.error(request, f"Error deleting production issues: {str(e)}")
            return HttpResponseRedirect(self.cancel_url)

class ProductionIssuePrintView(DetailView):
    model = ProductionIssue
    template_name = 'production/production_issue_print.html'
    context_object_name = 'production_issue'
    permission_required = 'Production.view_productionissue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Issue'
        context['subtitle'] = f'Issue {self.object.issue_number}'
        
        # Get lines
        context['lines'] = self.object.lines.all()
        
        # Get production order details
        context['production_order'] = self.object.production_order
        
        return context