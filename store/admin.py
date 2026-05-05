from django.contrib import admin
from .models import Category, Product, Order


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "brand",
        "price",
        "discount_price",
        "stock",
        "is_featured",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "is_featured", "is_active", "created_at")
    search_fields = ("name", "brand", "description")
    list_editable = ("price", "discount_price", "stock", "is_featured", "is_active")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "product",
        "quantity",
        "payment_method",
        "total_price",
        "created_at",
    )
    search_fields = ("name", "phone", "address", "product__name")
    list_filter = ("payment_method", "created_at")