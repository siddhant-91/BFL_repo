from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.models import inlineformset_factory
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .admin import ProductAdminForm, SizeChartInlineFormSet, VariantInlineFormSet
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


class ProductAdminContentTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="T-shirts")
        self.owner = get_user_model().objects.create_superuser(
            username="bfl-owner", email="owner@example.com", password="test-password-123"
        )
        self.client.force_login(self.owner)

    def test_product_editor_has_copy_and_image_guidance(self):
        response = self.client.get(reverse("admin:store_product_add"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Describe the feel, fabric, and details")
        self.assertContains(response, "Main product photo shown on the shop")
        self.assertContains(response, "Extra product photos (optional)")
        self.assertContains(response, "Size guide measurements")
        self.assertContains(response, "Add one row for each size and color combination you sell.")
        self.assertContains(response, "physically available in this size and color")

    def test_active_product_requires_main_photo_but_draft_can_be_saved(self):
        data = {
            "category": self.category.pk,
            "name": "Everyday Crew Tee",
            "price": 999,
            "compare_at_price": 1499,
            "size_system": "alpha",
            "featured_order": 0,
            "active": "on",
        }
        published_form = ProductAdminForm(data=data)
        self.assertFalse(published_form.is_valid())
        self.assertIn("main product photo", str(published_form.errors["image"]))

        data["active"] = ""
        draft_form = ProductAdminForm(data=data)
        self.assertTrue(draft_form.is_valid(), draft_form.errors)

    def test_active_product_accepts_uploaded_main_photo(self):
        image_bytes = BytesIO()
        Image.new("RGB", (80, 100), color="black").save(image_bytes, format="PNG")
        upload = SimpleUploadedFile("black-tee-front.png", image_bytes.getvalue(), content_type="image/png")
        form = ProductAdminForm(
            data={
                "category": self.category.pk,
                "name": "Black Crew Tee",
                "price": 999,
                "compare_at_price": 1499,
                "size_system": "alpha",
                "featured_order": 0,
                "active": "on",
            },
            files={"image": upload},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_draft_can_be_saved_before_size_stock_and_measurements_are_ready(self):
        draft = Product(
            category=self.category,
            name="Coming Soon Tee",
            price=999,
            compare_at_price=1499,
            active=False,
        )
        empty_variants = {
            "variants-TOTAL_FORMS": "0",
            "variants-INITIAL_FORMS": "0",
            "variants-MIN_NUM_FORMS": "0",
            "variants-MAX_NUM_FORMS": "1000",
        }
        empty_chart = {
            "size_chart_rows-TOTAL_FORMS": "0",
            "size_chart_rows-INITIAL_FORMS": "0",
            "size_chart_rows-MIN_NUM_FORMS": "0",
            "size_chart_rows-MAX_NUM_FORMS": "1000",
        }
        variant_formset = inlineformset_factory(
            Product, Variant, formset=VariantInlineFormSet, fields="__all__", extra=0
        )
        chart_formset = inlineformset_factory(
            Product, SizeChartRow, formset=SizeChartInlineFormSet, fields="__all__", extra=0
        )
        variants = variant_formset(empty_variants, instance=draft, prefix="variants")
        chart = chart_formset(empty_chart, instance=draft, prefix="size_chart_rows")
        self.assertTrue(variants.is_valid(), variants.errors)
        self.assertTrue(chart.is_valid(), chart.errors)

        live_product = Product(
            category=self.category,
            name="Published Tee",
            price=999,
            compare_at_price=1499,
            active=True,
        )
        live_variants = variant_formset(empty_variants, instance=live_product, prefix="variants")
        live_chart = chart_formset(empty_chart, instance=live_product, prefix="size_chart_rows")
        self.assertFalse(live_variants.is_valid())
        self.assertFalse(live_chart.is_valid())
