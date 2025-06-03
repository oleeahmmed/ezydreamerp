from django.contrib.auth.models import Permission, Group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
import json
from django.http import Http404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _


from django.contrib.auth import login, authenticate,get_backends
from .forms import LoginForm, RegistrationForm

def user_permissions_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Check if the logged-in user is a superuser or has the "Can change permission" permission
    can_change_permission = request.user.is_superuser or request.user.has_perm('auth.change_permission')

    if request.method == 'POST' and can_change_permission:
        # Update user permissions
        assigned_permissions = request.POST.get('assigned_permissions')
        if assigned_permissions:
            permission_ids = json.loads(assigned_permissions)
            user.user_permissions.set(permission_ids)

        # Update user groups
        assigned_groups = request.POST.get('assigned_groups')
        if assigned_groups:
            group_ids = json.loads(assigned_groups)
            user.groups.set(group_ids)

    # Fetch permissions
    all_permissions = Permission.objects.select_related('content_type')
    user_permissions = user.user_permissions.all()
    available_permissions = all_permissions.exclude(id__in=user_permissions.values_list('id', flat=True))

    # Fetch groups
    all_groups = Group.objects.all()
    user_groups = user.groups.all()
    available_groups = all_groups.exclude(id__in=user_groups.values_list('id', flat=True))

    # Format permissions
    def format_permission(permission):
        return {
            'id': permission.id,
            'name': f"{permission.content_type.app_label} | {permission.content_type.model} | {permission.name}"
        }

    formatted_available_permissions = [format_permission(p) for p in available_permissions]
    formatted_user_permissions = [format_permission(p) for p in user_permissions]

    context = {
        'user': user,
        'available_permissions': formatted_available_permissions,
        'assigned_permissions': formatted_user_permissions,
        'available_groups': available_groups,
        'assigned_groups': user_groups,
        'can_change_permission': can_change_permission,
    }
    return render(request, 'permissions.html', context)


def group_permissions_view(request, group_id):
    try:
        # Try to get the group, if it doesn't exist, return a 404 error
        group = get_object_or_404(Group, id=group_id)
    except Http404:
        # If the group does not exist, show a message and redirect back
        messages.error(request, _("The group you are looking for does not exist."))
        return redirect('group_list')  # Replace 'group_list' with your actual group list URL name

    # Check if the logged-in user is a superuser or has the "Can change permission" permission
    can_change_permission = request.user.is_superuser or request.user.has_perm('auth.change_permission')

    if request.method == 'POST' and can_change_permission:
        # Update group permissions
        assigned_permissions = request.POST.get('assigned_permissions')
        if assigned_permissions:
            permission_ids = json.loads(assigned_permissions)
            group.permissions.set(permission_ids)

    # Fetch all permissions for display
    all_permissions = Permission.objects.select_related('content_type')
    group_permissions = group.permissions.all()

    # Filter available permissions
    available_permissions = all_permissions.exclude(id__in=group_permissions.values_list('id', flat=True))

    # Format permissions
    def format_permission(permission):
        return {
            'id': permission.id,
            'name': f"{permission.content_type.app_label} | {permission.content_type.model} | {permission.name}"
        }

    formatted_available_permissions = [format_permission(p) for p in available_permissions]
    formatted_group_permissions = [format_permission(p) for p in group_permissions]

    context = {
        'group': group,
        'available_permissions': formatted_available_permissions,
        'assigned_permissions': formatted_group_permissions,
        'can_change_permission': can_change_permission,
    }

    return render(request, 'group_permissions.html', context)

from django.urls import reverse_lazy
from django.contrib.auth.models import User, Group
from django.views.generic import ListView, CreateView, UpdateView,DeleteView
from .forms import UserForm, GroupForm  
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
# Class-based Views for User
from django.contrib.auth.models import User
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView
from django.db.models import Q

