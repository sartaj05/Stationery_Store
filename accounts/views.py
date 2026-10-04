from django.contrib import messages
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
import csv

from django.http import HttpResponse
from .roles import STORE_STAFF_PERMISSIONS
from store.forms import (
    CategoryForm,
    ProductForm,
    OrderStatusForm,
    ProductRestockForm,
    InventoryAdjustmentForm,
    DeliveryZoneForm,
    BulkOrderStatusForm,
    BulkQuoteLineFormSet,
)
from store.models import (
    Category,
    DeliveryZone,
    InventoryMovement,
    Order,
    Product,
    BulkOrderRequest,
)
from store.services import (
    change_stock,
    record_order_status_change,
    send_bulk_quote_email,
)


# ===============================
# AUTH VIEWS
# ===============================

def has_store_staff_access(user):
    return user.is_authenticated and (
        user.is_superuser
        or any(user.has_perm(permission) for permission in STORE_STAFF_PERMISSIONS)
    )


def store_permission_required(*permissions):
    def permission_check(user):
        return user.is_authenticated and (
            user.is_superuser
            or any(user.has_perm(permission) for permission in permissions)
        )

    return user_passes_test(permission_check)


def _store_landing_url(user):
    if user.is_superuser or user.has_perm("store.view_store_dashboard"):
        return "superadmin_dashboard"
    if user.has_perm("store.manage_catalog"):
        return "superadmin_product_list"
    if user.has_perm("store.manage_inventory"):
        return "superadmin_low_stock_list"
    if user.has_perm("store.manage_orders"):
        return "superadmin_order_list"
    if user.has_perm("store.manage_bulk_requests"):
        return "superadmin_bulk_request_list"
    if user.has_perm("accounts.view_store_customers"):
        return "superadmin_customer_list"
    return "home"


@login_required
@user_passes_test(has_store_staff_access)
def store_staff_home(request):
    return redirect(_store_landing_url(request.user))

def custom_login(request):
    if request.user.is_authenticated:
        return redirect(_store_landing_url(request.user))

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

        return redirect(_store_landing_url(user))

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

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name,
        )

        messages.success(request, "Account created successfully. Please login.")
        return redirect("login")

    return render(request, "accounts/signup.html")


def custom_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")


# ===============================
# SUPERADMIN DASHBOARD
# ===============================

