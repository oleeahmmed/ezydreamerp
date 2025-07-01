from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.conf import settings
import csv

from .models import (
    BusinessPartner, 
    BusinessPartnerGroup,
    FinancialInformation,
    ContactInformation,
    Address,
    ContactPerson
)
from .forms import (
    BusinessPartnerForm, 
    BusinessPartnerFilterForm,
    FinancialInformationForm,
    ContactInformationForm,
    AddressForm,
    ContactPersonForm
)

class BusinessPartnerAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Base mixin for BusinessPartner views with common settings"""
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class BusinessPartnerListView(BusinessPartnerAccessMixin, ListView):
    model = BusinessPartner
    template_name = 'business_partner_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'BusinessPartnerMasterData.view_businesspartner'

    def get_queryset(self):
        queryset = BusinessPartner.objects.only(
            'id', 'code', 'name', 'bp_type', 'active', 'group'
        )
        form = BusinessPartnerFilterForm(self.request.GET)
        
        if form.is_valid():
            # Search across multiple fields
            if search_term := form.cleaned_data.get('search'):
                queryset = queryset.filter(
                    Q(name__icontains=search_term) |
                    Q(code__icontains=search_term) |
                    Q(group__name__icontains=search_term)
                )
        
        # Apply filters
        if bp_type := form.cleaned_data.get('bp_type'):
            queryset = queryset.filter(bp_type=bp_type)
        if group := form.cleaned_data.get('group'):
            queryset = queryset.filter(group=group)
        if form.cleaned_data.get('active'):
            queryset = queryset.filter(active=True)

    # Remove problematic filter
    # if not self.request.user.is_superuser:
    #     queryset = queryset.filter(group__in=self.request.user.businesspartnergroup_set.all())

        return queryset.select_related('group')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'filter_form': BusinessPartnerFilterForm(self.request.GET),
            'title': "Business Partners",
            'subtitle': "Manage your business partners",
            'create_url': reverse_lazy('BusinessPartnerMasterData:business_partner_create'),
            'model_name': "business partner",
            'can_create': self.request.user.has_perm('BusinessPartnerMasterData.add_businesspartner'),
            'can_delete': self.request.user.has_perm('BusinessPartnerMasterData.delete_businesspartner'),
        })
        return context

class BusinessPartnerCreateView(BusinessPartnerAccessMixin, SuccessMessageMixin, CreateView):
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'common/tabs-form.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:business_partner_list')
    success_message = "Business Partner %(name)s was created successfully"
    permission_required = 'BusinessPartnerMasterData.add_businesspartner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Business Partner",
            'subtitle': "Add a new business partner to your network",
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:business_partner_list'),
        })
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class BusinessPartnerUpdateView(BusinessPartnerAccessMixin, SuccessMessageMixin, UpdateView):
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'common/tabs-form.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:business_partner_list')
    success_message = "Business Partner %(name)s was updated successfully"
    permission_required = 'BusinessPartnerMasterData.change_businesspartner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Business Partner",
            'subtitle': f"Edit details for {self.object.name}",
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:business_partner_detail', 
                                     kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

class BusinessPartnerDeleteView(BusinessPartnerAccessMixin, SuccessMessageMixin, DeleteView):
    model = BusinessPartner
    template_name = 'delete_confirm.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:business_partner_list')
    success_message = "Business Partner was deleted successfully"
    permission_required = 'BusinessPartnerMasterData.delete_businesspartner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('BusinessPartnerMasterData:business_partner_detail', 
                                           kwargs={'pk': self.object.pk})
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

class BusinessPartnerDetailView(BusinessPartnerAccessMixin, DetailView):
    model = BusinessPartner
    template_name = 'common/tabs-form.html'
    permission_required = 'BusinessPartnerMasterData.view_businesspartner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Business Partner Details",
            'subtitle': f"View details for {self.object.name}",
            'form': BusinessPartnerForm(instance=self.object),
            'readonly': True,
            'print_url': reverse_lazy('BusinessPartnerMasterData:business_partner_print_detail', 
                                    kwargs={'pk': self.object.pk}),
            'update_url': reverse_lazy('BusinessPartnerMasterData:business_partner_update', 
                                     kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('BusinessPartnerMasterData:business_partner_delete', 
                                     kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:business_partner_list'),
            'can_update': self.request.user.has_perm('BusinessPartnerMasterData.change_businesspartner'),
            'can_delete': self.request.user.has_perm('BusinessPartnerMasterData.delete_businesspartner'),
        })
        return context

class BusinessPartnerExportView(BusinessPartnerAccessMixin, View):
    permission_required = 'BusinessPartnerMasterData.view_businesspartner'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="business_partners.csv"'

        writer = csv.writer(response)
        writer.writerow(['Code', 'Name', 'Type', 'Group', 'Active'])

    # Remove problematic filter
        queryset = BusinessPartner.objects.all()
    # if not request.user.is_superuser:
    #     queryset = queryset.filter(group__in=request.user.businesspartnergroup_set.all())

        # Use values_list to efficiently retrieve only needed fields
        business_partners = queryset.select_related('group').values_list(
            'code', 'name', 'bp_type', 'group__name', 'active'
        )
        
        for bp in business_partners:
            # Convert bp_type to display value
            bp_list = list(bp)
            if bp[2] == 'C':
                bp_list[2] = 'Customer'
            elif bp[2] == 'S':
                bp_list[2] = 'Supplier'
            writer.writerow(bp_list)

        return response

class BusinessPartnerBulkDeleteView(BusinessPartnerAccessMixin, View):
    permission_required = 'BusinessPartnerMasterData.delete_businesspartner'

    def post(self, request, *args, **kwargs):
        try:
            ids = request.POST.getlist('ids')
        # Filter by user's groups if not superuser
            queryset = BusinessPartner.objects.filter(id__in=ids)
        # if not request.user.is_superuser:
        #     queryset = queryset.filter(group__in=request.user.businesspartnergroup_set.all())
        
            deleted_count = queryset.count()
            queryset.delete()
        
            messages.success(request, f"{deleted_count} business partner(s) deleted successfully.")
            return JsonResponse({'status': 'success', 'deleted_count': deleted_count})
        except Exception as e:
            messages.error(request, f"Error deleting business partners: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class BusinessPartnerPrintView(BusinessPartnerAccessMixin, View):
    permission_required = 'BusinessPartnerMasterData.view_businesspartner'
    template_name = 'business_partner_print.html'

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
        # Single partner print view - use select_related and prefetch_related
            queryset = BusinessPartner.objects.filter(pk=kwargs['pk'])
        # if not request.user.is_superuser:
        #     queryset = queryset.filter(group__in=request.user.businesspartnergroup_set.all())
        
            partner = queryset.select_related(
                'group', 
                'contact_info', 
                'financial_info',
                'currency',
                'financial_info__payment_terms'
            ).prefetch_related(
                'addresses',
                'contact_persons'
            ).first()
        
            if not partner:
                raise Http404("Business partner not found")
        
            context.update({
                'partner': partner,
                'title': f'Business Partner: {partner.name}',
            })
        else:
        # List print view - only retrieve necessary fields
            queryset = BusinessPartner.objects.only('code', 'name', 'bp_type', 'active', 'group')
        # if not request.user.is_superuser:
        #     queryset = queryset.filter(group__in=request.user.businesspartnergroup_set.all())
        
            context.update({
                'business_partners': queryset.select_related('group'),
                'title': 'Business Partners List',
            })
        
        return render(request, self.template_name, context)

# Additional views for FinancialInformation, ContactInformation, Address, ContactPerson

# FinancialInformation Views
class FinancialInformationAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Base mixin for FinancialInformation views with common settings"""
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class FinancialInformationListView(FinancialInformationAccessMixin, ListView):
    model = FinancialInformation
    template_name = 'financial_information_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'BusinessPartnerMasterData.view_financialinformation'

    def get_queryset(self):
        queryset = FinancialInformation.objects.only(
            'id', 'credit_limit', 'balance', 'business_partner', 'payment_terms'
        )
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(business_partner__name__icontains=search_term) |
                Q(business_partner__code__icontains=search_term)
            )
    
    # Remove problematic filter
    # if not self.request.user.is_superuser:
    #     queryset = queryset.filter(
    #         business_partner__group__in=self.request.user.businesspartnergroup_set.all()
    #     )

        return queryset.select_related('business_partner', 'payment_terms')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Financial Information",
            'subtitle': "Manage financial information for business partners",
            'create_url': reverse_lazy('BusinessPartnerMasterData:financial_information_create'),
            'model_name': "financial information",
            'can_create': self.request.user.has_perm('BusinessPartnerMasterData.add_financialinformation'),
            'can_delete': self.request.user.has_perm('BusinessPartnerMasterData.delete_financialinformation'),
        })
        return context

