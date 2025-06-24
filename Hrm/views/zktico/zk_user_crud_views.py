import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from Hrm.models import ZKDevice
from Hrm.forms.zk_device_forms import ZKUserFilterForm, ZKUserForm

try:
    from zk import ZK
    ZK_AVAILABLE = True
except ImportError:
    ZK_AVAILABLE = False
    logging.warning("ZK library not available. Please install it with 'pip install pyzk'")

logger = logging.getLogger(__name__)

def _connect_to_zk_device(device: ZKDevice):
    """Establishes a connection to a ZK device."""
    if not ZK_AVAILABLE:
        logger.error("ZK library not available. Cannot connect to device.")
        return None
    try:
        conn_params = device.get_connection_params()
        password = conn_params.get('password')
        if password in [None, '']:
            conn_params['password'] = 0
        elif isinstance(password, str) and password.isdigit():
            conn_params['password'] = int(password)
        else:
            conn_params['password'] = 0
            logger.warning(f"Device {device.name} has non-numeric password. Using 0.")
        zk = ZK(**conn_params)
        conn = zk.connect()
        return conn
    except Exception as e:
        logger.error(f"Error connecting to ZK device {device.name} ({device.ip_address}): {str(e)}")
        return None

class ZKUserDeviceListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """View for listing users from ZK Devices with search and device filtering."""
    template_name = 'zk_device/device_user_list.html'
    permission_required = 'Hrm.view_zkdevice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_devices = ZKDevice.objects.all()
        users_from_devices = []
        filter_form = ZKUserFilterForm(self.request.POST if self.request.method == 'POST' else None)

        devices_to_query = []
        search_query = ''

        if filter_form.is_valid():
            selected_devices = filter_form.cleaned_data.get('device')
            search_query = filter_form.cleaned_data.get('search', '').strip()

            if selected_devices:
                devices_to_query = selected_devices
            else:
                devices_to_query = all_devices.filter(is_active=True)

        # Fetch users only on POST (when "Fetch Users" is clicked)
        if self.request.method == 'POST' and filter_form.is_valid():
            if not ZK_AVAILABLE:
                messages.error(self.request, _("ZK library not available. Cannot fetch users."))
            else:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_device = {executor.submit(self._fetch_users_from_single_device, device): device for device in devices_to_query}
                    for future in as_completed(future_to_device):
                        device = future_to_device[future]
                        try:
                            device_users_raw = future.result()
                            if device_users_raw:
                                for user in device_users_raw:
                                    user_name = user.name or f"User {user.uid}"
                                    if search_query and (search_query.lower() not in user_name.lower() and search_query not in str(user.uid)):
                                        continue
                                    users_from_devices.append({
                                        'device_id': device.id,
                                        'device_name': device.name,
                                        'uid': user.uid,
                                        'name': user_name,
                                        'privilege': user.privilege,
                                        'card': user.card,
                                        'password': user.password,
                                        'device': device,
                                    })
                        except Exception as e:
                            logger.error(f"Error fetching users from {device.name}: {str(e)}")
                            messages.error(self.request, _(f"Error fetching users from {device.name}: {str(e)}"))

        context.update({
            'objects': users_from_devices,
            'devices': all_devices,
            'search_query': search_query,
            'filter_form': filter_form,
            'title': _('ZK Device Users'),
            'subtitle': _('Manage users directly on ZKTeco devices'),
            'create_url': reverse_lazy('hrm:zk_user_add'),
            'can_create': self.request.user.has_perm('Hrm.add_zkdevice'),
            'can_view': self.request.user.has_perm('Hrm.view_zkdevice'),
            'can_update': self.request.user.has_perm('Hrm.change_zkdevice'),
            'can_delete': self.request.user.has_perm('Hrm.delete_zkdevice'),
            'zk_available': ZK_AVAILABLE,
            'model_name': _('ZK User'),
            'list_url': reverse_lazy('hrm:zk_user_list_device'),
            'print_url': '#',
        })
        return context

    def post(self, request, *args, **kwargs):
        """Handle POST request for fetching users."""
        return self.get(request, *args, **kwargs)

    def _fetch_users_from_single_device(self, device):
        """Helper to fetch users from a single device."""
        conn = None
        try:
            conn = _connect_to_zk_device(device)
            if conn:
                users = conn.get_users()

                for user in users:
                    print(f"UID: {user.uid}")
                    print(f"Name: {user.name}")
                    print(f"Card: {getattr(user, 'card', 'Not Found')}")
                    print(f"Privilege: {user.privilege}")
                    print(f"Password: {getattr(user, 'password', 'N/A')}")
                    print("-" * 40)

                return users
            else:
                messages.warning(self.request, _(f"Could not connect to {device.name}."))
                return []
        except Exception as e:
            logger.error(f"Error fetching users from {device.name}: {str(e)}")
            return []
        finally:
            if conn:
                conn.disconnect()

