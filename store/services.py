from django.core.exceptions import ValidationError

from .models import InventoryMovement


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
