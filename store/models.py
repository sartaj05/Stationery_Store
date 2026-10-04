from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Example: 📚 ✏️ 📒"
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]
        permissions = [
            ("manage_catalog", "Can manage the product catalogue"),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("manage_catalog", "Can manage the product catalogue"),
            ("manage_inventory", "Can manage product inventory"),
            ("view_store_dashboard", "Can view the store operations dashboard"),
        ]

    def final_price(self):
        return self.discount_price if self.discount_price else self.price

    def stock_status(self):
        if self.stock <= 0:
            return "Out of Stock"
        if self.stock <= 5:
            return "Low Stock"
        return "Available"

    def discount_amount(self):
        if self.discount_price:
            return self.price - self.discount_price
        return 0

    def __str__(self):
        return self.name


class Order(models.Model):
    PAYMENT_CHOICES = [
        ("COD", "Cash on Delivery"),
        ("UPI", "UPI Payment"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("PACKED", "Packed"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("UNPAID", "Unpaid"),
        ("PENDING", "Payment pending verification"),
        ("PAID", "Paid / verified"),
        ("FAILED", "Failed"),
        ("PARTIALLY_REFUNDED", "Partially refunded"),
        ("REFUNDED", "Refunded"),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=15)
    address = models.TextField()

    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name_snapshot = models.CharField(max_length=200, blank=True)
    product_brand_snapshot = models.CharField(max_length=100, blank=True)
    product_category_snapshot = models.CharField(max_length=100, blank=True)
    unit_price_snapshot = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    quantity = models.PositiveIntegerField(default=1)

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default="COD"
    )
    payment_status = models.CharField(
        max_length=24,
        choices=PAYMENT_STATUS_CHOICES,
        default="UNPAID",
    )
    transaction_reference = models.CharField(max_length=120, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    refund_reference = models.CharField(max_length=120, blank=True)
    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    refunded_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    admin_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("manage_orders", "Can manage customer orders"),
        ]

    def total_price(self):
        return self.unit_price_snapshot * self.quantity

    def save(self, *args, **kwargs):
        if (
            self._state.adding
            and self.payment_method == "UPI"
            and self.payment_status == "UNPAID"
        ):
            self.payment_status = "PENDING"
        if self.product_id and (
            not self.product_name_snapshot
            or not self.product_category_snapshot
            or self.unit_price_snapshot == 0
        ):
            product = self.product
            if not self.product_name_snapshot:
                self.product_name_snapshot = product.name
            if not self.product_brand_snapshot:
                self.product_brand_snapshot = product.brand
            if not self.product_category_snapshot:
                self.product_category_snapshot = product.category.name
            if self.unit_price_snapshot == 0:
                self.unit_price_snapshot = product.final_price()
        if self.payment_status == "PAID" and self.paid_at is None:
            self.paid_at = timezone.now()
        if self.payment_status in {"PARTIALLY_REFUNDED", "REFUNDED"} and self.refunded_at is None:
            self.refunded_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.product_name_snapshot or self.product.name}"


class BulkOrderRequest(models.Model):
    STATUS_CHOICES = [
        ("NEW", "New"),
        ("CONTACTED", "Contacted"),
        ("QUOTED", "Quoted"),
        ("CONVERTED", "Converted"),
        ("CLOSED", "Closed"),
    ]

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=15)
    organisation = models.CharField(max_length=150, blank=True)
    requirement = models.TextField()

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="NEW"
    )

    admin_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("manage_bulk_requests", "Can manage bulk order requests"),
        ]

    def __str__(self):
        return f"{self.name} - {self.phone}"
