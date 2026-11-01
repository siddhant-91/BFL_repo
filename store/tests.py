from django.test import TestCase
from django.urls import reverse

from .models import Category, Order, Product, SizeChartRow, Variant


class StorefrontFlowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="T-shirts", order=1)
        self.product = Product.objects.create(
            category=self.category,
            name="Test Crew Tee",
            description="A test garment for the store checks.",
            style="Round neck",
            fit="Regular",
            material="Cotton jersey",
            price=1000,
            compare_at_price=1500,
            featured=True,
            active=True,
        )
        self.variant = Variant.objects.create(
            product=self.product,
            size="M",
            color="Black",
            sku="TEST-TEE-BLK-M",
            stock=3,
            active=True,
        )
        SizeChartRow.objects.create(
            product=self.product,
            size="M",
            chest=52,
            shoulder=44,
            garment_length=70,
            sleeve_length=21,
        )

    def test_homepage_introduces_bfl_and_links_featured_product(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Good clothes.")
        self.assertContains(response, "Test Crew Tee")
        self.assertContains(response, "33% OFF")
        self.assertContains(response, reverse("product", args=[self.product.slug]))

    def test_product_page_shows_size_guide_and_discount(self):
        response = self.client.get(reverse("product", args=[self.product.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MRP ₹1500")
        self.assertContains(response, "33% OFF")
        self.assertContains(response, "Chest width")
        self.assertContains(response, "GARMENT MEASUREMENTS")
        self.assertContains(response, "Black / M")

    def test_guest_can_place_cod_order_and_stock_is_decremented(self):
        add_response = self.client.post(
            reverse("add_to_cart"),
            {"variant": self.variant.pk, "quantity": 2},
        )
        self.assertEqual(add_response.status_code, 302)

        checkout_response = self.client.post(
            reverse("checkout"),
            {
                "customer_name": "Store Test",
                "phone": "9876543210",
                "email": "buyer@example.com",
                "address": "10 Sample Road",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
                "payment_method": "cod",
            },
        )
        self.assertEqual(checkout_response.status_code, 302)
        order = Order.objects.get(customer_name="Store Test")
        self.assertEqual(order.payment_method, "cod")
        self.assertEqual(order.subtotal, 2000)
        self.assertEqual(order.shipping, 99)
        self.assertEqual(order.total, 2099)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 1)

    def test_owner_dashboard_requires_sign_in(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("manage_login"), response.url)
