from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core import mail
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomerProfile
from .forms import OrderStatusForm
from .models import (
    Category,
    DeliveryZone,
    InventoryMovement,
    Order,
    OrderStatusEvent,
    Product,
)


class StoreFlowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Notebooks",
            slug="notebooks",
            icon="book",
        )
        self.product = Product.objects.create(
            category=self.category,
            name="A4 Notebook",
            brand="Sample Brand",
            price=Decimal("100.00"),
            discount_price=Decimal("90.00"),
            stock=8,
        )
        self.customer = User.objects.create_user(
            username="customer",
            password="strong-test-password",
            first_name="Test Customer",
        )
        self.other_customer = User.objects.create_user(
            username="other-customer",
            password="strong-test-password",
        )

    def test_empty_catalogue_uses_non_purchasable_samples(self):
        self.product.delete()

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["using_dummy_content"])
        self.assertTrue(response.context["featured_products"][0].is_dummy)
        self.assertEqual(Product.objects.count(), 0)

    def test_active_database_product_replaces_sample_catalogue(self):
        response = self.client.get(reverse("product_list"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["using_dummy_content"])
        self.assertEqual(list(response.context["products"]), [self.product])
        self.assertFalse(getattr(response.context["products"][0], "is_dummy", False))

    def test_inactive_products_do_not_replace_sample_catalogue(self):
        self.product.is_active = False
        self.product.save(update_fields=["is_active"])

        response = self.client.get(reverse("product_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["using_dummy_content"])
        self.assertTrue(response.context["products"][0].is_dummy)

    def test_guest_direct_order_reduces_stock(self):
        response = self.client.post(
            reverse("order_product", args=[self.product.id]),
            {
                "name": "Guest Customer",
                "phone": "9876543210",
                "address": "10 Test Road, Delhi",
                "delivery_pincode": "110001",
                "quantity": 2,
                "payment_method": "COD",
            },
        )

        self.assertRedirects(response, reverse("order_success"))
        self.product.refresh_from_db()
        order = Order.objects.get()
        self.assertEqual(self.product.stock, 6)
        self.assertIsNone(order.customer)
        self.assertEqual(order.quantity, 2)
        self.assertEqual(order.total_price(), Decimal("180.00"))
        movement = InventoryMovement.objects.get(order=order)
        self.assertEqual(movement.quantity_delta, -2)
        self.assertEqual(movement.reason, "SALE")
        self.assertIsNone(movement.actor)
        movement.note = "Changed by test"
        with self.assertRaises(ValidationError):
            movement.save()
        with self.assertRaises(ValidationError):
            movement.delete()
        event = OrderStatusEvent.objects.get(order=order)
        self.assertEqual(event.from_status, "")
        self.assertEqual(event.to_status, "PENDING")
        self.assertEqual(event.note, "Order placed")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_guest_can_receive_order_updates_by_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("order_product", args=[self.product.id]),
                {
                    "name": "Guest Customer",
                    "phone": "9876543210",
                    "customer_email": "guest@example.com",
                    "address": "10 Test Road, Delhi",
                    "delivery_pincode": "110001",
                    "quantity": 1,
                    "payment_method": "COD",
                },
            )

        self.assertRedirects(response, reverse("order_success"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["guest@example.com"])

    def test_order_price_and_product_details_are_snapshotted(self):
        response = self.client.post(
            reverse("order_product", args=[self.product.id]),
            {
                "name": "Guest Customer",
                "phone": "9876543210",
                "address": "10 Test Road, Delhi",
                "delivery_pincode": "110001",
                "quantity": 2,
                "payment_method": "COD",
            },
        )
        self.assertRedirects(response, reverse("order_success"))
        order = Order.objects.get()

        self.product.name = "Updated Notebook"
        self.product.brand = "Updated Brand"
        self.product.price = Decimal("150.00")
        self.product.discount_price = Decimal("125.00")
        self.category.name = "Updated Category"
        self.category.save(update_fields=["name"])
        self.product.save(update_fields=["name", "brand", "price", "discount_price"])

        order.refresh_from_db()
        self.assertEqual(order.product_name_snapshot, "A4 Notebook")
        self.assertEqual(order.product_brand_snapshot, "Sample Brand")
        self.assertEqual(order.product_category_snapshot, "Notebooks")
        self.assertEqual(order.unit_price_snapshot, Decimal("90.00"))
        self.assertEqual(order.total_price(), Decimal("180.00"))

    def test_product_with_order_history_cannot_be_deleted(self):
        Order.objects.create(
            customer=self.customer,
            name="Test Customer",
            phone="9876543210",
            address="10 Test Road, Delhi",
            product=self.product,
            quantity=1,
        )

        with self.assertRaises(ProtectedError):
            self.product.delete()

    def test_upi_order_starts_pending_and_can_be_marked_verified(self):
        order = Order.objects.create(
            customer=self.customer,
            name="Test Customer",
            phone="9876543210",
            address="10 Test Road, Delhi",
            product=self.product,
            quantity=1,
            payment_method="UPI",
        )
        self.assertEqual(order.payment_status, "PENDING")

        missing_reference_form = OrderStatusForm(
            {
                "status": "PENDING",
                "admin_note": "",
                "payment_status": "PAID",
                "transaction_reference": "",
                "refund_reference": "",
                "refund_amount": "0",
            },
            instance=order,
        )
        self.assertFalse(missing_reference_form.is_valid())
        self.assertIn("transaction_reference", missing_reference_form.errors)

        verified_form = OrderStatusForm(
            {
                "status": "PENDING",
                "admin_note": "",
                "payment_status": "PAID",
                "transaction_reference": "UPI-TXN-123",
                "refund_reference": "",
                "refund_amount": "0",
            },
            instance=order,
        )
        self.assertTrue(verified_form.is_valid(), verified_form.errors)
        verified_order = verified_form.save()
        self.assertIsNotNone(verified_order.paid_at)
        self.assertEqual(verified_order.transaction_reference, "UPI-TXN-123")

    def test_refund_requires_verified_payment_and_valid_refund_reference(self):
        order = Order.objects.create(
            customer=self.customer,
            name="Test Customer",
            phone="9876543210",
            address="10 Test Road, Delhi",
            product=self.product,
            quantity=1,
            payment_method="UPI",
        )
        order.payment_status = "PAID"
        order.transaction_reference = "UPI-TXN-123"
        order.save()

        refund_form = OrderStatusForm(
            {
                "status": "PENDING",
                "admin_note": "",
                "payment_status": "PARTIALLY_REFUNDED",
                "transaction_reference": "UPI-TXN-123",
                "refund_reference": "REF-TXN-456",
                "refund_amount": "25.00",
            },
            instance=order,
        )
        self.assertTrue(refund_form.is_valid(), refund_form.errors)
        refunded_order = refund_form.save()
        self.assertEqual(refunded_order.refund_amount, Decimal("25.00"))
        self.assertEqual(refunded_order.refund_reference, "REF-TXN-456")
        self.assertIsNotNone(refunded_order.refunded_at)

    def test_dispatch_requires_carrier_or_tracking_and_records_timestamp(self):
        order = Order.objects.create(
            customer=self.customer,
            name="Test Customer",
            phone="9876543210",
            address="10 Test Road, Delhi",
            product=self.product,
            quantity=1,
        )
        form_data = {
            "status": "OUT_FOR_DELIVERY",
            "admin_note": "",
            "payment_status": "UNPAID",
            "transaction_reference": "",
            "refund_reference": "",
            "refund_amount": "0",
            "carrier_name": "",
            "tracking_number": "",
        }
        invalid_form = OrderStatusForm(form_data, instance=order)
        self.assertFalse(invalid_form.is_valid())
        self.assertIn("tracking_number", invalid_form.errors)

        form_data["carrier_name"] = "Delhi Stationery Van"
        form_data["tracking_number"] = "DS-TRACK-101"
        valid_form = OrderStatusForm(form_data, instance=order)
        self.assertTrue(valid_form.is_valid(), valid_form.errors)
        dispatched_order = valid_form.save()
        self.assertIsNotNone(dispatched_order.dispatched_at)
        self.assertEqual(dispatched_order.tracking_number, "DS-TRACK-101")

    def test_direct_order_cannot_exceed_available_stock(self):
        response = self.client.post(
            reverse("order_product", args=[self.product.id]),
            {
                "name": "Guest Customer",
                "phone": "9876543210",
                "address": "10 Test Road, Delhi",
                "delivery_pincode": "110001",
                "quantity": 9,
                "payment_method": "COD",
            },
        )

        self.assertRedirects(
            response,
            reverse("order_product", args=[self.product.id]),
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertFalse(Order.objects.exists())

    def test_cart_checkout_consumes_stock_and_clears_cart(self):
        self.client.login(username="customer", password="strong-test-password")
        session = self.client.session
        session["cart"] = {str(self.product.id): {"quantity": 3}}
        session.save()

        response = self.client.post(
            reverse("cart_checkout"),
            {
                "name": "Test Customer",
                "phone": "9876543210",
                "address": "10 Test Road, Delhi",
                "delivery_pincode": "110001",
                "payment_method": "COD",
            },
        )

        self.assertRedirects(response, reverse("order_success"))
        self.product.refresh_from_db()
        order = Order.objects.get()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.quantity, 3)
        self.assertEqual(self.client.session.get("cart"), {})
        movement = InventoryMovement.objects.get(order=order)
        self.assertEqual(movement.quantity_delta, -3)
        self.assertEqual(movement.reason, "SALE")
        self.assertEqual(movement.actor, self.customer)
        history_response = self.client.get(reverse("my_orders"))
        self.assertContains(history_response, "Status history")
        self.assertContains(history_response, "Order placed")

    def test_checkout_snapshots_serviceable_zone_fee(self):
        DeliveryZone.objects.create(
            name="Central Delhi",
            pincode="110001",
            delivery_fee=Decimal("25.00"),
            estimated_days=1,
        )
        self.client.login(username="customer", password="strong-test-password")
        session = self.client.session
        session["cart"] = {str(self.product.id): {"quantity": 2}}
        session.save()

        response = self.client.post(
            reverse("cart_checkout"),
            {
                "name": "Test Customer",
                "phone": "9876543210",
                "address": "10 Test Road, Delhi",
                "delivery_pincode": "110001",
                "payment_method": "COD",
            },
        )

        self.assertRedirects(response, reverse("order_success"))
        order = Order.objects.get()
        self.assertEqual(order.delivery_pincode, "110001")
        self.assertEqual(order.delivery_fee, Decimal("25.00"))
        self.assertEqual(order.items_total(), Decimal("180.00"))
        self.assertEqual(order.total_price(), Decimal("205.00"))

    def test_checkout_rejects_pincode_outside_configured_delivery_zones(self):
        DeliveryZone.objects.create(
            name="Central Delhi",
            pincode="110001",
            delivery_fee=Decimal("25.00"),
        )
        self.client.login(username="customer", password="strong-test-password")
        session = self.client.session
        session["cart"] = {str(self.product.id): {"quantity": 2}}
        session.save()

        response = self.client.post(
            reverse("cart_checkout"),
            {
                "name": "Test Customer",
                "phone": "9876543210",
                "address": "10 Test Road, Delhi",
                "delivery_pincode": "110099",
                "payment_method": "COD",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "delivery_pincode",
            "Delivery is not currently available for this PIN code.",
        )
        self.assertFalse(Order.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

    def test_checkout_rechecks_stock_and_keeps_cart_on_shortage(self):
        self.client.login(username="customer", password="strong-test-password")
        session = self.client.session
        session["cart"] = {str(self.product.id): {"quantity": 9}}
        session.save()

        response = self.client.post(
            reverse("cart_checkout"),
            {
                "name": "Test Customer",
                "phone": "9876543210",
                "address": "10 Test Road, Delhi",
                "delivery_pincode": "110001",
                "payment_method": "COD",
            },
        )

        self.assertRedirects(response, reverse("cart_detail"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertFalse(Order.objects.exists())
        self.assertEqual(
            self.client.session["cart"],
            {str(self.product.id): {"quantity": 9}},
        )

    def test_cart_checkout_requires_login(self):
        response = self.client.get(reverse("cart_checkout"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_customer_order_history_only_contains_their_orders(self):
        own_order = Order.objects.create(
            customer=self.customer,
            name="Test Customer",
            phone="9876543210",
            address="10 Test Road, Delhi",
            product=self.product,
            quantity=1,
        )
        Order.objects.create(
            customer=self.other_customer,
            name="Other Customer",
            phone="9876500000",
            address="20 Other Road, Delhi",
            product=self.product,
            quantity=1,
        )
        self.client.login(username="customer", password="strong-test-password")

        response = self.client.get(reverse("my_orders"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["orders"]), [own_order])

    def test_customer_cancellation_restores_stock(self):
        order = Order.objects.create(
            customer=self.customer,
            name="Test Customer",
            phone="9876543210",
            address="10 Test Road, Delhi",
            product=self.product,
            quantity=2,
            status="PENDING",
        )
        self.product.stock = 6
        self.product.save(update_fields=["stock"])
        self.client.login(username="customer", password="strong-test-password")

        response = self.client.post(reverse("cancel_order", args=[order.id]))

        self.assertRedirects(response, reverse("my_orders"))
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(order.status, "CANCELLED")
        movement = InventoryMovement.objects.get(order=order)
        self.assertEqual(movement.quantity_delta, 2)
        self.assertEqual(movement.reason, "CANCELLATION")
        self.assertEqual(movement.actor, self.customer)
        event = OrderStatusEvent.objects.get(order=order)
        self.assertEqual(event.from_status, "PENDING")
        self.assertEqual(event.to_status, "CANCELLED")

    def test_customer_cannot_cancel_another_customers_order(self):
        order = Order.objects.create(
            customer=self.other_customer,
            name="Other Customer",
            phone="9876500000",
            address="20 Other Road, Delhi",
            product=self.product,
            quantity=1,
        )
        self.client.login(username="customer", password="strong-test-password")

        response = self.client.post(reverse("cancel_order", args=[order.id]))

        self.assertEqual(response.status_code, 404)
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(order.status, "PENDING")

    def test_customer_profile_signal_creates_profile(self):
        self.assertTrue(
            CustomerProfile.objects.filter(user=self.customer).exists()
        )