class UserListView(PermissionRequiredMixin, ListView):
    model = User
    template_name = 'user/userlist.html'
    context_object_name = 'users'
    permission_required = 'auth.view_user'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) | 
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        return queryset.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class UserCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('permission:user_list')
    permission_required = 'auth.add_user'

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, _("You do not have permission to perform this action."))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Get model name dynamically
        context['can_edit'] = self.request.user.has_perm('auth.change_user')  # Check if user has permission to change users
        return context

    def form_valid(self, form):
        """
        Process the valid form data and set the password for the new user.
        """
        user = form.save(commit=False)

        # Set the password if provided
        password = form.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        # Save the user to the database
        user.save()

        messages.success(self.request, _("User created successfully."))
        return super().form_valid(form)

class UserUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('permission:user_list')
    permission_required = 'auth.change_user'

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, _("You do not have permission to perform this action."))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Get model name dynamically
        context['can_edit'] = self.request.user.has_perm('auth.change_user')  # Check if user has permission to change users
        return context

    def form_valid(self, form):
        """
        Process the valid form data and update the user's password if provided.
        """
        user = form.save(commit=False)

        # Update the password if provided
        password = form.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        user.save()

        messages.success(self.request, _("User updated successfully."))
        return super().form_valid(form)

class UserDeleteView(PermissionRequiredMixin, SuccessMessageMixin,DeleteView):
    model = User
    template_name = 'confirm_delete.html'
    success_url =  reverse_lazy('permission:user_list') 
    success_message = _("User deleted successfully!")
    permission_required = 'auth.delete_user'  
    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, _("You do not have permission to perform this action."))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form, making it dynamic for any model.
        """
        context = super().get_context_data(**kwargs)
        
        # Dynamically get model name
        model_name = self.model._meta.verbose_name.title()
        context['model_name'] = model_name
        
        # Add the object name dynamically based on the model
        context['object_name'] = str(self.object)

        # Dynamically check if the user has permission for this action
        context['can_delete'] = self.request.user.has_perm('auth.delete_user')
        # Add dynamic cancel URL based on the model
        context['cancel_url'] = self.get_cancel_url()

        return context

    def get_cancel_url(self):
        """
        Returns the URL to redirect to when the user cancels the deletion.
        The URL depends on the model being used.
        """
        model_name = self.model._meta.model_name
        return reverse_lazy(f'permission:user_list')
# Class-based Views for Group
class GroupListView(ListView):
    model = Group
    template_name = 'group/grouplist.html'
    context_object_name = 'groups'
    paginate_by = 10 

# Group Create View
class GroupCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('permission:group_list')  # Redirect after successful creation
    permission_required = 'auth.add_group'  # Permission required for creating a group

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, _("You do not have permission to perform this action."))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Get model name dynamically
        context['can_edit'] = self.request.user.has_perm('auth.change_group')  # Check if user has permission to change groups
        return context

# Group Update View
class GroupUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('permission:group_list')  # Redirect after successful update
    permission_required = 'auth.change_group'  # Permission required for updating a group

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, _("You do not have permission to perform this action."))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Get model name dynamically
        context['can_edit'] = self.request.user.has_perm('auth.change_group')  # Check if user has permission to change groups
        return context

# Group Delete View
class GroupDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Group
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('permission:group_list')  # Redirect after successful deletion
    success_message = _("Group deleted successfully!")
    permission_required = 'auth.delete_group'  # Permission required for deleting a group

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, _("You do not have permission to perform this action."))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form, making it dynamic for any model.
        """
        context = super().get_context_data(**kwargs)
        
        # Dynamically get model name
        model_name = self.model._meta.verbose_name.title()
        context['model_name'] = model_name
        
        # Add the object name dynamically based on the model
        context['object_name'] = str(self.object)

        # Dynamically check if the user has permission for this action
        context['can_delete'] = self.request.user.has_perm('auth.delete_group')
        
        # Add dynamic cancel URL based on the model
        context['cancel_url'] = self.success_url  # Corrected: Removed parentheses

        return context

    def get_cancel_url(self):
        """
        Returns the URL to redirect to when the user cancels the deletion.
        The URL depends on the model being used.
        """
        model_name = self.model._meta.model_name
        return reverse_lazy(f'{model_name}_list')


