from django import forms
from accounts.models import CustomerProfile
from .models import Vehicle


class CustomerProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomerProfile
        fields = ['phone', 'address', 'city']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save(update_fields=['first_name', 'last_name', 'email'])
        return profile

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vehicle_type', 'vehicle_name', 'vehicle_number', 'model_year', 'color', 'fuel_type']
        widgets = {
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'vehicle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Honda Activa 6G / Hyundai i20'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. TN 23 AB 1234'}),
            'model_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Pearl White'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
        }

