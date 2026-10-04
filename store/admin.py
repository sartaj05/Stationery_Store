from django.contrib import admin
from .models import (
    Category,
    InventoryMovement,
    Order,
    OrderStatusEvent,
    Product,
    BulkOrderRequest,
)


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
        "is_featured",
        "is_active",
    )
    readonly_fields = ("stock",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "product_name_snapshot",
        "quantity",
        "payment_method",
        "payment_status",
        "status",
        "total_price",
        "created_at",
    )
    search_fields = ("name", "phone", "address", "product_name_snapshot")
    list_filter = ("payment_method", "payment_status", "status", "created_at")
    readonly_fields = (
        "product",
        "product_name_snapshot",
        "product_brand_snapshot",
        "product_category_snapshot",
        "unit_price_snapshot",
        "customer_email",
        "status",
        "payment_status",
        "transaction_reference",
        "paid_at",
        "refund_reference",
        "refund_amount",
        "refunded_at",
        "created_at",
        "updated_at",
    )


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


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "product",
        "quantity_delta",
        "reason",
        "actor",
        "order",
    )
    list_filter = ("reason", "created_at")
    search_fields = ("product__name", "note", "order__name")
    readonly_fields = (
        "product",
        "order",
        "actor",
        "reason",
        "quantity_delta",
        "note",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderStatusEvent)
class OrderStatusEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "order", "from_status", "to_status", "actor")
    list_filter = ("to_status", "created_at")
    search_fields = ("order__name", "order__phone", "note")
    readonly_fields = (
        "order",
        "from_status",
        "to_status",
        "actor",
        "note",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