class FinancialInformationCreateView(FinancialInformationAccessMixin, SuccessMessageMixin, CreateView):
    model = FinancialInformation
    form_class = FinancialInformationForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:financial_information_list')
    success_message = "Financial Information for %(business_partner)s was created successfully"
    permission_required = 'BusinessPartnerMasterData.add_financialinformation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Financial Information",
            'subtitle': "Add financial information for a business partner",
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:financial_information_list'),
        })
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_message(self, cleaned_data):
        return self.success_message % {'business_partner': self.object.business_partner}

class FinancialInformationUpdateView(FinancialInformationAccessMixin, SuccessMessageMixin, UpdateView):
    model = FinancialInformation
    form_class = FinancialInformationForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:financial_information_list')
    success_message = "Financial Information for %(business_partner)s was updated successfully"
    permission_required = 'BusinessPartnerMasterData.change_financialinformation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Financial Information",
            'subtitle': f"Edit financial details for {self.object.business_partner.name}",
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:financial_information_detail', 
                                     kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_success_message(self, cleaned_data):
        return self.success_message % {'business_partner': self.object.business_partner}

class FinancialInformationDeleteView(FinancialInformationAccessMixin, SuccessMessageMixin, DeleteView):
    model = FinancialInformation
    template_name = 'delete_confirm.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:financial_information_list')
    success_message = "Financial Information was deleted successfully"
    permission_required = 'BusinessPartnerMasterData.delete_financialinformation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('BusinessPartnerMasterData:financial_information_detail', 
                                           kwargs={'pk': self.object.pk})
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

