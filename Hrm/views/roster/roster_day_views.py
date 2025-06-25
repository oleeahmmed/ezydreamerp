from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Q

from Hrm.models import RosterDay
from Hrm.forms import RosterDayForm, RosterDayFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class RosterDayListView(GenericFilterView):
    model = RosterDay
    template_name = 'roster/roster_day_list.html'
    context_object_name = 'objects'
    paginate_by = 20
    filter_form_class = RosterDayFilterForm
    permission_required = 'Hrm.view_rosterday'
    
    def get_queryset(self):
        """Optimize queryset with select_related"""
        return super().get_queryset().select_related(
            'roster_assignment__employee',
            'roster_assignment__roster',
            'shift'
        ).order_by('-date', 'roster_assignment__employee__first_name')
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        
        if filters.get('search'):
            queryset = queryset.filter(
                Q(roster_assignment__employee__first_name__icontains=filters['search']) |
                Q(roster_assignment__employee__last_name__icontains=filters['search']) |
                Q(roster_assignment__employee__employee_id__icontains=filters['search'])
            )
        
        if filters.get('roster_assignment'):
            queryset = queryset.filter(roster_assignment=filters['roster_assignment'])
            
        if filters.get('shift'):
            queryset = queryset.filter(shift=filters['shift'])
            
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
            
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
            
        if filters.get('employee_search'):
            queryset = queryset.filter(
                Q(roster_assignment__employee__first_name__icontains=filters['employee_search']) |
                Q(roster_assignment__employee__last_name__icontains=filters['employee_search']) |
                Q(roster_assignment__employee__employee_id__icontains=filters['employee_search'])
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:roster_day_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_rosterday')
        context['can_view'] = self.request.user.has_perm('Hrm.view_rosterday')
        context['can_update'] = self.request.user.has_perm('Hrm.change_rosterday')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_rosterday')
        context['can_export'] = self.request.user.has_perm('Hrm.view_rosterday')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_rosterday')
        
        return context

class RosterDayCreateView(CreateView):
    model = RosterDay
    form_class = RosterDayForm
    template_name = 'common/premium-form.html'
    permission_required = 'Hrm.add_rosterday'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Roster Day'
        context['subtitle'] = 'Add a new roster day assignment'
        context['cancel_url'] = reverse_lazy('hrm:roster_day_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        employee_name = self.object.roster_assignment.employee.get_full_name()
        messages.success(
            self.request, 
            f'Roster day for {employee_name} on {self.object.date} created successfully.'
        )
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:roster_day_detail', kwargs={'pk': self.object.pk})

class RosterDayUpdateView(UpdateView):
    model = RosterDay
    form_class = RosterDayForm
    template_name = 'common/premium-form.html'
    permission_required = 'Hrm.change_rosterday'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee_name = self.object.roster_assignment.employee.get_full_name()
        context['title'] = 'Update Roster Day'
        context['subtitle'] = f'Edit roster day for {employee_name} on {self.object.date}'
        context['cancel_url'] = reverse_lazy('hrm:roster_day_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        employee_name = self.object.roster_assignment.employee.get_full_name()
        messages.success(
            self.request, 
            f'Roster day for {employee_name} on {self.object.date} updated successfully.'
        )
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:roster_day_detail', kwargs={'pk': self.object.pk})

class RosterDayDetailView(DetailView):
    model = RosterDay
    template_name = 'common/premium-form.html'
    context_object_name = 'roster_day'
    permission_required = 'Hrm.view_rosterday'
    
    def get_queryset(self):
        """Optimize queryset with select_related"""
        return super().get_queryset().select_related(
            'roster_assignment__employee',
            'roster_assignment__roster',
            'shift'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee_name = self.object.roster_assignment.employee.get_full_name()
        context['title'] = 'Roster Day Details'
        context['subtitle'] = f'Roster day for {employee_name} on {self.object.date}'
        context['cancel_url'] = reverse_lazy('hrm:roster_day_list')
        context['update_url'] = reverse_lazy('hrm:roster_day_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:roster_day_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = RosterDayForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class RosterDayDeleteView(GenericDeleteView):
    model = RosterDay
    success_url = reverse_lazy('hrm:roster_day_list')
    permission_required = 'Hrm.delete_rosterday'

    def get_cancel_url(self):
        """Override cancel URL to redirect to RosterDay detail view."""
        return reverse_lazy('hrm:roster_day_detail', kwargs={'pk': self.object.pk})

class RosterDayExportView(BaseExportView):
    """Export view for RosterDay."""
    model = RosterDay
    filename = "roster_days.csv"
    permission_required = "Hrm.view_rosterday"
    field_names = [
        "Employee", "Employee ID", "Roster", "Date", "Shift", 
        "Shift Start", "Shift End", "Created At"
    ]

    def get_queryset(self):
        """Optimize queryset for export"""
        return super().get_queryset().select_related(
            'roster_assignment__employee',
            'roster_assignment__roster',
            'shift'
        ).order_by('-date', 'roster_assignment__employee__first_name')

    def get_export_data(self, obj):
        """Return data for CSV export"""
        return [
            obj.roster_assignment.employee.get_full_name(),
            obj.roster_assignment.employee.employee_id,
            obj.roster_assignment.roster.name,
            obj.date.strftime('%Y-%m-%d'),
            obj.shift.name,
            obj.shift.start_time.strftime('%H:%M'),
            obj.shift.end_time.strftime('%H:%M'),
            obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class RosterDayBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for RosterDays."""
    model = RosterDay
    permission_required = "Hrm.delete_rosterday"
    display_fields = [
        "roster_assignment__employee__get_full_name", 
        "date", 
        "shift__name"
    ]
    cancel_url = reverse_lazy("hrm:roster_day_list")
    success_url = reverse_lazy("hrm:roster_day_list")