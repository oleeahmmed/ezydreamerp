from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate


# User Form without specifying widgets in Meta
class UserForm(forms.ModelForm):
    password = forms.CharField(
            required=False,
            label='Password',
            widget=forms.PasswordInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50',
                'autocomplete': 'new-password'  # Prevents browser from auto-filling
            })
        )
    confirm_password = forms.CharField(
        required=False,
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50',
            'autocomplete': 'new-password'  # Prevents browser from auto-filling
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # CSS class to apply
        css_classes = 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'

        # Apply the CSS class to all fields dynamically
        for field in self.fields.values():
            field.widget.attrs.update({'class': css_classes})
        
        # Custom style for 'is_active' checkbox field
        self.fields['is_active'].widget.attrs.update({
            'class': 'mt-1'
        })

    # Custom validation for 'password' and 'confirm_password'
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Ensure passwords match
        if password and confirm_password and password != confirm_password:
            raise ValidationError({'confirm_password': "Passwords do not match."})

        return cleaned_data

    # Custom validation for 'username' field
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        # Only check uniqueness if it's a new user or the username is being changed
        if not self.instance.pk:  # New user (no primary key)
            if User.objects.filter(username=username).exists():
                raise ValidationError("Username already exists. Please choose a different one.")
        
        return username

    # Custom validation for 'email' field
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Only check uniqueness if it's a new user or the email is being changed
        if not self.instance.pk:  # New user (no primary key)
            if User.objects.filter(email=email).exists():
                raise ValidationError("Email is already in use. Please use a different one.")
        
        return email

    # Optional: Custom validation for 'is_active' (if needed)
    def clean_is_active(self):
        is_active = self.cleaned_data.get('is_active')
        # Only add validation if you have specific business rules
        # For example, prevent deactivating superusers:
        if self.instance.is_superuser and not is_active:
            raise ValidationError("Superusers cannot be deactivated.")
        return is_active


# Group Form without specifying widgets in Meta
class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically apply CSS classes to all fields
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'
            })



from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = ['name', 'codename', 'content_type']  # Fields you want to allow users to edit or create

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically apply CSS classes to all fields
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'
            })



class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-field', 'placeholder': ' ', 'autocomplete': 'off'}),
        label='Username'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-field', 'placeholder': ' ', 'autocomplete': 'off'}),
        label='Password'
    )

    def clean(self):
        # This method is called during validation to clean all the form fields.
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        # Custom validation: Check if the username exists in the database
        if username and not User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username not found. Please check and try again.")

        # Custom validation: Check if password is empty
        if password and len(password) < 6:
            raise forms.ValidationError("Password should be at least 6 characters long.")

        # Return the cleaned data
        return cleaned_data


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically apply CSS classes to all fields
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-[hsl(var(--border))] bg-[hsl(var(--input))] text-[hsl(var(--foreground))] shadow-sm focus:border-[hsl(var(--ring))] focus:ring focus:ring-[hsl(var(--ring))] focus:ring-opacity-50'
            })
    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'bio', 'phone_number', 'gender', 
                  'birth_date', 'address', 'position', 'department']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize user data if available
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

        # Add custom classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'profile_picture':
                field.widget.attrs['class'] = 'peer w-full px-4 py-3.5 rounded-lg border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-300 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-2 focus:ring-[hsl(var(--primary))] focus:ring-opacity-20 focus:bg-[hsl(var(--accent))] placeholder-transparent premium-input'
            field.widget.attrs['placeholder'] = field.label

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Save user data
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        return profile

    # Define fieldsets for the form
    fieldsets = [
        {
            'title': 'Personal Information',
            'icon': 'user',
            'fields': ['first_name', 'last_name', 'email', 'phone_number', 'gender', 'birth_date'],
            'description': 'Your personal contact information'
        },
        {
            'title': 'Professional Information',
            'icon': 'briefcase',
            'fields': ['position', 'department', 'bio'],
            'description': 'Your professional details and bio'
        },
        {
            'title': 'Additional Information',
            'icon': 'info',
            'fields': ['address', 'profile_picture'],
            'description': 'Additional details and profile picture'
        },
    ]