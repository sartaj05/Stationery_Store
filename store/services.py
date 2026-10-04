from decimal import Decimal
from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction

from .models import (
    BulkOrderRequest,
    DeliveryZone,
    InventoryMovement,
    Order,
    OrderStatusEvent,
)


def get_delivery_quote(pincode):
    pincode = (pincode or "").strip()
    zone = DeliveryZone.objects.filter(pincode=pincode, is_active=True).first()
    configured = DeliveryZone.objects.exists()

    if not configured:
        return SimpleNamespace(
            pincode=pincode,
            zone=None,
            serviceable=True,
            delivery_fee=Decimal("0.00"),
            estimated_days=None,
            configured=False,
        )

    if not zone or not zone.is_serviceable:
        return SimpleNamespace(
            pincode=pincode,
            zone=zone,
            serviceable=False,
            delivery_fee=None,
            estimated_days=None,
            configured=True,
        )

    return SimpleNamespace(
        pincode=pincode,
        zone=zone,
        serviceable=True,
        delivery_fee=zone.delivery_fee,
        estimated_days=zone.estimated_days,
        configured=True,
    )


def change_stock(*, product, quantity_delta, reason, actor=None, order=None, note=""):
    """Apply a stock delta and write the matching audit record.

    Callers that mutate existing inventory must hold a row lock inside
    ``transaction.atomic()`` before calling this function.
    """
    if quantity_delta == 0:
        raise ValidationError("A stock movement must change the quantity.")

    next_stock = product.stock + quantity_delta
    if next_stock < 0:
        raise ValidationError("Stock cannot be reduced below zero.")

    product.stock = next_stock
    product.save(update_fields=["stock"])

    return InventoryMovement.objects.create(
        product=product,
        order=order,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        reason=reason,
        quantity_delta=quantity_delta,
        note=note[:255],
    )


def send_order_status_email(order_id, to_status):
    order = Order.objects.select_related("customer").filter(pk=order_id).first()
    if not order:
        return
    recipient = order.customer_email or (
        order.customer.email if order.customer else ""
    )
    if not recipient:
        return

    first_name = (
        order.customer.first_name
        if order.customer and order.customer.first_name
        else order.name
    )
    status_label = dict(Order.STATUS_CHOICES).get(
        to_status,
        order.get_status_display(),
    )
    send_mail(
        subject=f"Delhi Stationery order #{order.id}: {status_label}",
        message=(
            f"Hello {first_name},\n\n"
            f"Your order #{order.id} status is now {status_label}.\n"
            + (
                f"Carrier: {order.carrier_name}\n"
                if order.carrier_name
                else ""
            )
            + (
                f"Tracking reference: {order.tracking_number}\n"
                if order.tracking_number
                else ""
            )
            + "\n"
            f"You can track it using the phone number provided at checkout.\n\n"
            "Delhi Stationery"
        ),
        from_email=None,
        recipient_list=[recipient],
        fail_silently=True,
    )


def record_order_status_change(*, order, from_status, actor=None, note="", notify=True):
    if from_status == order.status:
        return None

    event = OrderStatusEvent.objects.create(
        order=order,
        from_status=from_status,
        to_status=order.status,
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        note=note[:255],
    )
    if notify and (order.customer_id or order.customer_email):
        transaction.on_commit(
            lambda order_id=order.pk, to_status=order.status: send_order_status_email(
                order_id,
                to_status,
            )
        )
    return event


def send_bulk_quote_email(request_id, quote_url):
    bulk_request = BulkOrderRequest.objects.prefetch_related("quote_lines").filter(
        pk=request_id
    ).first()
    if not bulk_request or not bulk_request.email:
        return

    lines = "\n".join(
        f"- {line.product_name_snapshot}: {line.quantity} x {line.unit_price} = {line.total_price()}"
        for line in bulk_request.quote_lines.all()
    )
    expiry = (
        bulk_request.quote_valid_until.strftime("%d %b %Y")
        if bulk_request.quote_valid_until
        else "No expiry set"
    )
    send_mail(
        subject="Your Delhi Stationery bulk quote is ready",
        message=(
            f"Hello {bulk_request.name},\n\n"
            "Your requested bulk quote is ready:\n"
            f"{lines}\n\n"
            f"Items subtotal: {bulk_request.quote_subtotal()}\n"
            f"Please review delivery and accept the quote here: {quote_url}\n"
            f"Quote valid until: {expiry}\n\n"
            "Delhi Stationery"
        ),
        from_email=None,
        recipient_list=[bulk_request.email],
        fail_silently=True,
    )


def send_bulk_conversion_email(request_id):
    bulk_request = BulkOrderRequest.objects.prefetch_related("orders").filter(
        pk=request_id
    ).first()
    if not bulk_request or not bulk_request.email:
        return

    orders = list(bulk_request.orders.all())
    order_ids = ", ".join(f"#{order.pk}" for order in orders)
    total = sum((order.total_price() for order in orders), start=Decimal("0.00"))
    send_mail(
        subject="Your Delhi Stationery bulk quote was accepted",
        message=(
            f"Hello {bulk_request.name},\n\n"
            f"Your quote has been accepted and converted to orders: {order_ids}.\n"
            f"Total including delivery: {total}.\n"
            "Use your phone number and any order ID to track fulfilment.\n\n"
            "Delhi Stationery"
        ),
        from_email=None,
        recipient_list=[bulk_request.email],
        fail_silently=True,
    )
