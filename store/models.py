from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Example: 📚 ✏️ 📒")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def final_price(self):
        return self.discount_price if self.discount_price else self.price

    def stock_status(self):
        if self.stock <= 0:
            return "Out of Stock"
        if self.stock <= 5:
            return "Low Stock"
        return "Available"

    def __str__(self):
        return self.name


class Order(models.Model):
    PAYMENT_CHOICES = [
        ("COD", "Cash on Delivery"),
        ("UPI", "UPI Payment"),
    ]

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="COD")

    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.product.final_price() * self.quantity

    def __str__(self):
        return f"{self.name} - {self.product.name}"