@login_required
@store_permission_required("store.view_store_dashboard")
def superadmin_dashboard(request):
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    total_categories = Category.objects.count()

    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status="PENDING").count()
    confirmed_orders = Order.objects.filter(status="CONFIRMED").count()
    packed_orders = Order.objects.filter(status="PACKED").count()
    out_for_delivery_orders = Order.objects.filter(status="OUT_FOR_DELIVERY").count()
    delivered_orders = Order.objects.filter(status="DELIVERED").count()
    cancelled_orders = Order.objects.filter(status="CANCELLED").count()

    total_customers = User.objects.filter(is_superuser=False).count()
    active_customers = User.objects.filter(
        is_superuser=False,
        is_active=True,
    ).count()

    low_stock_count = Product.objects.filter(stock__lte=5).count()
    out_of_stock_count = Product.objects.filter(stock=0).count()

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

    revenue_orders = (
        Order.objects
        .select_related("product")
        .exclude(status="CANCELLED")
    )

    estimated_revenue = 0
    for order in revenue_orders:
        estimated_revenue += order.total_price()

    delivered_revenue_orders = (
        Order.objects
        .select_related("product")
        .filter(status="DELIVERED")
    )

    delivered_revenue = 0
    for order in delivered_revenue_orders:
        delivered_revenue += order.total_price()

    cod_orders = Order.objects.filter(payment_method="COD").count()
    upi_orders = Order.objects.filter(payment_method="UPI").count()

    if total_orders > 0:
        pending_percent = round((pending_orders / total_orders) * 100)
        confirmed_percent = round((confirmed_orders / total_orders) * 100)
        packed_percent = round((packed_orders / total_orders) * 100)
        out_for_delivery_percent = round((out_for_delivery_orders / total_orders) * 100)
        delivered_percent = round((delivered_orders / total_orders) * 100)
        cancelled_percent = round((cancelled_orders / total_orders) * 100)
        cod_percent = round((cod_orders / total_orders) * 100)
        upi_percent = round((upi_orders / total_orders) * 100)
    else:
        pending_percent = 0
        confirmed_percent = 0
        packed_percent = 0
        out_for_delivery_percent = 0
        delivered_percent = 0
        cancelled_percent = 0
        cod_percent = 0
        upi_percent = 0

    top_products_raw = (
        Order.objects
        .values("product__id", "product__name")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-total_quantity")[:5]
    )

    top_products = []
    max_top_quantity = 1

    for item in top_products_raw:
        quantity = item["total_quantity"] or 0

        if quantity > max_top_quantity:
            max_top_quantity = quantity

    for item in top_products_raw:
        quantity = item["total_quantity"] or 0

        top_products.append({
            "id": item["product__id"],
            "name": item["product__name"],
            "count": quantity,
            "percent": round((quantity / max_top_quantity) * 100) if max_top_quantity else 0,
        })

    today = timezone.now().date()
    monthly_orders = []

    for month_back in range(5, -1, -1):
        month_date = today.replace(day=1)

        year = month_date.year
        month = month_date.month - month_back

        while month <= 0:
            month += 12
            year -= 1

        month_count = Order.objects.filter(
            created_at__year=year,
            created_at__month=month,
        ).count()

        monthly_orders.append({
            "label": f"{month:02d}/{str(year)[-2:]}",
            "count": month_count,
        })

    max_month_count = max([item["count"] for item in monthly_orders], default=1)

    if max_month_count <= 0:
        max_month_count = 1

    for item in monthly_orders:
        item["percent"] = round((item["count"] / max_month_count) * 100)

    total_bulk_requests = BulkOrderRequest.objects.count()
    new_bulk_requests = BulkOrderRequest.objects.filter(status="NEW").count()

    context = {
        "total_products": total_products,
        "active_products": active_products,
        "total_categories": total_categories,

        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "confirmed_orders": confirmed_orders,
        "packed_orders": packed_orders,
        "out_for_delivery_orders": out_for_delivery_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,

        "pending_percent": pending_percent,
        "confirmed_percent": confirmed_percent,
        "packed_percent": packed_percent,
        "out_for_delivery_percent": out_for_delivery_percent,
        "delivered_percent": delivered_percent,
        "cancelled_percent": cancelled_percent,

        "total_customers": total_customers,
        "active_customers": active_customers,

        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,

        "estimated_revenue": estimated_revenue,
        "delivered_revenue": delivered_revenue,

        "cod_orders": cod_orders,
        "upi_orders": upi_orders,
        "cod_percent": cod_percent,
        "upi_percent": upi_percent,

        "top_products": top_products,
        "monthly_orders": monthly_orders,

        "total_bulk_requests": total_bulk_requests,
        "new_bulk_requests": new_bulk_requests,

        "latest_orders": latest_orders,
        "low_stock_products": low_stock_products,
    }

    return render(request, "accounts/superadmin_dashboard.html", context)


# ===============================
# CATEGORY MANAGEMENT
# ===============================

@login_required
@store_permission_required("store.manage_catalog")
def superadmin_category_list(request):
    query = request.GET.get("q", "").strip()

    categories = Category.objects.prefetch_related("products").all()

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
@store_permission_required("store.manage_catalog")
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
@store_permission_required("store.manage_catalog")
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
@store_permission_required("store.manage_catalog")
def superadmin_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        try:
            category.delete()
        except ProtectedError:
            messages.error(
                request,
                "This category contains products with order or inventory history. Archive those products instead.",
            )
        else:
            messages.success(request, "Category deleted successfully.")
        return redirect("superadmin_category_list")

    return render(request, "accounts/superadmin_confirm_delete.html", {
        "object": category,
        "cancel_url": "superadmin_category_list",
        "title": "Delete Category",
    })


