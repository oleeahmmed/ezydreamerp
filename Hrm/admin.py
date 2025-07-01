
from django.contrib import admin
from .models import Notice

from django import forms
from .models import Notice    
from django_ckeditor_5.widgets import CKEditor5Widget  
class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'department', 'user', 'target_type','file']
        widgets = {
            'content': CKEditor5Widget(config_name='default'), 
        }

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', )
    form = NoticeForm  # Use the custom form