class FinancialInformationDetailView(FinancialInformationAccessMixin, DetailView):
    model = FinancialInformation
    template_name = 'common/premium-form.html'
    permission_required = 'BusinessPartnerMasterData.view_financialinformation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Financial Information Details",
            'subtitle': f"View financial details for {self.object.business_partner.name}",
            'form': FinancialInformationForm(instance=self.object),
            'readonly': True,
            'update_url': reverse_lazy('BusinessPartnerMasterData:financial_information_update', 
                                     kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('BusinessPartnerMasterData:financial_information_delete', 
                                     kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:financial_information_list'),
            'can_update': self.request.user.has_perm('BusinessPartnerMasterData.change_financialinformation'),
            'can_delete': self.request.user.has_perm('BusinessPartnerMasterData.delete_financialinformation'),
        })
        return context

# ContactInformation Views
class ContactInformationAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Base mixin for ContactInformation views with common settings"""
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class ContactInformationListView(ContactInformationAccessMixin, ListView):
    model = ContactInformation
    template_name = 'contact_information_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'BusinessPartnerMasterData.view_contactinformation'

    def get_queryset(self):
        queryset = ContactInformation.objects.only(
            'id', 'phone', 'mobile', 'email', 'business_partner'
        )
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(business_partner__name__icontains=search_term) |
                Q(business_partner__code__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(phone__icontains=search_term)
            )
    
    # Remove problematic filter
    # if not self.request.user.is_superuser:
    #     queryset = queryset.filter(
    #         business_partner__group__in=self.request.user.businesspartnergroup_set.all()
    #     )

        return queryset.select_related('business_partner')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Contact Information",
            'subtitle': "Manage contact information for business partners",
            'create_url': reverse_lazy('BusinessPartnerMasterData:contact_information_create'),
            'model_name': "contact information",
            'can_create': self.request.user.has_perm('BusinessPartnerMasterData.add_contactinformation'),
            'can_delete': self.request.user.has_perm('BusinessPartnerMasterData.delete_contactinformation'),
        })
        return context

class ContactInformationCreateView(ContactInformationAccessMixin, SuccessMessageMixin, CreateView):
    model = ContactInformation
    form_class = ContactInformationForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:contact_information_list')
    success_message = "Contact Information for %(business_partner)s was created successfully"
    permission_required = 'BusinessPartnerMasterData.add_contactinformation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Contact Information",
            'subtitle': "Add contact information for a business partner",
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:contact_information_list'),
        })
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_message(self, cleaned_data):
        return self.success_message % {'business_partner': self.object.business_partner}

class ContactInformationUpdateView(ContactInformationAccessMixin, SuccessMessageMixin, UpdateView):
    model = ContactInformation
    form_class = ContactInformationForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:contact_information_list')
    success_message = "Contact Information for %(business_partner)s was updated successfully"
    permission_required = 'BusinessPartnerMasterData.change_contactinformation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Contact Information",
            'subtitle': f"Edit contact details for {self.object.business_partner.name}",
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:contact_information_detail', 
                                     kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_success_message(self, cleaned_data):
        return self.success_message % {'business_partner': self.object.business_partner}

class ContactInformationDeleteView(ContactInformationAccessMixin, SuccessMessageMixin, DeleteView):
    model = ContactInformation
    template_name = 'delete_confirm.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:contact_information_list')
    success_message = "Contact Information was deleted successfully"
    permission_required = 'BusinessPartnerMasterData.delete_contactinformation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('BusinessPartnerMasterData:contact_information_detail', 
                                           kwargs={'pk': self.object.pk})
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

class ContactInformationDetailView(ContactInformationAccessMixin, DetailView):
    model = ContactInformation
    template_name = 'common/premium-form.html'
    permission_required = 'BusinessPartnerMasterData.view_contactinformation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Contact Information Details",
            'subtitle': f"View contact details for {self.object.business_partner.name}",
            'form': ContactInformationForm(instance=self.object),
            'readonly': True,
            'update_url': reverse_lazy('BusinessPartnerMasterData:contact_information_update', 
                                     kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('BusinessPartnerMasterData:contact_information_delete', 
                                     kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:contact_information_list'),
            'can_update': self.request.user.has_perm('BusinessPartnerMasterData.change_contactinformation'),
            'can_delete': self.request.user.has_perm('BusinessPartnerMasterData.delete_contactinformation'),
        })
        return context

# Address Views
class AddressAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Base mixin for Address views with common settings"""
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class AddressListView(AddressAccessMixin, ListView):
    model = Address
    template_name = 'address_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'BusinessPartnerMasterData.view_address'

    def get_queryset(self):
        queryset = Address.objects.only(
            'id', 'address_type', 'street', 'city', 'country', 'is_default', 'business_partner'
        )
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(business_partner__name__icontains=search_term) |
                Q(business_partner__code__icontains=search_term) |
                Q(street__icontains=search_term) |
                Q(city__icontains=search_term) |
                Q(country__icontains=search_term)
            )
        
        # Filter by address type if provided
        address_type = self.request.GET.get('address_type', '')
        if address_type:
            queryset = queryset.filter(address_type=address_type)
    
    # Remove problematic filter
    # if not self.request.user.is_superuser:
    #     queryset = queryset.filter(
    #         business_partner__group__in=self.request.user.businesspartnergroup_set.all()
    #     )

        return queryset.select_related('business_partner')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Addresses",
            'subtitle': "Manage addresses for business partners",
            'create_url': reverse_lazy('BusinessPartnerMasterData:address_create'),
            'model_name': "address",
            'can_create': self.request.user.has_perm('BusinessPartnerMasterData.add_address'),
            'can_delete': self.request.user.has_perm('BusinessPartnerMasterData.delete_address'),
            'address_types': dict(Address.ADDRESS_TYPES),
        })
        return context

