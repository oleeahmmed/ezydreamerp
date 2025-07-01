from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db import transaction
from datetime import timedelta

from Hrm.models import Roster, RosterAssignment, RosterDay
from Hrm.forms import RosterForm, RosterAssignmentFormSet, RosterFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class RosterListView(GenericFilterView):
    model = Roster
    template_name = 'roster/roster_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = RosterFilterForm
    permission_required = 'Hrm.view_roster'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(name__icontains=filters['search'])
            
        if filters.get('start_date'):
            queryset = queryset.filter(start_date__gte=filters['start_date'])
            
        if filters.get('end_date'):
            queryset = queryset.filter(end_date__lte=filters['end_date'])
            
        # Status filtering
        if filters.get('status') == 'active':
            from django.utils import timezone
            today = timezone.now().date()
            queryset = queryset.filter(start_date__lte=today, end_date__gte=today)
        elif filters.get('status') == 'expired':
            from django.utils import timezone
            today = timezone.now().date()
            queryset = queryset.filter(end_date__lt=today)
        elif filters.get('status') == 'upcoming':
            from django.utils import timezone
            today = timezone.now().date()
            queryset = queryset.filter(start_date__gt=today)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:roster_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_roster')
        context['can_view'] = self.request.user.has_perm('Hrm.view_roster')
        context['can_update'] = self.request.user.has_perm('Hrm.change_roster')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_roster')
        context['can_export'] = self.request.user.has_perm('Hrm.view_roster')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_roster')
        
        return context

class RosterCreateView(CreateView):
    model = Roster
    form_class = RosterForm
    template_name = 'roster/roster_formset_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Roster'
        context['subtitle'] = 'Create roster and assign employees'
        context['cancel_url'] = reverse_lazy('hrm:roster_list')
        
        if self.request.POST:
            context['formset'] = RosterAssignmentFormSet(self.request.POST)
        else:
            context['formset'] = RosterAssignmentFormSet()
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            with transaction.atomic():
                # Save the main form (Roster)
                self.object = form.save()
                
                # Save the formset (RosterAssignments)
                formset.instance = self.object
                assignments = formset.save()
                
                # Auto-generate RosterDay entries for each assignment
                self.generate_roster_days(self.object, assignments)
            
            employee_count = len(assignments)
            messages.success(
                self.request, 
                f'Roster "{self.object.name}" created successfully with {employee_count} employees assigned.'
            )
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def generate_roster_days(self, roster, assignments):
        """Auto-generate RosterDay entries for all assignments"""
        current_date = roster.start_date
        while current_date <= roster.end_date:
            for assignment in assignments:
                RosterDay.objects.create(
                    roster_assignment=assignment,
                    date=current_date,
                    shift=assignment.shift
                )
            current_date += timedelta(days=1)
    
    def get_success_url(self):
        return reverse_lazy('hrm:roster_detail', kwargs={'pk': self.object.pk})

class RosterUpdateView(UpdateView):
    model = Roster
    form_class = RosterForm
    template_name = 'roster/roster_formset_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Roster'
        context['subtitle'] = f'Edit roster: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:roster_detail', kwargs={'pk': self.object.pk})
        
        if self.request.POST:
            context['formset'] = RosterAssignmentFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = RosterAssignmentFormSet(instance=self.object)
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            with transaction.atomic():
                # Save the main form
                self.object = form.save()
                
                # Delete existing RosterDay entries
                RosterDay.objects.filter(roster_assignment__roster=self.object).delete()
                
                # Save the formset
                formset.instance = self.object
                assignments = formset.save()
                
                # Regenerate RosterDay entries
                self.generate_roster_days(self.object, assignments)
            
            messages.success(self.request, f'Roster "{self.object.name}" updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def generate_roster_days(self, roster, assignments):
        """Auto-generate RosterDay entries for all assignments"""
        current_date = roster.start_date
        while current_date <= roster.end_date:
            for assignment in assignments:
                RosterDay.objects.create(
                    roster_assignment=assignment,
                    date=current_date,
                    shift=assignment.shift
                )
            current_date += timedelta(days=1)
    
    def get_success_url(self):
        return reverse_lazy('hrm:roster_detail', kwargs={'pk': self.object.pk})

class RosterDetailView(DetailView):
    model = Roster
    template_name = 'roster/roster_formset_form.html'
    context_object_name = 'roster'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Roster Details'
        context['subtitle'] = f'Roster: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:roster_list')
        context['update_url'] = reverse_lazy('hrm:roster_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:roster_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode
        context['form'] = RosterForm(instance=self.object)
        context['formset'] = RosterAssignmentFormSet(instance=self.object)
        
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

class RosterDeleteView(GenericDeleteView):
    model = Roster
    success_url = reverse_lazy('hrm:roster_list')
    permission_required = 'Hrm.delete_roster'

    def get_cancel_url(self):
        return reverse_lazy('hrm:roster_detail', kwargs={'pk': self.object.pk})

class RosterExportView(BaseExportView):
    """Export view for Roster."""
    model = Roster
    filename = "rosters.csv"
    permission_required = "Hrm.view_roster"
    field_names = ["Name", "Start Date", "End Date", "Description", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class RosterBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Rosters."""
    model = Roster
    permission_required = "Hrm.delete_roster"
    display_fields = ["name", "start_date", "end_date", "created_at"]
    cancel_url = reverse_lazy("hrm:roster_list")
    success_url = reverse_lazy("hrm:roster_list")