# --- ZK User Add View (Direct to Device) ---
class ZKUserAddView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """View for adding a user directly to ZK Devices."""
    template_name = "common/premium-form.html"
    form_class = ZKUserForm
    permission_required = "Hrm.add_zkdevice"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Add User to Device"),
                "subtitle": _(
                    "Add a new user directly to a ZKTeco device"
                ),
                "zk_available": ZK_AVAILABLE,
                "cancel_url": reverse_lazy("hrm:zk_user_list_device"),
            }
        )
        return context

    def form_valid(self, form):
        if not ZK_AVAILABLE:
            messages.error(self.request, _("ZK library not available. Please install it with 'pip install pyzk'"))
            return self.form_invalid(form)

        device = form.cleaned_data["devices"]  # Single device now
        user_id = int(form.cleaned_data["uid"])
        name = form.cleaned_data["name"]
        privilege = int(form.cleaned_data["privilege"])
        card_no = int(form.cleaned_data["card"]) if form.cleaned_data["card"] else 0
        password = form.cleaned_data["password"] or ""

        try:
            conn = _connect_to_zk_device(device)
            if conn:
                conn.set_user(
                    uid=user_id,
                    name=name,
                    privilege=privilege,
                    password=password,
                    card=card_no,
                )
                conn.disconnect()
                messages.success(
                    self.request,
                    _(
                        f"User {user_id} ({name}) added successfully to {device.name}."
                    ),
                )
            else:
                messages.error(
                    self.request,
                    _(f"Failed to connect to {device.name}. User not added."),
                )
        except Exception as e:
            messages.error(
                self.request,
                _(f"Error adding user to {device.name}: {str(e)}"),
            )
            logger.exception(f"Error adding user {user_id} to {device.name}")

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("hrm:zk_user_list_device")