class AddressCreateView(AddressAccessMixin, SuccessMessageMixin, CreateView):
    model = Address
    form_class = AddressForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:address_list')
    success_message = "Address for %(business_partner)s was created successfully"
    permission_required = 'BusinessPartnerMasterData.add_address'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Address",
            'subtitle': "Add an address for a business partner",
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:address_list'),
        })
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # If this is set as default, unset other defaults of the same type
        if form.instance.is_default:
            Address.objects.filter(
                business_partner=form.instance.business_partner,
                address_type=form.instance.address_type,
                is_default=True
            ).update(is_default=False)
        return super().form_valid(form)
    
    def get_success_message(self, cleaned_data):
        return self.success_message % {'business_partner': self.object.business_partner}

class AddressUpdateView(AddressAccessMixin, SuccessMessageMixin, UpdateView):
    model = Address
    form_class = AddressForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:address_list')
    success_message = "Address for %(business_partner)s was updated successfully"
    permission_required = 'BusinessPartnerMasterData.change_address'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Address",
            'subtitle': f"Edit address for {self.object.business_partner.name}",
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:address_detail', 
                                     kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        # If this is set as default, unset other defaults of the same type
        if form.instance.is_default:
            Address.objects.filter(
                business_partner=form.instance.business_partner,
                address_type=form.instance.address_type,
                is_default=True
            ).exclude(pk=form.instance.pk).update(is_default=False)
        return super().form_valid(form)
    
    def get_success_message(self, cleaned_data):
        return self.success_message % {'business_partner': self.object.business_partner}

