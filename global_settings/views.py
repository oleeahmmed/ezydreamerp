from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from .models import (
    Currency, PaymentTerms, CompanyInfo, Localization, Accounting,
    UserSettings, EmailSettings, TaxSettings, PaymentSettings,
    BackupSettings, GeneralSettings, Notification
)
from .forms import (
    CurrencyForm, PaymentTermsForm, CompanyInfoForm, LocalizationForm, AccountingForm,
    UserSettingsForm, EmailSettingsForm, TaxSettingsForm, PaymentSettingsForm,
    BackupSettingsForm, GeneralSettingsForm, NotificationForm
)

class BaseCrudView(View):
    model = None
    form_class = None
    template_name = 'common/premium-form.html'
    list_template_name = None
    print_template_name = 'common/print.html'
    base_list_template = 'common/base-list-modern.html'
    success_url = None
    list_url = None
    title = None
    subtitle = None
    paginate_by = 10
    search_fields = ['name']

    def dispatch(self, request, *args, **kwargs):
        self.action = kwargs.pop('action', 'list')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.action == 'list':
            return self.list(request)
        elif self.action == 'create':
            return self.create_form(request)
        elif self.action == 'detail':
            return self.detail(request, kwargs.get('pk'))
        elif self.action == 'update':
            return self.update_form(request, kwargs.get('pk'))
        elif self.action == 'delete':
            return self.delete_confirm(request, kwargs.get('pk'))
        elif self.action == 'print':
            return self.print_view(request)
        return redirect(self.list_url)

    def post(self, request, *args, **kwargs):
        if self.action == 'create':
            return self.create_object(request)
        elif self.action == 'update':
            return self.update_object(request, kwargs.get('pk'))
        elif self.action == 'delete':
            return self.delete_object(request, kwargs.get('pk'))
        return redirect(self.list_url)

    def get_search_query(self, request):
        search_query = request.GET.get('search', '')
        if not search_query:
            return None
        q_objects = Q()
        for field in self.search_fields:
            q_objects |= Q(**{f"{field}__icontains": search_query})
        return q_objects

    def list(self, request):
        objects = self.model.objects.all()
        search_query = self.get_search_query(request)
        if search_query:
            objects = objects.filter(search_query)
        objects = self.apply_filters(request, objects)
        paginator = Paginator(objects, self.paginate_by)
        page = request.GET.get('page')
        try:
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)
        context = self.get_list_context(request, objects, paginator)
        return render(request, self.list_template_name, context)

    def apply_filters(self, request, queryset):
        return queryset

    def get_list_context(self, request, objects, paginator):
        return {
            'objects': objects,
            'model_name': self.model.__name__,
            'title': f"{self.title} List",
            'create_url': f"{self.list_url}create/",
            'list_url': self.list_url,
            'print_url': f"{self.list_url}print/",
            'is_paginated': objects.has_other_pages(),
            'paginator': paginator,
            'page_obj': objects,
            'request': request,
            'base_template': self.base_list_template,
        }

    def detail(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        form = self.form_class(instance=obj)
        context = {
            'form': form,
            'object': obj,
            'model_name': self.model.__name__,
            'title': f"View {self.title}",
            'subtitle': f"Details for {self.title.lower()}",
            'update_url': f"{self.list_url}{pk}/update/",
            'delete_url': f"{self.list_url}{pk}/delete/",
            'cancel_url': self.list_url,
            'is_detail_view': True,
            'is_disabled': True,
        }
        return render(request, self.template_name, context)

    def create_form(self, request):
        form = self.form_class()
        context = {
            'form': form,
            'title': f"Create {self.title}",
            'subtitle': f"Add a new {self.title.lower()}",
            'submit_text': 'Create',
            'cancel_url': self.list_url,
        }
        return render(request, self.template_name, context)

    def create_object(self, request):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"{self.title} created successfully.")
            return redirect(self.success_url)
        context = {
            'form': form,
            'title': f"Create {self.title}",
            'subtitle': f"Add a new {self.title.lower()}",
            'submit_text': 'Create',
            'cancel_url': self.list_url,
        }
        return render(request, self.template_name, context)

    def update_form(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        form = self.form_class(instance=obj)
        context = {
            'form': form,
            'title': f"Update {self.title}",
            'subtitle': f"Modify {self.title.lower()} details",
            'submit_text': 'Update',
            'cancel_url': self.list_url,
        }
        return render(request, self.template_name, context)

    def update_object(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        form = self.form_class(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"{self.title} updated successfully.")
            return redirect(self.success_url)
        context = {
            'form': form,
            'title': f"Update {self.title}",
            'subtitle': f"Modify {self.title.lower()} details",
            'submit_text': 'Update',
            'cancel_url': self.list_url,
        }
        return render(request, self.template_name, context)

    def delete_confirm(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        context = {
            'object': obj,
            'title': f"Delete {self.title}",
            'subtitle': f"Are you sure you want to delete this {self.title.lower()}?",
            'cancel_url': self.list_url,
        }
        return render(request, 'delete_confirm.html', context)

    def delete_object(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        obj.delete()
        messages.success(request, f"{self.title} deleted successfully.")
        return redirect(self.list_url)

    def print_view(self, request):
        object_id = request.GET.get('id')
        if object_id:
            objects = self.model.objects.filter(pk=object_id)
        else:
            objects = self.model.objects.all()
        context = {
            'objects': objects,
            'model_name': self.model.__name__,
            'title': f"{self.title} Print View",
            'list_url': self.list_url,
        }
        return render(request, self.print_template_name, context)

class CurrencyCrudView(BaseCrudView):
    model = Currency
    form_class = CurrencyForm
    success_url = reverse_lazy('global_settings:currency_list')
    list_url = reverse_lazy('global_settings:currency_list')
    list_template_name = 'currency/list.html'
    print_template_name = 'currency/print.html'
    title = "Currency"
    subtitle = "Manage currency settings"
    search_fields = ['name', 'code', 'symbol']

    def apply_filters(self, request, queryset):
        exchange_rate_filter = request.GET.get('exchange_rate_filter', '')
        if exchange_rate_filter == 'high':
            queryset = queryset.order_by('-exchange_rate')
        elif exchange_rate_filter == 'low':
            queryset = queryset.order_by('exchange_rate')
        return queryset

class PaymentTermsCrudView(BaseCrudView):
    model = PaymentTerms
    form_class = PaymentTermsForm
    success_url = reverse_lazy('global_settings:payment_terms_list')
    list_url = reverse_lazy('global_settings:payment_terms_list')
    list_template_name = 'payment_terms/list.html'
    print_template_name = 'payment_terms/print.html'
    title = "Payment Terms"
    subtitle = "Manage payment terms"
    search_fields = ['name', 'description']

class CompanyInfoCrudView(BaseCrudView):
    model = CompanyInfo
    form_class = CompanyInfoForm
    success_url = reverse_lazy('global_settings:company_info_list')
    list_url = reverse_lazy('global_settings:company_info_list')
    list_template_name = 'company_info/list.html'
    print_template_name = 'company_info/print.html'
    title = "Company Information"
    subtitle = "Manage company details"
    search_fields = ['name', 'address', 'phone', 'email']

class LocalizationCrudView(BaseCrudView):
    model = Localization
    form_class = LocalizationForm
    success_url = reverse_lazy('global_settings:localization_list')
    list_url = reverse_lazy('global_settings:localization_list')
    list_template_name = 'localization/list.html'
    print_template_name = 'localization/print.html'
    title = "Localization"
    subtitle = "Manage localization settings"
    search_fields = ['language', 'timezone']

class AccountingCrudView(BaseCrudView):
    model = Accounting
    form_class = AccountingForm
    success_url = reverse_lazy('global_settings:accounting_list')
    list_url = reverse_lazy('global_settings:accounting_list')
    list_template_name = 'accounting/list.html'
    print_template_name = 'accounting/print.html'
    title = "Accounting"
    subtitle = "Manage accounting settings"
    search_fields = ['fiscal_year_start', 'tax_id']

class UserSettingsCrudView(BaseCrudView):
    model = UserSettings
    form_class = UserSettingsForm
    success_url = reverse_lazy('global_settings:user_settings_list')
    list_url = reverse_lazy('global_settings:user_settings_list')
    list_template_name = 'user_settings/list.html'
    print_template_name = 'user_settings/print.html'
    title = "User Settings"
    subtitle = "Manage user preferences"
    search_fields = ['user__username', 'theme']

class EmailSettingsCrudView(BaseCrudView):
    model = EmailSettings
    form_class = EmailSettingsForm
    success_url = reverse_lazy('global_settings:email_settings_list')
    list_url = reverse_lazy('global_settings:email_settings_list')
    list_template_name = 'email_settings/list.html'
    print_template_name = 'email_settings/print.html'
    title = "Email Settings"
    subtitle = "Manage email configuration"
    search_fields = ['smtp_server', 'smtp_port', 'email_address']

class TaxSettingsCrudView(BaseCrudView):
    model = TaxSettings
    form_class = TaxSettingsForm
    success_url = reverse_lazy('global_settings:tax_settings_list')
    list_url = reverse_lazy('global_settings:tax_settings_list')
    list_template_name = 'tax_settings/list.html'
    print_template_name = 'tax_settings/print.html'
    title = "Tax Settings"
    subtitle = "Manage tax configuration"
    search_fields = ['tax_name', 'tax_rate']

class PaymentSettingsCrudView(BaseCrudView):
    model = PaymentSettings
    form_class = PaymentSettingsForm
    success_url = reverse_lazy('global_settings:payment_settings_list')
    list_url = reverse_lazy('global_settings:payment_settings_list')
    list_template_name = 'payment_settings/list.html'
    print_template_name = 'payment_settings/print.html'
    title = "Payment Settings"
    subtitle = "Manage payment gateways and options"
    search_fields = ['gateway_name', 'api_key']

class BackupSettingsCrudView(BaseCrudView):
    model = BackupSettings
    form_class = BackupSettingsForm
    success_url = reverse_lazy('global_settings:backup_settings_list')
    list_url = reverse_lazy('global_settings:backup_settings_list')
    list_template_name = 'backup_settings/list.html'
    print_template_name = 'backup_settings/print.html'
    title = "Backup Settings"
    subtitle = "Manage backup configuration"
    search_fields = ['backup_frequency', 'storage_location']

class GeneralSettingsCrudView(BaseCrudView):
    model = GeneralSettings
    form_class = GeneralSettingsForm
    success_url = reverse_lazy('global_settings:general_settings_list')
    list_url = reverse_lazy('global_settings:general_settings_list')
    list_template_name = 'general_settings/list.html'
    print_template_name = 'general_settings/print.html'
    title = "General Settings"
    subtitle = "Manage general application settings"
    search_fields = ['site_name', 'maintenance_mode']

class NotificationCrudView(BaseCrudView):
    model = Notification
    form_class = NotificationForm
    success_url = reverse_lazy('global_settings:notification_list')
    list_url = reverse_lazy('global_settings:notification_list')
    list_template_name = 'notification/list.html'
    print_template_name = 'notification/print.html'
    title = "Notification"
    subtitle = "Manage notification settings"
    search_fields = ['title', 'message', 'notification_type']

    def apply_filters(self, request, queryset):
        notification_type = request.GET.get('notification_type', '')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        is_read = request.GET.get('is_read', '')
        if is_read:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
            
        return queryset
    
    def detail(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        
        # Mark notification as read when viewed
        if not obj.is_read:
            obj.is_read = True
            obj.save()
        
        form = self.form_class(instance=obj)
        context = {
            'form': form,
            'object': obj,
            'model_name': self.model.__name__,
            'title': f"View {self.title}",
            'subtitle': f"Details for {self.title.lower()}",
            'update_url': f"{self.list_url}{pk}/update/",
            'delete_url': f"{self.list_url}{pk}/delete/",
            'cancel_url': self.list_url,
            'is_detail_view': True,
            'is_disabled': True,
        }
        return render(request, self.template_name, context)

def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    
    # Check if the user has permission to mark this notification as read
    if notification.all_users or (notification.recipient and notification.recipient == request.user):
        notification.is_read = True
        notification.save()
    
    # Redirect back to the referring page or notification list
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
    else:
        return HttpResponseRedirect(reverse('global_settings:notification_list'))


from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse

def get_user_notifications(request):
    """
    Get unread notifications for the current user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'notifications': [], 'count': 0})
    
    # Get unread notifications for the current user or all users
    user_notifications = Notification.objects.filter(
        is_read=False,
        recipient=request.user
    ).order_by('-created_at')[:10]  # ইউজারের জন্য সর্বোচ্চ ১০টি নটিফিকেশন

    global_notifications = Notification.objects.filter(
        is_read=False, 
        all_users=True
    ).order_by('-created_at')[:10]  # সবার জন্য সর্বোচ্চ ১০টি নটিফিকেশন

    # দুইটি queryset merge করে Python লেভেলে লিমিট করুন
    notifications = list(user_notifications) + list(global_notifications)
    notifications = sorted(notifications, key=lambda x: x.created_at, reverse=True)[:10]  # সর্বশেষ ১০টি নটিফিকেশন নিন
    # Format notifications for JSON response
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_read': notification.is_read,
        })
    
    return JsonResponse({
        'notifications': notification_data,
        'count': len(notification_data)
    })        