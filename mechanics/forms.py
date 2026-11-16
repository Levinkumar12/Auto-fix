from django import forms
from .models import MechanicService
from billing.models import Invoice
from accounts.models import MechanicProfile

class WorkshopPaymentSettingsForm(forms.ModelForm):
    class Meta:
        model = MechanicProfile
        fields = ['workshop_name', 'upi_id', 'qr_code_image']
        widgets = {
            'workshop_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Garage / Workshop Name'}),
            'upi_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. garage@okhdfcbank, 9840123456@paytm'}),
            'qr_code_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class CompleteJobForm(forms.ModelForm):
    mechanic_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Diagnosis findings, repairs made, maintenance advice'})
    )
    labour_charge = forms.DecimalField(
        max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Labour charge (₹)'})
    )
    parts_charge = forms.DecimalField(
        max_digits=10, decimal_places=2, initial=0.00,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Spare parts total (₹)'})
    )
    parts_details = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List of spare parts used (e.g. Engine Oil 1L - ₹450, Air Filter - ₹200)'})
    )

    class Meta:
        model = Invoice
        fields = ['labour_charge', 'parts_charge', 'parts_details']


class ProvideEstimateForm(forms.Form):
    estimated_labour = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Estimated labour charge (₹)', 'id': 'id_estimated_labour'})
    )
    estimated_parts = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, initial=0.00,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Estimated parts cost (₹)', 'id': 'id_estimated_parts'})
    )
    estimate_notes = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Physical inspection findings, defect cause, required parts breakdown (e.g. Needs replacement of clutch plates ₹800 + labour ₹350)'})
    )


class MechanicServiceForm(forms.ModelForm):
    class Meta:
        model = MechanicService
        fields = ['service', 'custom_price', 'estimated_time', 'is_available']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'custom_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Your service price (₹)'}),
            'estimated_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 1.5 hours'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