# ===============================
# PRODUCT MANAGEMENT
# ===============================

@login_required
@store_permission_required("store.manage_catalog", "store.manage_inventory")
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
        "can_manage_catalog": request.user.is_superuser or request.user.has_perm("store.manage_catalog"),
        "can_manage_inventory": request.user.is_superuser or request.user.has_perm("store.manage_inventory"),
    })


@login_required
@store_permission_required("store.manage_catalog")
def superadmin_product_create(request):
    can_set_opening_stock = (
        request.user.is_superuser or request.user.has_perm("store.manage_inventory")
    )
    if request.method == "POST":
        form = ProductForm(
            request.POST,
            request.FILES,
            include_stock=can_set_opening_stock,
        )

        if form.is_valid():
            with transaction.atomic():
                product = form.save(commit=False)
                opening_stock = product.stock if can_set_opening_stock else 0
                product.stock = 0
                product.save()
                form.save_m2m()
                if opening_stock:
                    change_stock(
                        product=product,
                        quantity_delta=opening_stock,
                        reason="INITIAL",
                        actor=request.user,
                        note="Opening stock on product creation",
                    )
            messages.success(request, "Product created successfully.")
            return redirect("superadmin_product_list")
    else:
        form = ProductForm(include_stock=can_set_opening_stock)

    return render(request, "accounts/superadmin_product_form.html", {
        "form": form,
        "title": "Add Product",
    })


@login_required
@store_permission_required("store.manage_catalog")
def superadmin_product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(
            request.POST,
            request.FILES,
            instance=product,
            include_stock=False,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect("superadmin_product_list")
    else:
        form = ProductForm(instance=product, include_stock=False)

    return render(request, "accounts/superadmin_product_form.html", {
        "form": form,
        "title": "Edit Product",
        "product": product,
    })


@login_required
@store_permission_required("store.manage_catalog")
def superadmin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        try:
            product.delete()
        except ProtectedError:
            messages.error(
                request,
                "This product has order or inventory history and cannot be deleted. Mark it inactive instead.",
            )
        else:
            messages.success(request, "Product deleted successfully.")
        return redirect("superadmin_product_list")

    return render(request, "accounts/superadmin_confirm_delete.html", {
        "object": product,
        "cancel_url": "superadmin_product_list",
        "title": "Delete Product",
    })


# ===============================
# ORDER MANAGEMENT
# ===============================

@login_required
@store_permission_required("store.manage_orders")
def superadmin_order_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    orders = Order.objects.select_related("product", "product__category").all()

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
@store_permission_required("store.manage_orders")
def superadmin_order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("product", "product__category").prefetch_related("status_events"),
        pk=pk,
    )

    if request.method == "POST":
        previous_status = order.status
        form = OrderStatusForm(request.POST, instance=order)

        if form.is_valid():
            with transaction.atomic():
                order = form.save()
                record_order_status_change(
                    order=order,
                    from_status=previous_status,
                    actor=request.user,
                    note="Updated by store staff",
                )
            messages.success(request, "Order updated successfully.")
            return redirect("superadmin_order_detail", pk=order.pk)
    else:
        form = OrderStatusForm(instance=order)

    return render(request, "accounts/superadmin_order_detail.html", {
        "order": order,
        "form": form,
    })


# ===============================
# BULK REQUEST MANAGEMENT
# ===============================

@login_required
@store_permission_required("store.manage_bulk_requests")
def superadmin_bulk_request_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    bulk_requests = BulkOrderRequest.objects.all()

    if query:
        bulk_requests = bulk_requests.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(organisation__icontains=query) |
            Q(requirement__icontains=query)
        )

    if status:
        bulk_requests = bulk_requests.filter(status=status)

    paginator = Paginator(bulk_requests, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "query": query,
        "status": status,
        "status_choices": BulkOrderRequest.STATUS_CHOICES,
    }

    return render(request, "accounts/superadmin_bulk_request_list.html", context)


