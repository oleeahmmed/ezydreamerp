from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from Hrm.models import Holiday
from Hrm.forms import HolidayForm, HolidayFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class HolidayListView(GenericFilterView):
    model = Holiday
    template_name = 'leave/holiday_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = HolidayFilterForm
    permission_required = 'Hrm.view_holiday'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                name__icontains=filters['search']
            ) | queryset.filter(
                description__icontains=filters['search']
            )
            
        if filters.get('year'):
            import datetime
            year = int(filters['year'])
            start_date = datetime.date(year, 1, 1)
            end_date = datetime.date(year, 12, 31)
            queryset = queryset.filter(date__range=[start_date, end_date])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:holiday_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_holiday')
        context['can_view'] = self.request.user.has_perm('Hrm.view_holiday')
        context['can_update'] = self.request.user.has_perm('Hrm.change_holiday')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_holiday')
        context['can_export'] = self.request.user.has_perm('Hrm.view_holiday')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_holiday')
        
        return context

class HolidayCreateView(CreateView):
    model = Holiday
    form_class = HolidayForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Holiday'
        context['subtitle'] = 'Add a new holiday to the system'
        context['cancel_url'] = reverse_lazy('hrm:holiday_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Holiday {self.object.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:holiday_detail', kwargs={'pk': self.object.pk})

class HolidayUpdateView(UpdateView):
    model = Holiday
    form_class = HolidayForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Holiday'
        context['subtitle'] = f'Edit holiday {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:holiday_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Holiday {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:holiday_detail', kwargs={'pk': self.object.pk})

class HolidayDetailView(DetailView):
    model = Holiday
    template_name = 'common/premium-form.html'
    context_object_name = 'holiday'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Holiday Details'
        context['subtitle'] = f'Holiday: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:holiday_list')
        context['update_url'] = reverse_lazy('hrm:holiday_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:holiday_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = HolidayForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class HolidayDeleteView(GenericDeleteView):
    model = Holiday
    success_url = reverse_lazy('hrm:holiday_list')
    permission_required = 'Hrm.delete_holiday'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Holiday detail view."""
        return reverse_lazy('hrm:holiday_detail', kwargs={'pk': self.object.pk})

class HolidayExportView(BaseExportView):
    """Export view for Holiday."""
    model = Holiday
    filename = "holidays.csv"
    permission_required = "Hrm.view_holiday"
    field_names = ["Name", "Date", "Description", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class HolidayBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Holidays."""
    model = Holiday
    permission_required = "Hrm.delete_holiday"
    display_fields = ["name", "date", "created_at"]
    cancel_url = reverse_lazy("hrm:holiday_list")
    success_url = reverse_lazy("hrm:holiday_list")