# --- ZK User Update View (Direct to Device) ---
class ZKUserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """View for updating a user directly on ZK Devices."""
    template_name = "common/premium-form.html"
    form_class = ZKUserForm
    permission_required = "Hrm.change_zkdevice"

    def dispatch(self, request, *args, **kwargs):
        self.device = get_object_or_404(ZKDevice, pk=self.kwargs['device_id'])
        self.user_id_on_device = self.kwargs['user_id']
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if not ZK_AVAILABLE:
            messages.error(self.request, _("ZK library not available. Cannot fetch user data for update."))
            return initial

        user_data = self._get_user_from_device(self.device, self.user_id_on_device)
        if user_data:
            initial.update({
                'devices': self.device,  # Single device object
                'uid': user_data['uid'],
                'name': user_data['name'],
                'privilege': user_data['privilege'],
                'card': user_data['card'],
                'password': user_data['password'],
            })
        else:
            messages.error(self.request, _(f"Could not retrieve user {self.user_id_on_device} from {self.device.name}."))
        return initial

    def get_form_kwargs(self):
        """Pass the instance to the form for edit context."""
        kwargs = super().get_form_kwargs()
        if hasattr(self, 'device') and hasattr(self, 'user_id_on_device'):
            # Simulate an instance with device association
            kwargs['instance'] = type('obj', (object,), {
                'device': self.device,  # Single device
                'uid': self.user_id_on_device,
                'name': self.get_initial().get('name', ''),
                'privilege': self.get_initial().get('privilege', 0),
                'card': self.get_initial().get('card', 0),
                'password': self.get_initial().get('password', ''),
            })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": _("Update User on Device"),
                "subtitle": _(f"Edit user {self.user_id_on_device} on {self.device.name}"),
                "zk_available": ZK_AVAILABLE,
                "cancel_url": reverse_lazy("hrm:zk_user_list_device"),
                "is_update_view": True,
            }
        )
        return context

    def form_valid(self, form):
        if not ZK_AVAILABLE:
            messages.error(self.request, _("ZK library not available. Please install it with 'pip install pyzk'"))
            return self.form_invalid(form)

        device = form.cleaned_data["devices"]  # Single device now
        user_id = int(form.cleaned_data["uid"])
        name = form.cleaned_data["name"]
        privilege = int(form.cleaned_data["privilege"])
        card_no = int(form.cleaned_data["card"]) if form.cleaned_data["card"] else 0
        password = form.cleaned_data["password"] or ""

        try:
            conn = _connect_to_zk_device(device)
            if conn:
                conn.set_user(
                    uid=user_id,
                    name=name,
                    privilege=privilege,
                    password=password,
                    card=card_no,
                )
                conn.disconnect()
                messages.success(
                    self.request,
                    _(
                        f"User {user_id} ({name}) updated successfully on {device.name}."
                    ),
                )
                return HttpResponseRedirect(self.get_success_url())
            else:
                messages.error(
                    self.request,
                    _(f"Failed to connect to {device.name}. User not updated."),
                )
        except Exception as e:
            messages.error(
                self.request,
                _(f"Error updating user on {device.name}: {str(e)}"),
            )
            logger.exception(f"Error updating user {user_id} on {device.name}")

        return self.form_invalid(form)

    def _get_user_from_device(self, device, user_id):
        """Helper to fetch a single user's data from a device."""
        conn = None
        try:
            conn = _connect_to_zk_device(device)
            if conn:
                users = conn.get_users()
                for user in users:
                    if str(user.uid) == str(user_id):
                        return {
                            'uid': user.uid,
                            'name': user.name,
                            'privilege': user.privilege,
                            'card': user.card,
                            'password': user.password,
                        }
        except Exception as e:
            logger.error(f"Error fetching user {user_id} from {device.name}: {str(e)}")
        finally:
            if conn:
                conn.disconnect()
        return None

    def get_success_url(self):
        return reverse_lazy("hrm:zk_user_list_device")

