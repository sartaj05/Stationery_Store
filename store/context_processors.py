def cart_counter(request):
    cart = request.session.get("cart", {})

    cart_count = 0

    for item in cart.values():
        try:
            cart_count += int(item.get("quantity", 0))
        except (TypeError, ValueError):
            continue

    return {
        "global_cart_count": cart_count,
    }