@login_required
@store_permission_required("store.manage_bulk_requests")
def superadmin_bulk_request_detail(request, pk):
    bulk_request = get_object_or_404(
        BulkOrderRequest.objects.prefetch_related("quote_lines", "orders"),
        pk=pk,
    )

    if request.method == "POST" and request.POST.get("action") == "save_quote":
        quote_formset = BulkQuoteLineFormSet(
            request.POST,
            instance=bulk_request,
            prefix="quote",
        )
        form = BulkOrderStatusForm(instance=bulk_request)
        if bulk_request.status == "CONVERTED":
            messages.error(request, "An accepted quote cannot be edited.")
        elif quote_formset.is_valid():
            quote_lines = quote_formset.save(commit=False)
            with transaction.atomic():
                for deleted_line in quote_formset.deleted_objects:
                    deleted_line.delete()
                for line in quote_lines:
                    line.request = bulk_request
                    line.product_name_snapshot = line.product.name
                    line.product_brand_snapshot = line.product.brand
                    line.product_category_snapshot = line.product.category.name
                    line.save()
                quote_formset.save_m2m()
                bulk_request.status = "QUOTED"
                bulk_request.quote_valid_until = timezone.now() + timedelta(days=7)
                bulk_request.save(
                    update_fields=["status", "quote_valid_until", "updated_at"]
                )
                quote_url = request.build_absolute_uri(
                    reverse(
                        "bulk_quote_accept",
                        kwargs={"token": bulk_request.quote_token},
                    )
                )
                transaction.on_commit(
                    lambda request_id=bulk_request.pk, url=quote_url: send_bulk_quote_email(
                        request_id,
                        url,
                    )
                )
            messages.success(
                request,
                "Quote saved. The customer can accept it for the next seven days.",
            )
            return redirect("superadmin_bulk_request_detail", pk=bulk_request.pk)
    elif request.method == "POST":
        form = BulkOrderStatusForm(request.POST, instance=bulk_request)

        if form.is_valid():
            form.save()
            messages.success(request, "Bulk request updated successfully.")
            return redirect("superadmin_bulk_request_detail", pk=bulk_request.pk)
        quote_formset = BulkQuoteLineFormSet(instance=bulk_request, prefix="quote")
    else:
        form = BulkOrderStatusForm(instance=bulk_request)
        quote_formset = BulkQuoteLineFormSet(instance=bulk_request, prefix="quote")

    context = {
        "bulk_request": bulk_request,
        "form": form,
        "quote_formset": quote_formset,
        "quote_url": (
            request.build_absolute_uri(
                reverse(
                    "bulk_quote_accept",
                    kwargs={"token": bulk_request.quote_token},
                )
            )
            if bulk_request.status == "QUOTED"
            else ""
        ),
    }

    return render(request, "accounts/superadmin_bulk_request_detail.html", context)


# ===============================
# CUSTOMER MANAGEMENT
# ===============================

@login_required
@store_permission_required("accounts.view_store_customers")
def superadmin_customer_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    customers = (
        User.objects
        .filter(is_superuser=False)
        .annotate(order_count=Count("orders"))
        .order_by("-date_joined")
    )

    if query:
        customers = customers.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    if status == "active":
        customers = customers.filter(is_active=True)
    elif status == "inactive":
        customers = customers.filter(is_active=False)

    paginator = Paginator(customers, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "query": query,
        "status": status,
    }

    return render(request, "accounts/superadmin_customer_list.html", context)

