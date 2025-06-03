from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect  
class GenericDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    A reusable delete view for any model.
    """
    template_name = 'delete_confirm.html'
    success_message = "Deleted successfully"
    login_url = '/login/'
    permission_required = ""

    def get_context_data(self, **kwargs):
        """
        Pass dynamic context to the template.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'model_name': self.model._meta.verbose_name.title(),
            'object_name': str(self.object),
            'cancel_url': self.get_cancel_url(),
            'delete_message': f"Are you sure you want to delete this {self.model._meta.verbose_name}?",
        })
        return context

    def get_cancel_url(self):
        """
        Define the cancel URL dynamically. Defaults to an empty URL.
        """
        if hasattr(self.object, "get_absolute_url"):
            return self.object.get_absolute_url()
        return ""

    def delete(self, request, *args, **kwargs):
        """
        Override delete to show a success message.
        """
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} deleted successfully.")
        return super().delete(request, *args, **kwargs)




from django.views.generic import ListView
class GenericFilterView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    A reusable filter view for any model that supports filtering using a form.
    """
    model = None  # Set this in the subclass
    template_name = None  # Set this in the subclass
    filter_form_class = None  # This should be a Django form for filtering
    permission_required = ""
    paginate_by = 10

    def get_queryset(self):
        """
        Override to filter the queryset based on the provided filter form.
        """
        queryset = super().get_queryset().order_by('-created_at')
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
        else:
            self.filter_form = None

        return queryset

    def apply_filters(self, queryset):
        """
        Override this method to apply custom filtering logic.
        """
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(document_number__icontains=filters['search'])
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        if filters.get('date_from'):
            queryset = queryset.filter(document_date__gte=filters['date_from'])
        if filters.get('date_to'):
            queryset = queryset.filter(document_date__lte=filters['date_to'])
        return queryset

    def get_context_data(self, **kwargs):
        """
        Add filter form to the context.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'filter_form': self.filter_form,
            'title': f"{self.model._meta.verbose_name_plural.title()}",
            'subtitle': f"Manage {self.model._meta.verbose_name_plural}",
        })
        return context


import csv
from django.http import HttpResponse
from django.views import View
class BaseExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Base export view to export any model's data to CSV.
    """
    model = None  # Define in subclass
    filename = "export.csv"
    permission_required = ""
    field_names = []  # Define field names manually in subclass
    queryset_filter = None  # Optional queryset filtering method

    def get_queryset(self, request):
        """
        Returns queryset, applying filtering if needed.
        """
        queryset = self.model.objects.all()
        if self.queryset_filter:
            queryset = self.queryset_filter(request, queryset)
        return queryset

    def get(self, request, *args, **kwargs):
        """
        Generates and returns CSV file.
        """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{self.filename}"'

        writer = csv.writer(response)
        writer.writerow(self.field_names)  # Write header row

        queryset = self.get_queryset(request)
        data = queryset.values_list(*[field.lower().replace(" ", "_") for field in self.field_names])

        for row in data:
            writer.writerow(row)

        return response




from django.http import JsonResponse
from django.views.generic import TemplateView




class BaseBulkDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """
    Base bulk delete view for displaying bulk delete confirmation.
    """
    model = None  # Define in subclass
    template_name = "common/bulk_delete_confirm.html"
    permission_required = ""
    display_fields = []  # Fields to display in confirmation table
    cancel_url = None  # Manually set the cancel URL in subclass
    success_url = None  # URL to redirect to after successful deletion

    def get_queryset(self, request, ids):
        """
        Returns queryset for deletion.
        """
        return self.model.objects.filter(id__in=ids)

    def get_context_data(self, **kwargs):
        """
        Add context for bulk delete confirmation template.
        """
        context = super().get_context_data(**kwargs)
        ids = self.request.GET.getlist("ids")
        context.update({
            "objects": self.get_queryset(self.request, ids),
            "model_name": self.model._meta.verbose_name_plural.title(),
            "display_fields": self.display_fields,
            "delete_url": self.request.path,
            "cancel_url": self.cancel_url if self.cancel_url else "",  # Allow manual setting
        })
        return context

class BaseBulkDeleteConfirmView(BaseBulkDeleteView, View):
    """
    Handles bulk delete action after confirmation.
    """

    def post(self, request, *args, **kwargs):
        """
        Deletes selected objects after confirmation and redirects to success URL.
        """
        try:
            ids = request.POST.getlist("ids")
            queryset = self.get_queryset(request, ids)

            deleted_count = queryset.count()
            queryset.delete()

            messages.success(request, f"{deleted_count} {self.model._meta.verbose_name_plural} deleted successfully.")

            # Redirect to success_url instead of returning JSON response
            return HttpResponseRedirect(self.success_url if self.success_url else self.cancel_url)

        except Exception as e:
            messages.error(request, f"Error deleting {self.model._meta.verbose_name_plural}: {str(e)}")
            return HttpResponseRedirect(self.cancel_url if self.cancel_url else "/")


