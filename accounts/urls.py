from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.custom_login, name="login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", views.custom_logout, name="logout"),

    path(
        "superadmin/dashboard/",
        views.superadmin_dashboard,
        name="superadmin_dashboard"
    ),

    path(
        "superadmin/categories/",
        views.superadmin_category_list,
        name="superadmin_category_list"
    ),
    path(
        "superadmin/categories/add/",
        views.superadmin_category_create,
        name="superadmin_category_create"
    ),
    path(
        "superadmin/categories/<int:pk>/edit/",
        views.superadmin_category_update,
        name="superadmin_category_update"
    ),
    path(
        "superadmin/categories/<int:pk>/delete/",
        views.superadmin_category_delete,
        name="superadmin_category_delete"
    ),

    path(
        "superadmin/products/",
        views.superadmin_product_list,
        name="superadmin_product_list"
    ),
    path(
        "superadmin/products/add/",
        views.superadmin_product_create,
        name="superadmin_product_create"
    ),
    path(
        "superadmin/products/<int:pk>/edit/",
        views.superadmin_product_update,
        name="superadmin_product_update"
    ),
    path(
        "superadmin/products/<int:pk>/delete/",
        views.superadmin_product_delete,
        name="superadmin_product_delete"
    ),

    path(
        "superadmin/orders/",
        views.superadmin_order_list,
        name="superadmin_order_list"
    ),
    path(
        "superadmin/orders/<int:pk>/",
        views.superadmin_order_detail,
        name="superadmin_order_detail"
    ),

    path(
        "superadmin/bulk-requests/",
        views.superadmin_bulk_request_list,
        name="superadmin_bulk_request_list"
    ),
    path(
        "superadmin/bulk-requests/<int:pk>/",
        views.superadmin_bulk_request_detail,
        name="superadmin_bulk_request_detail"
    ),

    path(
        "superadmin/customers/",
        views.superadmin_customer_list,
        name="superadmin_customer_list"
    ),
    path(
        "superadmin/customers/<int:pk>/",
        views.superadmin_customer_detail,
        name="superadmin_customer_detail"
    ),
    path(
        "superadmin/customers/<int:pk>/toggle-status/",
        views.superadmin_customer_toggle_status,
        name="superadmin_customer_toggle_status"
    ),

    path(
        "superadmin/low-stock/",
        views.superadmin_low_stock_list,
        name="superadmin_low_stock_list"
    ),
    path(
        "superadmin/low-stock/<int:pk>/restock/",
        views.superadmin_product_restock,
        name="superadmin_product_restock"
    ),
    path(
        "superadmin/orders/<int:pk>/invoice/",
        views.superadmin_order_invoice,
        name="superadmin_order_invoice"
    ),
    path(
        "superadmin/export/products/",
        views.superadmin_export_products_csv,
        name="superadmin_export_products_csv"
    ),
    path(
        "superadmin/export/orders/",
        views.superadmin_export_orders_csv,
        name="superadmin_export_orders_csv"
    ),
    path(
        "superadmin/export/customers/",
        views.superadmin_export_customers_csv,
        name="superadmin_export_customers_csv"
    ),
    path(
        "superadmin/export/bulk-requests/",
        views.superadmin_export_bulk_requests_csv,
        name="superadmin_export_bulk_requests_csv"
    ),
]