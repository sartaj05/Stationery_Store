from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, DecimalField, ExpressionWrapper
from django.shortcuts import get_object_or_404, redirect, render

from store.forms import CategoryForm, ProductForm, OrderStatusForm
from store.models import Category, Order, Product


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

        if not user.is_active:
            messages.error(request, "Your account is inactive.")
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

        if email and User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
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
    pending_orders = Order.objects.filter(status="PENDING").count()
    delivered_orders = Order.objects.filter(status="DELIVERED").count()

    latest_orders = (
        Order.objects
        .select_related("product")
        .order_by("-created_at")[:10]
    )

    low_stock_products = (
        Product.objects
        .filter(stock__lte=5)
        .select_related("category")
        .order_by("stock")[:10]
    )

    context = {
        "total_products": total_products,
        "active_products": active_products,
        "total_categories": total_categories,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "latest_orders": latest_orders,
        "low_stock_products": low_stock_products,
    }

    return render(request, "accounts/superadmin_dashboard.html", context)


@login_required
@user_passes_test(is_superadmin)
def superadmin_category_list(request):
    query = request.GET.get("q", "").strip()

    categories = Category.objects.all()

    if query:
        categories = categories.filter(
            Q(name__icontains=query) |
            Q(slug__icontains=query)
        )

    paginator = Paginator(categories, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/superadmin_category_list.html", {
        "page_obj": page_obj,
        "query": query,
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Category created successfully.")
            return redirect("superadmin_category_list")
    else:
        form = CategoryForm()

    return render(request, "accounts/superadmin_category_form.html", {
        "form": form,
        "title": "Add Category",
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)

        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect("superadmin_category_list")
    else:
        form = CategoryForm(instance=category)

    return render(request, "accounts/superadmin_category_form.html", {
        "form": form,
        "title": "Edit Category",
        "category": category,
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully.")
        return redirect("superadmin_category_list")

    return render(request, "accounts/superadmin_confirm_delete.html", {
        "object": category,
        "cancel_url": "superadmin_category_list",
        "title": "Delete Category",
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_product_list(request):
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()
    stock_filter = request.GET.get("stock", "").strip()

    products = Product.objects.select_related("category").all()
    categories = Category.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(description__icontains=query)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if stock_filter == "low":
        products = products.filter(stock__lte=5)
    elif stock_filter == "out":
        products = products.filter(stock=0)
    elif stock_filter == "active":
        products = products.filter(is_active=True)
    elif stock_filter == "inactive":
        products = products.filter(is_active=False)

    paginator = Paginator(products, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/superadmin_product_list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "query": query,
        "category_slug": category_slug,
        "stock_filter": stock_filter,
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Product created successfully.")
            return redirect("superadmin_product_list")
    else:
        form = ProductForm()

    return render(request, "accounts/superadmin_product_form.html", {
        "form": form,
        "title": "Add Product",
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect("superadmin_product_list")
    else:
        form = ProductForm(instance=product)

    return render(request, "accounts/superadmin_product_form.html", {
        "form": form,
        "title": "Edit Product",
        "product": product,
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect("superadmin_product_list")

    return render(request, "accounts/superadmin_confirm_delete.html", {
        "object": product,
        "cancel_url": "superadmin_product_list",
        "title": "Delete Product",
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_order_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    orders = Order.objects.select_related("product").all()

    if query:
        orders = orders.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(product__name__icontains=query)
        )

    if status:
        orders = orders.filter(status=status)

    paginator = Paginator(orders, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "accounts/superadmin_order_list.html", {
        "page_obj": page_obj,
        "query": query,
        "status": status,
        "status_choices": Order.STATUS_CHOICES,
    })


@login_required
@user_passes_test(is_superadmin)
def superadmin_order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("product", "product__category"),
        pk=pk
    )

    if request.method == "POST":
        form = OrderStatusForm(request.POST, instance=order)

        if form.is_valid():
            form.save()
            messages.success(request, "Order updated successfully.")
            return redirect("superadmin_order_detail", pk=order.pk)
    else:
        form = OrderStatusForm(instance=order)

    return render(request, "accounts/superadmin_order_detail.html", {
        "order": order,
        "form": form,
    })