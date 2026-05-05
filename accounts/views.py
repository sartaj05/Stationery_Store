from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from store.models import Product, Category, Order


def custom_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("superadmin_dashboard")
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

        login(request, user)

        if user.is_superuser:
            return redirect("superadmin_dashboard")

        return redirect("home")

    return render(request, "accounts/login.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not full_name or not username or not password:
            messages.error(request, "All required fields are mandatory.")
            return redirect("signup")

        if password != confirm_password:
            messages.error(request, "Password and confirm password do not match.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("signup")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name
        )

        messages.success(request, "Account created successfully. Please login.")
        return redirect("login")

    return render(request, "accounts/signup.html")


def custom_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")


def is_superadmin(user):
    return user.is_authenticated and user.is_superuser


@login_required
@user_passes_test(is_superadmin)
def superadmin_dashboard(request):
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    total_categories = Category.objects.count()
    total_orders = Order.objects.count()
    latest_orders = Order.objects.select_related("product").order_by("-created_at")[:10]
    low_stock_products = Product.objects.filter(stock__lte=5).order_by("stock")[:10]

    context = {
        "total_products": total_products,
        "active_products": active_products,
        "total_categories": total_categories,
        "total_orders": total_orders,
        "latest_orders": latest_orders,
        "low_stock_products": low_stock_products,
    }

    return render(request, "accounts/superadmin_dashboard.html", context)