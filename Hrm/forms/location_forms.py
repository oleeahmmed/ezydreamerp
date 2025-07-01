from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from ..models import Location, LocationAttendance, UserLocation

User = get_user_model()

class LocationForm(forms.ModelForm):
    # Override the fields to remove any validators that might be causing issues
    latitude = forms.DecimalField(
        max_digits=10, 
        decimal_places=8,
        required=True,
        help_text=_("Enter latitude coordinate (e.g., 23.7537064)")
    )
    
    longitude = forms.DecimalField(
        max_digits=11, 
        decimal_places=8,
        required=True,
        help_text=_("Enter longitude coordinate (e.g., 90.3797806)")
    )
    
    radius = forms.DecimalField(
        max_digits=5, 
        decimal_places=2,
        required=True,
        min_value=0.01,
        help_text=_("Enter radius in kilometers (minimum 0.01)")
    )
    
    class Meta:
        model = Location
        fields = ['name', 'address', 'latitude', 'longitude', 'radius', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'placeholder': _('Enter location name')
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'placeholder': _('Enter full address'),
                'rows': 3
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'step': 'any',  # Allow any decimal value
                'placeholder': '23.7537064',
                'readonly': False,
                'disabled': False
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'step': 'any',  # Allow any decimal value
                'placeholder': '90.3797806',
                'readonly': False,
                'disabled': False
            }),
            'radius': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'step': 'any',  # Allow any decimal value
                'min': '0.01',  # Set minimum to a small value
                'placeholder': '1.00',
                'readonly': False,
                'disabled': False
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        # Add any custom validation logic here if needed
        return cleaned_data
class LocationFilterForm(forms.Form):
    name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent',
            'placeholder': _('Search by name')
        })
    )
    
    # Use TypedChoiceField instead of BooleanField for filtering
    is_active = forms.TypedChoiceField(
        required=False,
        choices=(
            ('', _('All Status')),
            ('True', _('Active')),
            ('False', _('Inactive')),
        ),
        coerce=lambda x: x == 'True' if x in ('True', 'False') else None,
        empty_value=None,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent'
        })
    )

class LocationAttendanceForm(forms.ModelForm):
    class Meta:
        model = LocationAttendance
        fields = ['location', 'attendance_type', 'latitude', 'longitude', 'is_within_radius', 'distance']
        widgets = {
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'attendance_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'step': '0.00000001'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'step': '0.00000001'
            }),
            'distance': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]',
                'step': '0.01'
            }),
            'is_within_radius': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'
            }),
        }

class LocationAttendanceFilterForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label=_("User"),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label=_("Location"),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    attendance_type = forms.ChoiceField(
        required=False,
        label=_("Type"),
        choices=(('', _("All Types")), ('IN', _("Check-in")), ('OUT', _("Check-out"))),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    date_from = forms.DateField(
        required=False,
        label=_("From Date"),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    date_to = forms.DateField(
        required=False,
        label=_("To Date"),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    is_within_radius = forms.ChoiceField(
        required=False,
        label=_("Radius Status"),
        choices=(('', _("All Radius Status")), ('True', _("Within Radius")), ('False', _("Outside Radius"))),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )

class UserLocationForm(forms.ModelForm):
    class Meta:
        model = UserLocation
        fields = ['user', 'location', 'is_primary']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50'
            }),
        }

class UserLocationFilterForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label=_("User"),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label=_("Location"),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )
    is_primary = forms.ChoiceField(
        required=False,
        label=_("Primary Status"),
        choices=(('', _("All Status")), ('True', _("Primary")), ('False', _("Secondary"))),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]'
        })
    )