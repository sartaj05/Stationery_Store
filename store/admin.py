from django.contrib import admin
from .models import Category, Product, Order, BulkOrderRequest


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
    list_editable = (
        "price",
        "discount_price",
        "stock",
        "is_featured",
        "is_active",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "product",
        "quantity",
        "payment_method",
        "status",
        "total_price",
        "created_at",
    )
    search_fields = ("name", "phone", "address", "product__name")
    list_filter = ("payment_method", "status", "created_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(BulkOrderRequest)
class BulkOrderRequestAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "organisation",
        "status",
        "created_at",
    )
    search_fields = ("name", "phone", "organisation", "requirement")
    list_filter = ("status", "created_at")
    readonly_fields = ("created_at", "updated_at")