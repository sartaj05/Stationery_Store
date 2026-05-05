from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["name", "phone", "address", "quantity", "payment_method"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your full name"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter mobile number"
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter Delhi delivery address"
            }),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1
            }),
            "payment_method": forms.Select(attrs={
                "class": "form-control"
            }),
        }