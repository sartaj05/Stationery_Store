from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages

from .models import Product, Category
from .forms import OrderForm


def home(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    latest_products = Product.objects.filter(is_active=True).order_by("-created_at")[:12]

    context = {
        "categories": categories,
        "featured_products": featured_products,
        "latest_products": latest_products,
    }
    return render(request, "store/home.html", context)


def product_list(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()

    query = request.GET.get("q")
    category_slug = request.GET.get("category")

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(brand__icontains=query) |
            Q(description__icontains=query)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    context = {
        "products": products,
        "categories": categories,
        "query": query,
        "selected_category": category_slug,
    }
    return render(request, "store/product_list.html", context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]

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
            order = form.save(commit=False)
            order.product = product

            if order.quantity > product.stock:
                messages.error(request, "Quantity is greater than available stock.")
                return redirect("order_product", product_id=product.id)

            order.save()

            product.stock -= order.quantity
            product.save()

            messages.success(request, "Your order has been placed successfully.")
            return redirect("order_success")

    else:
        form = OrderForm()

    context = {
        "product": product,
        "form": form,
    }
    return render(request, "store/order_form.html", context)


def order_success(request):
    return render(request, "store/order_success.html")


def about(request):
    return render(request, "store/about.html")


def contact(request):
    return render(request, "store/contact.html")