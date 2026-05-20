from django.contrib import admin
from .models import CustomerProfile


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "phone",
        "city",
        "pincode",
        "updated_at",
    )
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
        "city",
        "pincode",
    )
    list_filter = ("city", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