@login_required
@store_permission_required("accounts.view_store_customers")
def superadmin_customer_detail(request, pk):
    customer = get_object_or_404(
        User.objects.annotate(order_count=Count("orders")),
        pk=pk,
        is_superuser=False,
    )

    profile = getattr(customer, "customer_profile", None)

    orders = (
        Order.objects
        .select_related("product", "product__category")
        .filter(customer=customer)
        .order_by("-created_at")
    )

    total_spent = 0
    for order in orders:
        total_spent += order.total_price()

    pending_orders = orders.filter(status="PENDING").count()
    delivered_orders = orders.filter(status="DELIVERED").count()
    cancelled_orders = orders.filter(status="CANCELLED").count()

    profile_completed = False
    if profile:
        profile_completed = bool(profile.phone and profile.address)

    context = {
        "customer": customer,
        "profile": profile,
        "profile_completed": profile_completed,
        "orders": orders,
        "total_spent": total_spent,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
    }

    return render(request, "accounts/superadmin_customer_detail.html", context)

@login_required
@store_permission_required("accounts.manage_store_customers")
def superadmin_customer_toggle_status(request, pk):
    customer = get_object_or_404(User, pk=pk, is_superuser=False)

    if request.method == "POST":
        customer.is_active = not customer.is_active
        customer.save(update_fields=["is_active"])

        if customer.is_active:
            messages.success(request, f"{customer.username} has been activated.")
        else:
            messages.success(request, f"{customer.username} has been deactivated.")

    return redirect("superadmin_customer_detail", pk=customer.pk)


# ===============================
# LOW STOCK MANAGEMENT
# ===============================

@login_required
@store_permission_required("store.manage_inventory")
def superadmin_low_stock_list(request):
    query = request.GET.get("q", "").strip()
    stock_filter = request.GET.get("stock", "low").strip()

    products = Product.objects.select_related("category").all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query)
        )

    if stock_filter == "out":
        products = products.filter(stock=0)
    elif stock_filter == "low":
        products = products.filter(stock__gt=0, stock__lte=5)
    elif stock_filter == "all-alerts":
        products = products.filter(stock__lte=5)
    else:
        products = products.filter(stock__lte=5)

    products = products.order_by("stock", "name")

    low_stock_count = Product.objects.filter(stock__gt=0, stock__lte=5).count()
    out_of_stock_count = Product.objects.filter(stock=0).count()
    total_alert_count = Product.objects.filter(stock__lte=5).count()

    paginator = Paginator(products, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "query": query,
        "stock_filter": stock_filter,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "total_alert_count": total_alert_count,
    }

    return render(request, "accounts/superadmin_low_stock_list.html", context)


