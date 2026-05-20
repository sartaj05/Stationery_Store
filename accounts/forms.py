from django import forms
from .models import CustomerProfile


class CustomerProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter full name"
        })
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter email address"
        })
    )

    class Meta:
        model = CustomerProfile
        fields = [
            "first_name",
            "email",
            "phone",
            "address",
            "city",
            "pincode",
            "landmark",
        ]

        widgets = {
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter 10 digit mobile number"
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "House no, street, area, colony"
            }),
            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Delhi"
            }),
            "pincode": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter pincode"
            }),
            "landmark": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nearby landmark optional"
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields["first_name"].initial = self.user.get_full_name() or self.user.first_name or self.user.username
            self.fields["email"].initial = self.user.email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()

        if phone:
            if not phone.isdigit():
                raise forms.ValidationError("Phone number must contain digits only.")

            if len(phone) != 10:
                raise forms.ValidationError("Enter a valid 10 digit mobile number.")

        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get("pincode", "").strip()

        if pincode:
            if not pincode.isdigit():
                raise forms.ValidationError("Pincode must contain digits only.")

            if len(pincode) != 6:
                raise forms.ValidationError("Enter a valid 6 digit pincode.")

        return pincode

    def save(self, commit=True):
        profile = super().save(commit=False)

        if self.user:
            full_name = self.cleaned_data.get("first_name", "").strip()
            email = self.cleaned_data.get("email", "").strip()

            name_parts = full_name.split(" ", 1)
            self.user.first_name = name_parts[0]
            self.user.last_name = name_parts[1] if len(name_parts) > 1 else ""
            self.user.email = email

            if commit:
                self.user.save(update_fields=["first_name", "last_name", "email"])

        if commit:
            profile.save()

        return profile
