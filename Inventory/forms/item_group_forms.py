from django import forms
from ..models import ItemGroup
from .base_forms import CustomTextarea, BaseFilterForm

class ItemGroupForm(forms.ModelForm):
    """Form for creating and updating ItemGroup records"""
    
    code = forms.CharField(
        max_length=20,
        help_text="Unique code for the item group",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            'placeholder': 'Enter item group code'
        })
    )
    
    name = forms.CharField(
        max_length=100,
        help_text="Item group name",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
            'placeholder': 'Enter item group name'
        })
    )
    
    # description = forms.CharField(
    #     widget=CustomTextarea(attrs={
    #         'rows': 3,
    #         'placeholder': 'Enter item group description'
    #     }),
    #     required=False,
    #     help_text="Description of this item group"
    # )
    
    class Meta:
        model = ItemGroup
        fields = ['code', 'name', 'parent', ]
        widgets = {
            'parent': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-[hsl(var(--border))] text-[hsl(var(--primary))] focus:ring-[hsl(var(--ring))]'
            }),
        }
        help_texts = {
            'parent': 'Parent item group (if any)',
            'is_active': 'Whether this item group is active',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter active parent groups only
        self.fields['parent'].queryset = ItemGroup.objects.filter(is_active=True)
        
        # Exclude self from parent options when editing
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(pk=self.instance.pk)

    def clean_code(self):
        """Convert code to uppercase"""
        code = self.cleaned_data['code'].upper()
        return code

class ItemGroupFilterForm(BaseFilterForm):
    """Form for filtering ItemGroup records"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search item groups...',
        })
    )
    
    parent = forms.ModelChoiceField(
        required=False,
        queryset=ItemGroup.objects.filter(is_active=True),
        empty_label="All Groups",
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Status'),
            ('true', 'Active'),
            ('false', 'Inactive'),
        ],
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = ItemGroup.objects.filter(is_active=True).order_by('name')
    
    def clean_is_active(self):
        """Convert is_active string to boolean"""
        is_active = self.cleaned_data.get('is_active')
        if is_active == '':
            return None
        return is_active == 'true'