class AddressDeleteView(AddressAccessMixin, SuccessMessageMixin, DeleteView):
    model = Address
    template_name = 'delete_confirm.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:address_list')
    success_message = "Address was deleted successfully"
    permission_required = 'BusinessPartnerMasterData.delete_address'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('BusinessPartnerMasterData:address_detail', 
                                           kwargs={'pk': self.object.pk})
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

class AddressDetailView(AddressAccessMixin, DetailView):
    model = Address
    template_name = 'common/premium-form.html'
    permission_required = 'BusinessPartnerMasterData.view_address'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Address Details",
            'subtitle': f"View address for {self.object.business_partner.name}",
            'form': AddressForm(instance=self.object),
            'readonly': True,
            'update_url': reverse_lazy('BusinessPartnerMasterData:address_update', 
                                     kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('BusinessPartnerMasterData:address_delete', 
                                     kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:address_list'),
            'can_update': self.request.user.has_perm('BusinessPartnerMasterData.change_address'),
            'can_delete': self.request.user.has_perm('BusinessPartnerMasterData.delete_address'),
        })
        return context

# ContactPerson Views
class ContactPersonAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Base mixin for ContactPerson views with common settings"""
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class ContactPersonListView(ContactPersonAccessMixin, ListView):
    model = ContactPerson
    template_name = 'contact_person_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'BusinessPartnerMasterData.view_contactperson'

    def get_queryset(self):
        queryset = ContactPerson.objects.only(
            'id', 'name', 'position', 'email', 'phone', 'is_default', 'business_partner'
        )
        
        # Filter by search term if provided
        search_term = self.request.GET.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(business_partner__name__icontains=search_term) |
                Q(business_partner__code__icontains=search_term) |
                Q(name__icontains=search_term) |
                Q(position__icontains=search_term) |
                Q(email__icontains=search_term)
            )
    
    # Remove problematic filter
    # if not self.request.user.is_superuser:
    #     queryset = queryset.filter(
    #         business_partner__group__in=self.request.user.businesspartnergroup_set.all()
    #     )

        return queryset.select_related('business_partner')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Contact Persons",
            'subtitle': "Manage contact persons for business partners",
            'create_url': reverse_lazy('BusinessPartnerMasterData:contact_person_create'),
            'model_name': "contact person",
            'can_create': self.request.user.has_perm('BusinessPartnerMasterData.add_contactperson'),
            'can_delete': self.request.user.has_perm('BusinessPartnerMasterData.delete_contactperson'),
        })
        return context

class ContactPersonCreateView(ContactPersonAccessMixin, SuccessMessageMixin, CreateView):
    model = ContactPerson
    form_class = ContactPersonForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:contact_person_list')
    success_message = "Contact Person for %(business_partner)s was created successfully"
    permission_required = 'BusinessPartnerMasterData.add_contactperson'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Contact Person",
            'subtitle': "Add a contact person for a business partner",
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:contact_person_list'),
        })
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # If this is set as default, unset other defaults
        if form.instance.is_default:
            ContactPerson.objects.filter(
                business_partner=form.instance.business_partner,
                is_default=True
            ).update(is_default=False)
        return super().form_valid(form)
    
    def get_success_message(self, cleaned_data):
        return self.success_message % {'business_partner': self.object.business_partner}

class ContactPersonUpdateView(ContactPersonAccessMixin, SuccessMessageMixin, UpdateView):
    model = ContactPerson
    form_class = ContactPersonForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:contact_person_list')
    success_message = "Contact Person for %(business_partner)s was updated successfully"
    permission_required = 'BusinessPartnerMasterData.change_contactperson'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Contact Person",
            'subtitle': f"Edit contact person for {self.object.business_partner.name}",
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:contact_person_detail', 
                                     kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        # If this is set as default, unset other defaults
        if form.instance.is_default:
            ContactPerson.objects.filter(
                business_partner=form.instance.business_partner,
                is_default=True
            ).exclude(pk=form.instance.pk).update(is_default=False)
        return super().form_valid(form)
    
    def get_success_message(self, cleaned_data):
        return self.success_message % {'business_partner': self.object.business_partner}

class ContactPersonDeleteView(ContactPersonAccessMixin, SuccessMessageMixin, DeleteView):
    model = ContactPerson
    template_name = 'delete_confirm.html'
    success_url = reverse_lazy('BusinessPartnerMasterData:contact_person_list')
    success_message = "Contact Person was deleted successfully"
    permission_required = 'BusinessPartnerMasterData.delete_contactperson'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy('BusinessPartnerMasterData:contact_person_detail', 
                                           kwargs={'pk': self.object.pk})
        return context

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

class ContactPersonDetailView(ContactPersonAccessMixin, DetailView):
    model = ContactPerson
    template_name = 'common/premium-form.html'
    permission_required = 'BusinessPartnerMasterData.view_contactperson'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Contact Person Details",
            'subtitle': f"View contact person for {self.object.business_partner.name}",
            'form': ContactPersonForm(instance=self.object),
            'readonly': True,
            'update_url': reverse_lazy('BusinessPartnerMasterData:contact_person_update', 
                                     kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('BusinessPartnerMasterData:contact_person_delete', 
                                     kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('BusinessPartnerMasterData:contact_person_list'),
            'can_update': self.request.user.has_perm('BusinessPartnerMasterData.change_contactperson'),
            'can_delete': self.request.user.has_perm('BusinessPartnerMasterData.delete_contactperson'),
        })
        return context        