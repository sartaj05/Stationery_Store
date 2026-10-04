from io import StringIO
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from store.models import (
    Category,
    DeliveryZone,
    InventoryMovement,
    Order,
    OrderStatusEvent,
    Product,
)


class SuperadminAccessTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer",
            password="strong-test-password",
        )
        self.staff = User.objects.create_user(
            username="staff",
            password="strong-test-password",
            is_staff=True,
        )
        self.superuser = User.objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="strong-test-password",
        )

    def test_anonymous_user_is_redirected_from_dashboard(self):
        response = self.client.get(reverse("superadmin_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_customer_cannot_open_dashboard(self):
        self.client.login(username="customer", password="strong-test-password")

        response = self.client.get(reverse("superadmin_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_staff_user_without_superuser_flag_cannot_open_dashboard(self):
        self.client.login(username="staff", password="strong-test-password")

        response = self.client.get(reverse("superadmin_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_superuser_can_open_dashboard(self):
        self.client.login(username="owner", password="strong-test-password")

        response = self.client.get(reverse("superadmin_dashboard"))

        self.assertEqual(response.status_code, 200)

    def test_customer_cannot_create_products(self):
        category = Category.objects.create(name="Pens", slug="pens")
        self.client.login(username="customer", password="strong-test-password")

        response = self.client.post(
            reverse("superadmin_product_create"),
            {
                "category": category.id,
                "name": "New Pen",
                "brand": "Test Brand",
                "description": "Test product",
                "price": "10.00",
                "discount_price": "",
                "stock": 5,
                "is_featured": "",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(category.products.exists())


class CustomerProfileViewTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="profile-customer",
            password="strong-test-password",
            first_name="Profile Customer",
        )
        self.client.login(
            username="profile-customer",
            password="strong-test-password",
        )

    def test_customer_can_update_profile_and_delivery_address(self):
        response = self.client.post(
            reverse("customer_profile"),
            {
                "first_name": "Riya Sharma",
                "email": "riya@example.com",
                "phone": "9876543210",
                "address": "12 Market Road",
                "city": "Delhi",
                "pincode": "110001",
                "landmark": "Near Metro Station",
            },
        )

        self.assertRedirects(response, reverse("customer_profile"))
        self.customer.refresh_from_db()
        profile = self.customer.customer_profile
        self.assertEqual(self.customer.first_name, "Riya")
        self.assertEqual(self.customer.last_name, "Sharma")
        self.assertEqual(self.customer.email, "riya@example.com")
        self.assertEqual(profile.phone, "9876543210")
        self.assertEqual(profile.pincode, "110001")
        self.assertIn("Near Metro Station", profile.full_address())

    def test_customer_profile_rejects_invalid_phone_and_pincode(self):
        response = self.client.post(
            reverse("customer_profile"),
            {
                "first_name": "Riya Sharma",
                "email": "riya@example.com",
                "phone": "123",
                "address": "12 Market Road",
                "city": "Delhi",
                "pincode": "123",
                "landmark": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "phone", "Enter a valid 10 digit mobile number.")
        self.assertFormError(response.context["form"], "pincode", "Enter a valid 6 digit pincode.")


class StoreStaffRoleTests(TestCase):
    def setUp(self):
        call_command("setup_store_roles", stdout=StringIO())
        self.category = Category.objects.create(name="Pens", slug="pens")
        self.product = Product.objects.create(
            category=self.category,
            name="Blue Pen",
            price="20.00",
            stock=3,
        )
        self.catalog_user = User.objects.create_user(
            username="catalog-staff",
            password="strong-test-password",
            is_staff=True,
        )
        self.inventory_user = User.objects.create_user(
            username="inventory-staff",
            password="strong-test-password",
            is_staff=True,
        )
        self.order_user = User.objects.create_user(
            username="order-staff",
            password="strong-test-password",
            is_staff=True,
        )
        self.support_user = User.objects.create_user(
            username="support-staff",
            password="strong-test-password",
            is_staff=True,
        )
        self.manager_user = User.objects.create_user(
            username="store-manager",
            password="strong-test-password",
            is_staff=True,
        )
        self.catalog_user.groups.add(Group.objects.get(name="Catalog Manager"))
        self.inventory_user.groups.add(Group.objects.get(name="Inventory Manager"))
        self.order_user.groups.add(Group.objects.get(name="Order Manager"))
        self.support_user.groups.add(Group.objects.get(name="Customer Support"))
        self.manager_user.groups.add(Group.objects.get(name="Store Manager"))

    def test_role_setup_command_is_idempotent_and_assigns_scoped_permissions(self):
        call_command("setup_store_roles", stdout=StringIO())

        self.assertEqual(Group.objects.count(), 7)
        self.assertTrue(self.catalog_user.has_perm("store.manage_catalog"))
        self.assertFalse(self.catalog_user.has_perm("store.manage_orders"))
        self.assertTrue(self.manager_user.has_perm("store.manage_orders"))
        self.assertTrue(self.manager_user.has_perm("store.view_store_dashboard"))

    def test_catalog_manager_can_manage_products_and_categories_only(self):
        self.client.login(
            username="catalog-staff",
            password="strong-test-password",
        )

        self.assertEqual(
            self.client.get(reverse("superadmin_product_list")).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("superadmin_category_list")).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("superadmin_order_list")).status_code,
            302,
        )
        self.assertRedirects(
            self.client.get(reverse("store_staff_home")),
            reverse("superadmin_product_list"),
        )

    def test_catalog_manager_cannot_set_stock_on_product_creation(self):
        self.client.login(
            username="catalog-staff",
            password="strong-test-password",
        )
        create_page = self.client.get(reverse("superadmin_product_create"))
        self.assertEqual(create_page.status_code, 200)
        self.assertNotContains(create_page, 'name="stock"')

        response = self.client.post(
            reverse("superadmin_product_create"),
            {
                "category": self.category.id,
                "name": "Catalog Only Product",
                "brand": "Test Brand",
                "description": "Created without inventory permission",
                "price": "10.00",
                "discount_price": "",
                "stock": 99,
                "is_featured": "",
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("superadmin_product_list"))
        product = Product.objects.get(name="Catalog Only Product")
        self.assertEqual(product.stock, 0)
        self.assertFalse(InventoryMovement.objects.filter(product=product).exists())

    def test_inventory_manager_can_restock_but_cannot_edit_catalogue(self):
        self.client.login(
            username="inventory-staff",
            password="strong-test-password",
        )

        self.assertEqual(self.client.get(reverse("superadmin_low_stock_list")).status_code, 200)
        product_list = self.client.get(reverse("superadmin_product_list"))
        self.assertEqual(product_list.status_code, 200)
        self.assertNotContains(product_list, "Add Product")
        self.assertNotContains(product_list, "✏️ Edit")
        self.assertEqual(
            self.client.get(reverse("superadmin_product_create")).status_code,
            302,
        )
        self.client.post(
            reverse("superadmin_product_restock", args=[self.product.id]),
            {"add_stock": 5, "reason": "Supplier delivery"},
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        movement = InventoryMovement.objects.get(product=self.product)
        self.assertEqual(movement.quantity_delta, 5)
        self.assertEqual(movement.reason, "RESTOCK")
        self.assertEqual(movement.actor, self.inventory_user)
        self.assertEqual(movement.note, "Supplier delivery")

    def test_inventory_manager_can_make_reasoned_manual_adjustments(self):
        self.client.login(
            username="inventory-staff",
            password="strong-test-password",
        )

        self.assertEqual(
            self.client.get(
                reverse("superadmin_product_adjust_stock", args=[self.product.id])
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("superadmin_inventory_movements")).status_code,
            200,
        )

        response = self.client.post(
            reverse("superadmin_product_adjust_stock", args=[self.product.id]),
            {"direction": "REMOVE", "quantity": 2, "reason": "Damaged in store"},
        )

        self.assertRedirects(response, reverse("superadmin_inventory_movements"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        movement = InventoryMovement.objects.get(product=self.product)
        self.assertEqual(movement.quantity_delta, -2)
        self.assertEqual(movement.reason, "ADJUSTMENT")
        self.assertEqual(movement.actor, self.inventory_user)

        self.client.post(
            reverse("superadmin_product_adjust_stock", args=[self.product.id]),
            {"direction": "REMOVE", "quantity": 5, "reason": "Damaged in store"},
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        self.assertEqual(InventoryMovement.objects.filter(product=self.product).count(), 1)

    def test_order_manager_is_limited_to_order_module(self):
        self.client.login(
            username="order-staff",
            password="strong-test-password",
        )

        self.assertEqual(
            self.client.get(reverse("superadmin_order_list")).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("superadmin_bulk_request_list")).status_code,
            302,
        )
        self.assertEqual(
            self.client.get(reverse("superadmin_delivery_zones")).status_code,
            200,
        )
        self.assertRedirects(
            self.client.get(reverse("store_staff_home")),
            reverse("superadmin_order_list"),
        )

    def test_order_manager_can_configure_delivery_zone_fees(self):
        self.client.login(
            username="order-staff",
            password="strong-test-password",
        )

        response = self.client.post(
            reverse("superadmin_delivery_zones"),
            {
                "name": "Central Delhi",
                "pincode": "110001",
                "delivery_fee": "25.00",
                "estimated_days": 1,
                "is_serviceable": "on",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("superadmin_delivery_zones"))
        zone = DeliveryZone.objects.get(pincode="110001")
        self.assertEqual(zone.delivery_fee, Decimal("25.00"))
        self.assertEqual(zone.estimated_days, 1)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_staff_order_status_change_is_logged_and_emails_customer(self):
        customer = User.objects.create_user(
            username="email-customer",
            email="customer@example.com",
            password="strong-test-password",
        )
        order = Order.objects.create(
            customer=customer,
            name="Email Customer",
            phone="9876543210",
            address="10 Test Road, Delhi",
            product=self.product,
            quantity=1,
            status="PENDING",
        )
        self.client.login(
            username="order-staff",
            password="strong-test-password",
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("superadmin_order_detail", args=[order.id]),
                {
                    "status": "CONFIRMED",
                    "admin_note": "Internal note",
                    "payment_status": "UNPAID",
                    "transaction_reference": "",
                    "refund_reference": "",
                    "refund_amount": "0",
                },
            )

        self.assertRedirects(
            response,
            reverse("superadmin_order_detail", args=[order.id]),
        )
        event = OrderStatusEvent.objects.get(order=order)
        self.assertEqual(event.from_status, "PENDING")
        self.assertEqual(event.to_status, "CONFIRMED")
        self.assertEqual(event.actor, self.order_user)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("order #", mail.outbox[0].subject.lower())
        self.assertEqual(mail.outbox[0].to, ["customer@example.com"])

        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                reverse("superadmin_order_detail", args=[order.id]),
                {
                    "status": "CONFIRMED",
                    "admin_note": "Follow-up note",
                    "payment_status": "UNPAID",
                    "transaction_reference": "",
                    "refund_reference": "",
                    "refund_amount": "0",
                },
            )
        self.assertEqual(OrderStatusEvent.objects.filter(order=order).count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_customer_support_can_view_but_not_change_customer_accounts(self):
        self.client.login(
            username="support-staff",
            password="strong-test-password",
        )

        customer = User.objects.create_user(
            username="managed-customer",
            password="strong-test-password",
        )
        self.assertEqual(
            self.client.get(reverse("superadmin_customer_list")).status_code,
            200,
        )
        detail_response = self.client.get(
            reverse("superadmin_customer_detail", args=[customer.id])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertNotContains(detail_response, "Deactivate Customer")
        response = self.client.post(
            reverse("superadmin_customer_toggle_status", args=[customer.id])
        )
        customer.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(customer.is_active)

    def test_store_manager_can_open_dashboard(self):
        self.client.login(
            username="store-manager",
            password="strong-test-password",
        )

        self.assertEqual(
            self.client.get(reverse("superadmin_dashboard")).status_code,
            200,
        )

    def test_customer_account_manager_can_deactivate_customers(self):
        account_manager = User.objects.create_user(
            username="account-manager",
            password="strong-test-password",
            is_staff=True,
        )
        account_manager.groups.add(
            Group.objects.get(name="Customer Account Manager")
        )
        customer = User.objects.create_user(
            username="account-to-disable",
            password="strong-test-password",
        )
        self.client.login(
            username="account-manager",
            password="strong-test-password",
        )

        response = self.client.post(
            reverse("superadmin_customer_toggle_status", args=[customer.id])
        )

        customer.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("superadmin_customer_detail", args=[customer.id]),
        )
        self.assertFalse(customer.is_active)

    def test_staff_login_redirects_to_first_allowed_workspace(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "catalog-staff",
                "password": "strong-test-password",
            },
        )

        self.assertRedirects(response, reverse("superadmin_product_list"))
