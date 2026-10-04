from django import forms
from .models import Category, Product, Order, BulkOrderRequest


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

    def clean_slug(self):
        slug = self.cleaned_data.get("slug", "").strip().lower()

        if not slug:
            raise forms.ValidationError("Slug is required.")

        return slug


class ProductForm(forms.ModelForm):
    def __init__(self, *args, include_stock=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not include_stock:
            self.fields.pop("stock", None)

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
                "class": "form-control",
                "accept": "image/*"
            }),
            "is_featured": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if image:
            max_size = 3 * 1024 * 1024

            if image.size > max_size:
                raise forms.ValidationError("Image size must be less than 3MB.")

            allowed_types = ["image/jpeg", "image/png", "image/webp"]

            if hasattr(image, "content_type") and image.content_type not in allowed_types:
                raise forms.ValidationError("Only JPG, PNG, and WEBP images are allowed.")

        return image

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        discount_price = cleaned_data.get("discount_price")

        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")

        if discount_price is not None and discount_price < 0:
            raise forms.ValidationError("Discount price cannot be negative.")

        if price is not None and discount_price is not None:
            if discount_price >= price:
                raise forms.ValidationError(
                    "Discount price must be less than original price."
                )

        return cleaned_data


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "status",
            "admin_note",
            "payment_status",
            "transaction_reference",
            "refund_reference",
            "refund_amount",
        ]

        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "payment_status": forms.Select(attrs={"class": "form-control"}),
            "transaction_reference": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "UPI / provider transaction ID",
            }),
            "refund_reference": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Refund transaction ID",
            }),
            "refund_amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),
            "admin_note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Internal note for this order"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        payment_status = cleaned_data.get("payment_status")
        transaction_reference = cleaned_data.get("transaction_reference", "").strip()
        refund_reference = cleaned_data.get("refund_reference", "").strip()
        refund_amount = cleaned_data.get("refund_amount")

        if (
            payment_status == "PAID"
            and self.instance.payment_method == "UPI"
            and not transaction_reference
        ):
            self.add_error(
                "transaction_reference",
                "Enter the UPI transaction reference before marking payment verified.",
            )

        if payment_status in {"PARTIALLY_REFUNDED", "REFUNDED"}:
            if self.instance.payment_status not in {"PAID", "PARTIALLY_REFUNDED"}:
                self.add_error(
                    "payment_status",
                    "Only a verified payment can be refunded.",
                )
            if not refund_reference:
                self.add_error("refund_reference", "Enter the refund transaction reference.")
            if refund_amount is None or refund_amount <= 0:
                self.add_error("refund_amount", "Refund amount must be greater than zero.")
            elif refund_amount > self.instance.total_price():
                self.add_error(
                    "refund_amount",
                    "Refund amount cannot be greater than the order total.",
                )
            elif payment_status == "REFUNDED" and refund_amount != self.instance.total_price():
                self.add_error(
                    "refund_amount",
                    "A full refund must match the order total. Use partial refund for a smaller amount.",
                )
            elif payment_status == "PARTIALLY_REFUNDED" and refund_amount >= self.instance.total_price():
                self.add_error(
                    "refund_amount",
                    "Use refunded when returning the full order total.",
                )

        return cleaned_data


class BulkOrderRequestForm(forms.ModelForm):
    class Meta:
        model = BulkOrderRequest
        fields = ["name", "phone", "organisation", "requirement"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your full name"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter 10 digit mobile number"
            }),
            "organisation": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "School / Office / Organisation"
            }),
            "requirement": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Example: 100 A4 notebooks, 50 blue pens..."
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()

        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain digits only.")

        if len(phone) != 10:
            raise forms.ValidationError("Enter a valid 10 digit mobile number.")

        return phone


class BulkOrderStatusForm(forms.ModelForm):
    class Meta:
        model = BulkOrderRequest
        fields = ["status", "admin_note"]

        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "admin_note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Internal follow-up note"
            }),
        }


class ProductRestockForm(forms.Form):
    add_stock = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": 1,
            "placeholder": "Enter stock quantity"
        })
    )
    reason = forms.CharField(
        max_length=255,
        min_length=5,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Reason for this stock change",
        }),
    )


class InventoryAdjustmentForm(forms.Form):
    DIRECTION_CHOICES = [
        ("ADD", "Add stock"),
        ("REMOVE", "Remove stock"),
    ]

    direction = forms.ChoiceField(choices=DIRECTION_CHOICES)
    quantity = forms.IntegerField(min_value=1)
    reason = forms.CharField(max_length=255, min_length=5)


class CartCheckoutForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your full name"
        })
    )

    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter 10 digit mobile number"
        })
    )

    address = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Enter complete delivery address"
        })
    )

    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_CHOICES,
        widget=forms.Select(attrs={
            "class": "form-control"
        })
    )

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()

        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain digits only.")

        if len(phone) != 10:
            raise forms.ValidationError("Enter a valid 10 digit mobile number.")

        return phone
