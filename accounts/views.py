from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
import csv

from django.http import HttpResponse
from store.forms import (
    CategoryForm,
    ProductForm,
    OrderStatusForm,
    ProductRestockForm,
    BulkOrderStatusForm,
)
from store.models import Category, Order, Product, BulkOrderRequest


# ===============================
# AUTH VIEWS
# ===============================

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


def is_superadmin(user):
    return user.is_authenticated and user.is_superuser


# ===============================
# SUPERADMIN DASHBOARD
# ===============================

@login_required
@user_passes_test(is_superadmin)
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
@user_passes_test(is_superadmin)
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


# ===============================
# PRODUCT MANAGEMENT
# ===============================

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


# ===============================
# ORDER MANAGEMENT
# ===============================

@login_required
@user_passes_test(is_superadmin)
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
@user_passes_test(is_superadmin)
def superadmin_order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("product", "product__category"),
        pk=pk,
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


# ===============================
# BULK REQUEST MANAGEMENT
# ===============================

@login_required
@user_passes_test(is_superadmin)
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
@user_passes_test(is_superadmin)
def superadmin_bulk_request_detail(request, pk):
    bulk_request = get_object_or_404(BulkOrderRequest, pk=pk)

    if request.method == "POST":
        form = BulkOrderStatusForm(request.POST, instance=bulk_request)

        if form.is_valid():
            form.save()
            messages.success(request, "Bulk request updated successfully.")
            return redirect("superadmin_bulk_request_detail", pk=bulk_request.pk)
    else:
        form = BulkOrderStatusForm(instance=bulk_request)

    context = {
        "bulk_request": bulk_request,
        "form": form,
    }

    return render(request, "accounts/superadmin_bulk_request_detail.html", context)


# ===============================
# CUSTOMER MANAGEMENT
# ===============================

@login_required
@user_passes_test(is_superadmin)
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
@user_passes_test(is_superadmin)
def superadmin_customer_detail(request, pk):
    customer = get_object_or_404(
        User.objects.annotate(order_count=Count("orders")),
        pk=pk,
        is_superuser=False,
    )

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

    context = {
        "customer": customer,
        "orders": orders,
        "total_spent": total_spent,
        "pending_orders": pending_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
    }

    return render(request, "accounts/superadmin_customer_detail.html", context)


@login_required
@user_passes_test(is_superadmin)
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
@user_passes_test(is_superadmin)
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
@user_passes_test(is_superadmin)
def superadmin_product_restock(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductRestockForm(request.POST)

        if form.is_valid():
            add_stock = form.cleaned_data["add_stock"]
            product.stock += add_stock
            product.save(update_fields=["stock"])

            messages.success(
                request,
                f"{add_stock} units added to {product.name}. Current stock: {product.stock}."
            )
        else:
            messages.error(request, "Please enter a valid stock quantity.")

    return redirect("superadmin_low_stock_list")


@login_required
@user_passes_test(is_superadmin)
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
@user_passes_test(is_superadmin)
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
@user_passes_test(is_superadmin)
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
        "Address",
        "Registered Username",
        "Product",
        "Category",
        "Quantity",
        "Unit Price",
        "Total Price",
        "Payment Method",
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
            order.address,
            order.customer.username if order.customer else "",
            order.product.name if order.product else "",
            order.product.category.name if order.product and order.product.category else "",
            order.quantity,
            order.product.final_price() if order.product else "",
            order.total_price(),
            order.get_payment_method_display(),
            order.get_status_display(),
            order.admin_note,
            order.created_at.strftime("%d-%m-%Y %I:%M %p") if order.created_at else "",
            order.updated_at.strftime("%d-%m-%Y %I:%M %p") if order.updated_at else "",
        ])

    return response


@login_required
@user_passes_test(is_superadmin)
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
@user_passes_test(is_superadmin)
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