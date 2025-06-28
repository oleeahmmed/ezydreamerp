from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db import transaction

from ..models import RosterAssignment, RosterDay
from ..forms import RosterAssignmentForm, RosterDayFormSet, RosterAssignmentFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class RosterAssignmentListView(GenericFilterView):
    model = RosterAssignment
    template_name = 'roster/roster_assignment_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = RosterAssignmentFilterForm
    permission_required = 'hrm.view_rosterassignment'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                employee__first_name__icontains=filters['search']
            ) | queryset.filter(
                employee__last_name__icontains=filters['search']
            ) | queryset.filter(
                employee__employee_id__icontains=filters['search']
            ) | queryset.filter(
                roster__name__icontains=filters['search']
            )
            
        if filters.get('roster'):
            queryset = queryset.filter(roster=filters['roster'])
            
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:roster_assignment_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_rosterassignment')
        context['can_view'] = self.request.user.has_perm('hrm.view_rosterassignment')
        context['can_update'] = self.request.user.has_perm('hrm.change_rosterassignment')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_rosterassignment')
        context['can_export'] = self.request.user.has_perm('hrm.view_rosterassignment')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_rosterassignment')
        
        return context

class RosterAssignmentCreateView(CreateView):
    model = RosterAssignment
    form_class = RosterAssignmentForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Roster Assignment'
        context['subtitle'] = 'Assign employee to roster'
        context['cancel_url'] = reverse_lazy('hrm:roster_assignment_list')
        
        if self.request.POST:
            context['formset'] = RosterDayFormSet(self.request.POST)
        else:
            context['formset'] = RosterDayFormSet()
            
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
            
            messages.success(self.request, f'Roster assignment for {self.object.employee.get_full_name()} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('hrm:roster_assignment_detail', kwargs={'pk': self.object.pk})

class RosterAssignmentUpdateView(UpdateView):
    model = RosterAssignment
    form_class = RosterAssignmentForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Roster Assignment'
        context['subtitle'] = f'Edit roster assignment for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:roster_assignment_detail', kwargs={'pk': self.object.pk})
        
        if self.request.POST:
            context['formset'] = RosterDayFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = RosterDayFormSet(instance=self.object)
            
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
            
            messages.success(self.request, f'Roster assignment for {self.object.employee.get_full_name()} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('hrm:roster_assignment_detail', kwargs={'pk': self.object.pk})

class RosterAssignmentDetailView(DetailView):
    model = RosterAssignment
    template_name = 'common/formset-form.html'
    context_object_name = 'roster_assignment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Roster Assignment Details'
        context['subtitle'] = f'Roster assignment for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:roster_assignment_list')
        context['update_url'] = reverse_lazy('hrm:roster_assignment_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:roster_assignment_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = RosterAssignmentForm(instance=self.object)
        context['formset'] = RosterDayFormSet(instance=self.object)
        
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

class RosterAssignmentDeleteView(GenericDeleteView):
    model = RosterAssignment
    success_url = reverse_lazy('hrm:roster_assignment_list')
    permission_required = 'hrm.delete_rosterassignment'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Roster Assignment detail view."""
        return reverse_lazy('hrm:roster_assignment_detail', kwargs={'pk': self.object.pk})

class RosterAssignmentExportView(BaseExportView):
    """Export view for Roster Assignment."""
    model = RosterAssignment
    filename = "roster_assignments.csv"
    permission_required = "hrm.view_rosterassignment"
    field_names = ["Roster", "Employee", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class RosterAssignmentBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Roster Assignments."""
    model = RosterAssignment
    permission_required = "hrm.delete_rosterassignment"
    display_fields = ["roster", "employee", "created_at"]
    cancel_url = reverse_lazy("hrm:roster_assignment_list")
    success_url = reverse_lazy("hrm:roster_assignment_list")