@login_required
@store_permission_required("store.manage_inventory")
def superadmin_product_restock(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductRestockForm(request.POST)

        if form.is_valid():
            add_stock = form.cleaned_data["add_stock"]
            with transaction.atomic():
                product = Product.objects.select_for_update().get(pk=pk)
                change_stock(
                    product=product,
                    quantity_delta=add_stock,
                    reason="RESTOCK",
                    actor=request.user,
                    note=form.cleaned_data["reason"],
                )

            messages.success(
                request,
                f"{add_stock} units added to {product.name}. Current stock: {product.stock}."
            )
        else:
            messages.error(request, "Please enter a valid stock quantity.")

    return redirect("superadmin_low_stock_list")


@login_required
@store_permission_required("store.manage_inventory")
def superadmin_product_adjust_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = InventoryAdjustmentForm(request.POST)
        if form.is_valid():
            quantity_delta = form.cleaned_data["quantity"]
            if form.cleaned_data["direction"] == "REMOVE":
                quantity_delta *= -1
            try:
                with transaction.atomic():
                    product = Product.objects.select_for_update().get(pk=pk)
                    change_stock(
                        product=product,
                        quantity_delta=quantity_delta,
                        reason="ADJUSTMENT",
                        actor=request.user,
                        note=form.cleaned_data["reason"],
                    )
            except ValidationError as error:
                messages.error(request, "; ".join(error.messages))
            else:
                messages.success(request, f"Stock adjusted for {product.name}.")
        else:
            messages.error(request, "Enter a quantity and a clear reason for the adjustment.")
        return redirect("superadmin_inventory_movements")
    return render(request, "accounts/superadmin_inventory_adjust.html", {
        "product": product,
        "form": InventoryAdjustmentForm(),
    })


@login_required
@store_permission_required("store.manage_inventory")
def superadmin_inventory_movements(request):
    movements = InventoryMovement.objects.select_related(
        "product", "actor", "order"
    )
    reason = request.GET.get("reason", "").strip()
    query = request.GET.get("q", "").strip()
    if reason:
        movements = movements.filter(reason=reason)
    if query:
        movements = movements.filter(
            Q(product__name__icontains=query)
            | Q(note__icontains=query)
            | Q(order__name__icontains=query)
        )
    page_obj = Paginator(movements, 25).get_page(request.GET.get("page"))
    return render(request, "accounts/superadmin_inventory_movements.html", {
        "page_obj": page_obj,
        "query": query,
        "reason": reason,
        "reason_choices": InventoryMovement.REASON_CHOICES,
    })


@login_required
@store_permission_required("store.manage_delivery_zones")
def superadmin_delivery_zones(request, pk=None):
    zone = get_object_or_404(DeliveryZone, pk=pk) if pk is not None else None
    form = DeliveryZoneForm(request.POST or None, instance=zone)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Delivery zone saved.")
        return redirect("superadmin_delivery_zones")

    return render(request, "accounts/superadmin_delivery_zones.html", {
        "form": form,
        "zones": DeliveryZone.objects.all(),
        "editing_zone": zone,
    })


@login_required
@store_permission_required("store.manage_orders")
def superadmin_order_invoice(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("product", "product__category", "customer"),
        pk=pk,
    )

    context = {
        "order": order,
    }

    return render(request, "accounts/superadmin_order_invoice.html", context)


# ===============================
# CSV EXPORTS
# ===============================

def _csv_response(filename):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    return response


@login_required
@store_permission_required("store.manage_catalog", "store.manage_inventory")
def superadmin_export_products_csv(request):
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()
    stock_filter = request.GET.get("stock", "").strip()

    products = Product.objects.select_related("category").all()

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

    products = products.order_by("-created_at")

    response = _csv_response("products_export.csv")
    writer = csv.writer(response)

    writer.writerow([
        "ID",
        "Product Name",
        "Category",
        "Brand",
        "Description",
        "Original Price",
        "Discount Price",
        "Final Price",
        "Stock",
        "Stock Status",
        "Featured",
        "Active",
        "Created At",
    ])

    for product in products:
        writer.writerow([
            product.id,
            product.name,
            product.category.name if product.category else "",
            product.brand,
            product.description,
            product.price,
            product.discount_price if product.discount_price else "",
            product.final_price(),
            product.stock,
            product.stock_status(),
            "Yes" if product.is_featured else "No",
            "Yes" if product.is_active else "No",
            product.created_at.strftime("%d-%m-%Y %I:%M %p") if product.created_at else "",
        ])

    return response


@login_required
@store_permission_required("store.manage_orders")
def superadmin_export_orders_csv(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    orders = Order.objects.select_related(
        "product",
        "product__category",
        "customer"
    ).all()

    if query:
        orders = orders.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(product__name__icontains=query) |
            Q(customer__username__icontains=query)
        )

    if status:
        orders = orders.filter(status=status)

    orders = orders.order_by("-created_at")

    response = _csv_response("orders_export.csv")
    writer = csv.writer(response)

    writer.writerow([
        "Order ID",
        "Customer Name",
        "Phone",
        "Customer Email",
        "Address",
        "Delivery PIN Code",
        "Delivery Fee",
        "Carrier",
        "Tracking Reference",
        "Registered Username",
        "Product",
        "Category",
        "Quantity",
        "Unit Price",
        "Total Price",
        "Payment Method",
        "Payment Status",
        "Transaction Reference",
        "Refund Reference",
        "Refund Amount",
        "Status",
        "Admin Note",
        "Created At",
        "Updated At",
    ])

    for order in orders:
        writer.writerow([
            order.id,
            order.name,
            order.phone,
            order.customer_email or (order.customer.email if order.customer else ""),
            order.address,
            order.delivery_pincode,
            order.delivery_fee,
            order.carrier_name,
            order.tracking_number,
            order.customer.username if order.customer else "",
            order.product_name_snapshot,
            order.product_category_snapshot,
            order.quantity,
            order.unit_price_snapshot,
            order.total_price(),
            order.get_payment_method_display(),
            order.get_payment_status_display(),
            order.transaction_reference,
            order.refund_reference,
            order.refund_amount,
            order.get_status_display(),
            order.admin_note,
            order.created_at.strftime("%d-%m-%Y %I:%M %p") if order.created_at else "",
            order.updated_at.strftime("%d-%m-%Y %I:%M %p") if order.updated_at else "",
        ])

    return response


@login_required
@store_permission_required("accounts.view_store_customers")
def superadmin_export_customers_csv(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    customers = (
        User.objects
        .filter(is_superuser=False)
        .annotate(order_count=Count("orders"))
        .order_by("-date_joined")
    )

    if query:
        customers = customers.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    if status == "active":
        customers = customers.filter(is_active=True)
    elif status == "inactive":
        customers = customers.filter(is_active=False)

    response = _csv_response("customers_export.csv")
    writer = csv.writer(response)

    writer.writerow([
        "User ID",
        "Username",
        "Full Name",
        "First Name",
        "Last Name",
        "Email",
        "Active",
        "Staff",
        "Superuser",
        "Total Orders",
        "Date Joined",
        "Last Login",
    ])

    for customer in customers:
        writer.writerow([
            customer.id,
            customer.username,
            customer.get_full_name(),
            customer.first_name,
            customer.last_name,
            customer.email,
            "Yes" if customer.is_active else "No",
            "Yes" if customer.is_staff else "No",
            "Yes" if customer.is_superuser else "No",
            customer.order_count,
            customer.date_joined.strftime("%d-%m-%Y %I:%M %p") if customer.date_joined else "",
            customer.last_login.strftime("%d-%m-%Y %I:%M %p") if customer.last_login else "",
        ])

    return response


@login_required
@store_permission_required("store.manage_bulk_requests")
def superadmin_export_bulk_requests_csv(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    bulk_requests = BulkOrderRequest.objects.all()

    if query:
        bulk_requests = bulk_requests.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(organisation__icontains=query) |
            Q(requirement__icontains=query)
        )

    if status:
        bulk_requests = bulk_requests.filter(status=status)

    bulk_requests = bulk_requests.order_by("-created_at")

    response = _csv_response("bulk_requests_export.csv")
    writer = csv.writer(response)

    writer.writerow([
        "Request ID",
        "Name",
        "Phone",
        "Organisation",
        "Requirement",
        "Status",
        "Admin Note",
        "Created At",
        "Updated At",
    ])

    for item in bulk_requests:
        writer.writerow([
            item.id,
            item.name,
            item.phone,
            item.organisation,
            item.requirement,
            item.get_status_display(),
            item.admin_note,
            item.created_at.strftime("%d-%m-%Y %I:%M %p") if item.created_at else "",
            item.updated_at.strftime("%d-%m-%Y %I:%M %p") if item.updated_at else "",
        ])

    return response


# Add this import near other imports:
from .forms import CustomerProfileForm
from .models import CustomerProfile


# Add this view after custom_logout or before superadmin views:

@login_required
def customer_profile(request):
    if request.user.is_superuser:
        return redirect("superadmin_dashboard")

    profile, created = CustomerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = CustomerProfileForm(request.POST, instance=profile, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("customer_profile")
    else:
        form = CustomerProfileForm(instance=profile, user=request.user)

    return render(request, "accounts/customer_profile.html", {
        "form": form,
        "profile": profile,
    })
