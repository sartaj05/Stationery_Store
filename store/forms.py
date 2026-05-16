from django import forms
from .models import Category, Product, Order


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

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()

        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain digits only.")

        if len(phone) != 10:
            raise forms.ValidationError("Enter a valid 10 digit mobile number.")

        return phone

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")

        if quantity is None or quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")

        return quantity


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "slug", "icon"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: Notebooks"
            }),
            "slug": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "example: notebooks"
            }),
            "icon": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Example: 📚"
            }),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "category",
            "name",
            "brand",
            "description",
            "price",
            "discount_price",
            "stock",
            "image",
            "is_featured",
            "is_active",
        ]

        widgets = {
            "category": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter product name"
            }),
            "brand": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter brand name"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Enter product description"
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "discount_price": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "stock": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0"
            }),
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
            "is_featured": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        discount_price = cleaned_data.get("discount_price")

        if price is not None and discount_price is not None:
            if discount_price >= price:
                raise forms.ValidationError(
                    "Discount price must be less than original price."
                )

        return cleaned_data


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status", "admin_note"]

        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "admin_note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Internal note for this order"
            }),
        }