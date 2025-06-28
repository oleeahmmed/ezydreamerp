from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import Roster
from ..forms import RosterForm, RosterFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class RosterListView(GenericFilterView):
    model = Roster
    template_name = 'roster/roster_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = RosterFilterForm
    permission_required = 'hrm.view_roster'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                name__icontains=filters['search']
            ) | queryset.filter(
                description__icontains=filters['search']
            )
            
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
        context['can_create'] = self.request.user.has_perm('hrm.add_roster')
        context['can_view'] = self.request.user.has_perm('hrm.view_roster')
        context['can_update'] = self.request.user.has_perm('hrm.change_roster')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_roster')
        context['can_export'] = self.request.user.has_perm('hrm.view_roster')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_roster')
        
        return context

class RosterCreateView(CreateView):
    model = Roster
    form_class = RosterForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Roster'
        context['subtitle'] = 'Add a new roster to the system'
        context['cancel_url'] = reverse_lazy('hrm:roster_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Roster {self.object.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:roster_detail', kwargs={'pk': self.object.pk})

class RosterUpdateView(UpdateView):
    model = Roster
    form_class = RosterForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Roster'
        context['subtitle'] = f'Edit roster {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:roster_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Roster {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:roster_detail', kwargs={'pk': self.object.pk})

class RosterDetailView(DetailView):
    model = Roster
    template_name = 'common/premium-form.html'
    context_object_name = 'roster'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Roster Details'
        context['subtitle'] = f'Roster: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:roster_list')
        context['update_url'] = reverse_lazy('hrm:roster_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:roster_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = RosterForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class RosterDeleteView(GenericDeleteView):
    model = Roster
    success_url = reverse_lazy('hrm:roster_list')
    permission_required = 'hrm.delete_roster'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Roster detail view."""
        return reverse_lazy('hrm:roster_detail', kwargs={'pk': self.object.pk})

class RosterExportView(BaseExportView):
    """Export view for Roster."""
    model = Roster
    filename = "rosters.csv"
    permission_required = "hrm.view_roster"
    field_names = ["Name", "Start Date", "End Date", "Description", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class RosterBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Rosters."""
    model = Roster
    permission_required = "hrm.delete_roster"
    display_fields = ["name", "start_date", "end_date", "created_at"]
    cancel_url = reverse_lazy("hrm:roster_list")
    success_url = reverse_lazy("hrm:roster_list")

