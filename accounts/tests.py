from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from store.models import Category


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
