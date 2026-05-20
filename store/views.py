from decimal import Decimal
from types import SimpleNamespace

from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Product, Category, Order
from .forms import OrderForm, BulkOrderRequestForm


# ============================================================
# DUMMY PUBLIC CONTENT
# Shows only when no active real products exist.
# Once admin/superadmin adds real active product, dummy disappears.
# ============================================================

def _dummy_category(name, slug, icon):
    return SimpleNamespace(
        id=slug,
        name=name,
        slug=slug,
        icon=icon,
        is_dummy=True,
    )


def _dummy_product(
    name,
    category,
    brand,
    description,
    price,
    discount_price,
    stock,
    image_url,
    is_featured=False,
):
    return SimpleNamespace(
        id=None,
        name=name,
        category=category,
        brand=brand,
        description=description,
        price=Decimal(str(price)),
        discount_price=Decimal(str(discount_price)) if discount_price else None,
        stock=stock,
        image=None,
        image_url=image_url,
        is_featured=is_featured,
        is_active=True,
        is_dummy=True,
        final_price=Decimal(str(discount_price)) if discount_price else Decimal(str(price)),
        stock_status=(
            "Out of Stock"
            if stock <= 0
            else "Low Stock"
            if stock <= 5
            else "Available"
        ),
    )


def get_dummy_categories():
    return [
        _dummy_category("Notebooks", "notebooks", "📒"),
        _dummy_category("Pens", "pens", "🖊️"),
        _dummy_category("School Supplies", "school-supplies", "🎒"),
        _dummy_category("Office Stationery", "office-stationery", "📁"),
        _dummy_category("Exam Materials", "exam-materials", "📋"),
        _dummy_category("Art Supplies", "art-supplies", "🎨"),
    ]


def get_dummy_products():
    categories = {category.slug: category for category in get_dummy_categories()}

    return [
        _dummy_product(
            name="Premium A4 Notebook Pack",
            category=categories["notebooks"],
            brand="Classmate",
            description="High-quality ruled notebooks suitable for school, coaching, office notes and daily writing.",
            price="240",
            discount_price="199",
            stock=25,
            image_url="https://images.unsplash.com/photo-1531346878377-a5be20888e57?auto=format&fit=crop&w=900&q=80",
            is_featured=True,
        ),
        _dummy_product(
            name="Blue Ball Pen Set",
            category=categories["pens"],
            brand="Cello",
            description="Smooth writing blue ball pen set for students, offices and daily stationery use.",
            price="120",
            discount_price="99",
            stock=60,
            image_url="https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?auto=format&fit=crop&w=900&q=80",
            is_featured=True,
        ),
        _dummy_product(
            name="Student Geometry Box",
            category=categories["school-supplies"],
            brand="Camlin",
            description="Complete geometry box for school students with compass, divider, scale and protractor.",
            price="180",
            discount_price="149",
            stock=18,
            image_url="https://images.unsplash.com/photo-1456735190827-d1262f71b8a3?auto=format&fit=crop&w=900&q=80",
            is_featured=True,
        ),
        _dummy_product(
            name="Office File Folder Combo",
            category=categories["office-stationery"],
            brand="Solo",
            description="Durable file folders for office documents, school certificates and business records.",
            price="300",
            discount_price="249",
            stock=12,
            image_url="https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&w=900&q=80",
            is_featured=True,
        ),
        _dummy_product(
            name="Exam Writing Pad",
            category=categories["exam-materials"],
            brand="Delhi Stationery",
            description="Strong and lightweight exam pad for school, college and competitive exams.",
            price="90",
            discount_price="75",
            stock=30,
            image_url="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80",
            is_featured=False,
        ),
        _dummy_product(
            name="Colour Pencil Kit",
            category=categories["art-supplies"],
            brand="Faber-Castell",
            description="Bright colour pencil kit for drawing, school projects and creative artwork.",
            price="220",
            discount_price="179",
            stock=9,
            image_url="https://images.unsplash.com/photo-1513364776144-60967b0f800f?auto=format&fit=crop&w=900&q=80",
            is_featured=False,
        ),
        _dummy_product(
            name="Register Long Book",
            category=categories["notebooks"],
            brand="Navneet",
            description="Long register book for accounts, rough work, coaching notes and office records.",
            price="160",
            discount_price="135",
            stock=22,
            image_url="https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=80",
            is_featured=False,
        ),
        _dummy_product(
            name="Stapler and Pin Set",
            category=categories["office-stationery"],
            brand="Kangaro",
            description="Office stapler with pin pack for files, documents and daily desk work.",
            price="180",
            discount_price="150",
            stock=14,
            image_url="https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=900&q=80",
            is_featured=False,
        ),
    ]


def _filter_dummy_products(products, query=None, category_slug=None):
    filtered_products = products

    if query:
        q = query.lower()
        filtered_products = [
            product for product in filtered_products
            if q in product.name.lower()
            or q in product.brand.lower()
            or q in product.description.lower()
            or q in product.category.name.lower()
        ]

    if category_slug:
        filtered_products = [
            product for product in filtered_products
            if product.category.slug == category_slug
        ]

    return filtered_products


# ============================================================
# PUBLIC STORE VIEWS
# ============================================================

