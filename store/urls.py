from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),

    path("products/", views.product_list, name="product_list"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("products/<int:product_id>/order/", views.order_product, name="order_product"),

    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("cart/checkout/", views.cart_checkout, name="cart_checkout"),

    path("order-success/", views.order_success, name="order_success"),
    path("track-order/", views.track_order, name="track_order"),
    path("my-orders/", views.my_orders, name="my_orders"),

    path("orders/<int:order_id>/cancel/", views.cancel_order, name="cancel_order"),
    path("orders/<int:order_id>/reorder/", views.reorder_product, name="reorder_product"),

    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
]