from .forms import PermissionForm



class PermissionListView(ListView):
    model = Permission
    template_name = 'permission/permission_list.html'
    context_object_name = 'permissions'
    paginate_by = 10

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        if search_query:
            return Permission.objects.filter(name__icontains=search_query)
        return Permission.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class PermissionCreateView(PermissionRequiredMixin, CreateView):
    model = Permission
    form_class = PermissionForm 
    template_name = 'common/form.html'  
    success_url = reverse_lazy('permission:permission_list') 
    permission_required = 'auth.add_permission' 
    
    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, _("You do not have permission to perform this action."))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Get model name dynamically
        context['can_edit'] = self.request.user.has_perm('auth.add_permission')  # Check if user has permission to change users

        return context    
class PermissionUpdateView(PermissionRequiredMixin, UpdateView):
    model = Permission
    form_class = PermissionForm  # Use the custom PermissionForm instead of 'fields'
    template_name = 'common/form.html'  # Your template for the form
    success_url = reverse_lazy('permission:permission_list')  # Redirect after successful update
    permission_required = 'auth.change_permission'  # Required permission for this view

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, _("You do not have permission to perform this action."))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Pass model name to template
        context['can_edit'] = self.request.user.has_perm('auth.change_permission')  # Check if user has permission to change groups
        return context

class PermissionDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Permission
    template_name = 'confirm_delete.html'  
    success_url = reverse_lazy('permission:permission_list')  
    success_message = _("Permission deleted successfully!")
    permission_required = 'auth.delete_permission'  

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, _("You do not have permission to perform this action."))
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form, making it dynamic for any model.
        """
        context = super().get_context_data(**kwargs)
        
        # Dynamically get model name
        model_name = self.model._meta.verbose_name.title()
        context['model_name'] = model_name
        
        # Add the object name dynamically based on the model
        context['object_name'] = str(self.object)

        # Dynamically check if the user has permission for this action
        context['can_delete'] = self.request.user.has_perm('auth.delete_permission')
        
        # Add dynamic cancel URL based on the model
        context['cancel_url'] = self.success_url  # Corrected: Removed parentheses

        return context

    def get_cancel_url(self):
        """
        Returns the URL to redirect to when the user cancels the deletion.
        The URL depends on the model being used.
        """
        model_name = self.model._meta.model_name
        return reverse_lazy(f'{model_name}_list')     
    
    

def login_view(request):
    if request.user.is_authenticated:  # Redirect authenticated users
        return redirect('permission:robot_greeting')  # Change to robot greeting

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Authenticate the user
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, _("Welcome back, {}!").format(user.username))
                    return redirect('permission:robot_greeting')  # Change to robot greeting
                else:
                    messages.error(request, _("This account is inactive."))
            else:
                # Handle invalid credentials
                messages.error(request, _("Incorrect username or password."))
        else:
            # If form is invalid, show errors
            messages.error(request, _("Please correct the errors below."))
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Explicitly set the backend for the user
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user)
            messages.success(request, _("Welcome, {}! Your account has been created.").format(user.username))  # Success message
            return redirect('permission:dashboard')
        else:
            messages.error(request, _("There was an error with your registration."))  # Error message
    else:
        form = RegistrationForm()
    return render(request, 'auth/register.html', {'form': form})
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    messages.success(request, _("You have been logged out successfully."))
    return redirect('permission:login')



@login_required
def dashboard_view(request):
    return render(request, 'auth/dashboard.html')

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from .models import UserProfile
from .forms import UserProfileForm

class UserProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'common/fieldset-form.html'
    success_url = reverse_lazy('permission:view_profile')
    success_message = _("Profile updated successfully!")

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Update Profile')
        context['model_name'] = _('Profile')
        context['cancel_url'] = reverse_lazy('permission:dashboard')
        return context
    
    
from django.views.generic import DetailView

class UserProfileDetailView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = 'profile/view_profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Profile Details')
        return context

from django.views.generic import TemplateView

class RobotGreetingView(TemplateView):
    template_name = 'auth/robot_greeting.html'