def home(request):
    real_active_products = Product.objects.filter(is_active=True)
    has_real_products = real_active_products.exists()

    if has_real_products:
        categories = Category.objects.all()
        featured_products = real_active_products.filter(is_featured=True)[:8]

        if not featured_products.exists():
            featured_products = real_active_products.order_by("-created_at")[:8]

        latest_products = real_active_products.order_by("-created_at")[:12]
        using_dummy_content = False
    else:
        categories = get_dummy_categories()
        dummy_products = get_dummy_products()
        featured_products = [
            product for product in dummy_products
            if product.is_featured
        ][:8]
        latest_products = dummy_products[:12]
        using_dummy_content = True

    context = {
        "categories": categories,
        "featured_products": featured_products,
        "latest_products": latest_products,
        "using_dummy_content": using_dummy_content,
    }

    return render(request, "store/home.html", context)


def product_list(request):
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()

    real_active_products = Product.objects.filter(is_active=True)
    has_real_products = real_active_products.exists()

    if has_real_products:
        products = real_active_products.select_related("category")
        categories = Category.objects.all()
        using_dummy_content = False

        if query:
            products = products.filter(
                Q(name__icontains=query)
                | Q(brand__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query)
            )

        if category_slug:
            products = products.filter(category__slug=category_slug)

    else:
        categories = get_dummy_categories()
        products = _filter_dummy_products(
            get_dummy_products(),
            query=query,
            category_slug=category_slug,
        )
        using_dummy_content = True

    context = {
        "products": products,
        "categories": categories,
        "query": query,
        "selected_category": category_slug,
        "using_dummy_content": using_dummy_content,
    }

    return render(request, "store/product_list.html", context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    related_products = (
        Product.objects
        .filter(category=product.category, is_active=True)
        .exclude(id=product.id)
        .select_related("category")[:4]
    )

    context = {
        "product": product,
        "related_products": related_products,
    }

    return render(request, "store/product_detail.html", context)


def order_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if product.stock <= 0:
        messages.error(request, "This product is currently out of stock.")
        return redirect("product_detail", product_id=product.id)

    if request.method == "POST":
        form = OrderForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                locked_product = Product.objects.select_for_update().get(
                    id=product.id,
                    is_active=True,
                )

                order = form.save(commit=False)
                order.product = locked_product

                if request.user.is_authenticated:
                    order.customer = request.user

                if order.quantity > locked_product.stock:
                    messages.error(
                        request,
                        "Quantity is greater than available stock."
                    )
                    return redirect("order_product", product_id=locked_product.id)

                order.save()

                locked_product.stock -= order.quantity
                locked_product.save(update_fields=["stock"])

            messages.success(
                request,
                f"Your order has been placed successfully. Your Order ID is #{order.id}."
            )

            request.session["last_order_id"] = order.id

            return redirect("order_success")

    else:
        initial_data = {}

        if request.user.is_authenticated:
            initial_data["name"] = (
                request.user.get_full_name()
                or request.user.first_name
                or request.user.username
            )

            profile = getattr(request.user, "customer_profile", None)

            if profile:
                initial_data["phone"] = profile.phone or ""
                initial_data["address"] = profile.full_address() or ""
            else:
                initial_data["phone"] = ""

        form = OrderForm(initial=initial_data)

    context = {
        "product": product,
        "form": form,
    }

    return render(request, "store/order_form.html", context)


def order_success(request):
    last_order_id = request.session.get("last_order_id")

    return render(request, "store/order_success.html", {
        "last_order_id": last_order_id,
    })


def track_order(request):
    orders = None
    searched = False

    phone = request.GET.get("phone", "").strip()
    order_id = request.GET.get("order_id", "").strip()

    if phone or order_id:
        searched = True

        orders = (
            Order.objects
            .select_related("product", "product__category")
            .all()
        )

        if phone:
            orders = orders.filter(phone=phone)

        if order_id:
            if order_id.isdigit():
                orders = orders.filter(id=int(order_id))
            else:
                orders = Order.objects.none()

        orders = orders.order_by("-created_at")

        if not orders.exists():
            messages.error(
                request,
                "No order found with the provided details. Please check your phone number or order ID."
            )

    context = {
        "orders": orders,
        "searched": searched,
        "phone": phone,
        "order_id": order_id,
    }

    return render(request, "store/track_order.html", context)


@login_required
def my_orders(request):
    orders = (
        Order.objects
        .select_related("product", "product__category")
        .filter(customer=request.user)
        .order_by("-created_at")
    )

    context = {
        "orders": orders,
    }

    return render(request, "store/my_orders.html", context)


def about(request):
    return render(request, "store/about.html")


def contact(request):
    if request.method == "POST":
        form = BulkOrderRequestForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your bulk order request has been submitted successfully. We will contact you soon."
            )
            return redirect("contact")
    else:
        form = BulkOrderRequestForm()

    return render(request, "store/contact.html", {
        "form": form,
    })
    
    
@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("product"),
        id=order_id,
        customer=request.user
    )

    if request.method == "POST":
        if order.status not in ["PENDING", "CONFIRMED"]:
            messages.error(request, "This order cannot be cancelled now.")
            return redirect("my_orders")

        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=order.product.id)

            order.status = "CANCELLED"
            order.admin_note = "Cancelled by customer."
            order.save(update_fields=["status", "admin_note", "updated_at"])

            product.stock += order.quantity
            product.save(update_fields=["stock"])

        messages.success(request, f"Order #{order.id} cancelled successfully.")
        return redirect("my_orders")

    return redirect("my_orders")


@login_required
def reorder_product(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("product"),
        id=order_id,
        customer=request.user
    )

    if not order.product.is_active:
        messages.error(request, "This product is no longer available.")
        return redirect("my_orders")

    if order.product.stock <= 0:
        messages.error(request, "This product is currently out of stock.")
        return redirect("my_orders")

    return redirect("order_product", product_id=order.product.id)