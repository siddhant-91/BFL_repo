import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name="Category", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=80, unique=True)), ("slug", models.SlugField(blank=True, unique=True)),
            ("order", models.PositiveSmallIntegerField(default=0)),
        ], options={"ordering": ["order", "name"], "verbose_name_plural": "categories"}),
        migrations.CreateModel(name="Order", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("number", models.CharField(blank=True, max_length=24, unique=True)), ("customer_name", models.CharField(max_length=120)),
            ("email", models.EmailField(blank=True, max_length=254)), ("phone", models.CharField(max_length=24)),
            ("address", models.TextField()), ("city", models.CharField(max_length=80)), ("state", models.CharField(max_length=80)),
            ("postal_code", models.CharField(max_length=12)), ("notes", models.CharField(blank=True, max_length=240)),
            ("subtotal", models.PositiveIntegerField(default=0)), ("shipping", models.PositiveIntegerField(default=0)),
            ("total", models.PositiveIntegerField(default=0)),
            ("status", models.CharField(choices=[("new","New"),("confirmed","Confirmed"),("packed","Packed"),("shipped","Shipped"),("delivered","Delivered"),("cancelled","Cancelled")],default="new",max_length=20)),
            ("payment_method", models.CharField(choices=[("cod","Cash on delivery"),("razorpay","Online payment")],default="cod",max_length=20)),
            ("payment_status", models.CharField(choices=[("pending","Pending"),("paid","Paid"),("failed","Failed")],default="pending",max_length=20)),
            ("payment_id", models.CharField(blank=True, max_length=100)), ("gateway_order_id", models.CharField(blank=True, max_length=100)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ], options={"ordering": ["-created_at"]}),
        migrations.CreateModel(name="Product", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=160)), ("slug", models.SlugField(blank=True, unique=True)),
            ("description", models.TextField(blank=True)), ("style", models.CharField(blank=True, max_length=100)),
            ("fit", models.CharField(blank=True, max_length=80)), ("material", models.CharField(blank=True, max_length=120)),
            ("care", models.CharField(blank=True, max_length=240)), ("price", models.PositiveIntegerField(help_text="Price in INR")),
            ("compare_at_price", models.PositiveIntegerField(blank=True, null=True)), ("image", models.ImageField(blank=True, upload_to="products/")),
            ("image_alt", models.CharField(blank=True, max_length=160)), ("tags", models.CharField(blank=True, help_text="Comma-separated internal tags", max_length=240)),
            ("featured", models.BooleanField(default=False)), ("active", models.BooleanField(default=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="products", to="store.category")),
        ], options={"ordering": ["-featured", "-created_at"]}),
        migrations.CreateModel(name="ProductImage", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("image", models.ImageField(upload_to="products/gallery/")),
            ("alt_text", models.CharField(blank=True, max_length=160)),
            ("order", models.PositiveSmallIntegerField(default=0)),
            ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="photos", to="store.product")),
        ], options={"ordering": ["order", "id"]}),
        migrations.CreateModel(name="Variant", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("size", models.CharField(blank=True, help_text="Use One Size for accessories", max_length=30)),
            ("color", models.CharField(blank=True, max_length=50)), ("sku", models.CharField(max_length=80, unique=True)),
            ("price", models.PositiveIntegerField(blank=True, help_text="Leave blank to use product price", null=True)),
            ("stock", models.PositiveIntegerField(default=0)), ("active", models.BooleanField(default=True, help_text="Turn off to hide this size/color from shoppers")),
            ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="variants", to="store.product")),
        ], options={"ordering": ["color", "size"]}),
        migrations.CreateModel(name="OrderItem", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("product_name", models.CharField(max_length=160)), ("variant_label", models.CharField(blank=True, max_length=100)),
            ("sku", models.CharField(max_length=80)), ("quantity", models.PositiveSmallIntegerField()),
            ("unit_price", models.PositiveIntegerField()),
            ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="store.order")),
            ("variant", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="store.variant")),
        ]),
    ]