# --- ZK User Detail View (Direct from Device) ---
class ZKUserDetailView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """View for displaying ZK User details directly from a device."""
    template_name = 'common/premium-form.html'
    permission_required = 'Hrm.view_zkdevice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        device_id = self.kwargs['device_id']
        user_id = self.kwargs['user_id']
        
        device = get_object_or_404(ZKDevice, pk=device_id)
        user_data = None
        
        if ZK_AVAILABLE:
            try:
                conn = _connect_to_zk_device(device)
                if conn:
                    users = conn.get_users()
                    conn.disconnect()
                    for user in users:
                        if str(user.uid) == str(user_id):
                            user_data = {
                                'uid': user.uid,
                                'name': user.name,
                                'privilege': user.privilege,
                                'card': user.card,
                                'password': user.password,
                            }
                            break
                else:
                    messages.warning(self.request, _(f"Could not connect to {device.name} to fetch user details."))
            except Exception as e:
                logger.error(f"Error fetching user {user_id} from {device.name}: {str(e)}")
                messages.error(self.request, _(f"Error fetching user {user_id} from {device.name}: {str(e)}"))
        else:
            messages.error(self.request, _("ZK library not available. Cannot fetch user details."))

        # Create a disabled form for display purposes
        form = ZKUserForm(initial={
            'devices': device,  # Single device object
            'uid': user_data['uid'] if user_data else '',
            'name': user_data['name'] if user_data else '',
            'privilege': user_data['privilege'] if user_data else '',
            'card': user_data['card'] if user_data else '',
            'password': user_data['password'] if user_data else '',
        }, instance=type('obj', (object,), {'device': device}))
        for field in form.fields.values():
            field.widget.attrs['readonly'] = 'readonly'
            field.widget.attrs['disabled'] = 'disabled'

        context.update({
            'title': _("ZK User Details"),
            'subtitle': user_data['name'] if user_data else _("User Details"),
            'cancel_url': reverse_lazy('hrm:zk_user_list_device'),
            'update_url': reverse_lazy('hrm:zk_user_update', kwargs={'device_id': device_id, 'user_id': user_id}),
            'delete_url': reverse_lazy('hrm:zk_user_delete', kwargs={'device_id': device_id, 'user_id': user_id}),
            'is_detail_view': True,
            'form': form,
            'user_data': user_data,
            'device': device,
            'zk_available': ZK_AVAILABLE,
        })
        return context

# --- ZK User Delete View (Direct from Device) ---
class ZKUserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """View for deleting a ZK User directly from a device."""
    template_name = 'zk_device/delete_confirm.html'
    permission_required = 'Hrm.delete_zkdevice'

    def dispatch(self, request, *args, **kwargs):
        self.device = get_object_or_404(ZKDevice, pk=self.kwargs['device_id'])
        self.user_id_on_device = self.kwargs['user_id']
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_data = self._get_user_from_device(self.device, self.user_id_on_device)
        user_name = user_data['name'] if user_data else self.user_id_on_device
        context.update({
            'title': _("Delete User from Device"),
            'subtitle': _(f"Are you sure you want to delete user {user_name} from {self.device.name}? This action cannot be undone."),
            'cancel_url': reverse_lazy('hrm:zk_user_detail', kwargs={'device_id': self.device.pk, 'user_id': self.user_id_on_device}),
            'action_url': reverse_lazy('hrm:zk_user_delete', kwargs={'device_id': self.device.pk, 'user_id': self.user_id_on_device}),
            'zk_available': ZK_AVAILABLE,
        })
        return context

    def post(self, request, *args, **kwargs):
        if not ZK_AVAILABLE:
            messages.error(self.request, _("ZK library not available. Cannot delete user."))
            return HttpResponseRedirect(reverse_lazy('hrm:zk_user_list_device'))

        try:
            conn = _connect_to_zk_device(self.device)
            if conn:
                conn.delete_user(uid=int(self.user_id_on_device))
                conn.disconnect()
                messages.success(self.request, _(f"User {self.user_id_on_device} deleted successfully from {self.device.name}."))
            else:
                messages.error(self.request, _(f"Failed to connect to {self.device.name}. User not deleted."))
        except Exception as e:
            messages.error(self.request, _(f"Error deleting user {self.user_id_on_device} from {self.device.name}: {str(e)}"))
            logger.exception(f"Error deleting user {self.user_id_on_device} from {self.device.name}")
        
        return HttpResponseRedirect(reverse_lazy('hrm:zk_user_list_device'))

    def _get_user_from_device(self, device, user_id):
        """Helper to fetch a single user's data from a device."""
        conn = None
        try:
            conn = _connect_to_zk_device(device)
            if conn:
                users = conn.get_users()
                for user in users:
                    if str(user.uid) == str(user_id):
                        return {
                            'uid': user.uid,
                            'name': user.name,
                            'privilege': user.privilege,
                            'card': user.card,
                            'password': user.password,
                        }
        except Exception as e:
            logger.error(f"Error fetching user {user_id} from {device.name}: {str(e)}")
        finally:
            if conn:
                conn.disconnect()
        return None