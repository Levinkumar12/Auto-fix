from django import forms
from .models import Payment, Review

class PaymentForm(forms.ModelForm):
    transaction_reference = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 423456789012 (UPI Reference / UTR No.)',
            'id': 'id_transaction_reference'
        })
    )

    class Meta:
        model = Payment
        fields = ['payment_method']
        widgets = {
            'payment_method': forms.RadioSelect(attrs={'class': 'form-check-input payment-method-radio'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Share your experience with this mechanic (quality of work, timeliness, behavior)...'}),
        }

