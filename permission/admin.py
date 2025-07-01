from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin

# ডিফল্ট User এবং Group আনরেজিস্টার করুন
admin.site.unregister(User)
admin.site.unregister(Group)

# User মডেল রেজিস্টার করুন
@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm  # Unfold এর সঠিক স্টাইলিং সহ ফর্ম
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ('username', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('username', 'email')
    ordering = ('username',)

# Group মডেল রেজিস্টার করুন
@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


from django.contrib.auth.models import Permission

# Permission মডেল রেজিস্টার করুন
@admin.register(Permission)
class PermissionAdmin(ModelAdmin):
    list_display = ('name', 'codename', 'content_type')
    search_fields = ('name', 'codename')
    list_filter = ('content_type',)