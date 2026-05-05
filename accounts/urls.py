from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.custom_login, name="login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", views.custom_logout, name="logout"),
    path("superadmin/dashboard/", views.superadmin_dashboard, name="superadmin_dashboard"),
]