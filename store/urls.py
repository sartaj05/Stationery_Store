from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("products/", views.product_list, name="product_list"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("products/<int:product_id>/order/", views.order_product, name="order_product"),

    path("order-success/", views.order_success, name="order_success"),

    path("track-order/", views.track_order, name="track_order"),

    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
]