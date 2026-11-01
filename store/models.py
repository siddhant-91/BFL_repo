from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    SIZE_SYSTEMS = [
        ("alpha", "Alpha sizes — XS, S, M, L, XL"),
        ("waist", "Waist inches — 28, 30, 32, 34..."),
        ("numeric", "Numeric sizes — 38, 40, 42..."),
        ("one_size", "One size"),
        ("custom", "Custom sizes"),
    ]
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True, blank=True)
    size_system = models.CharField(max_length=16, choices=SIZE_SYSTEMS, default="alpha", help_text="Choose one size system for this product. Add a variant row for each size/color you sell.")
    description = models.TextField(blank=True)
    style = models.CharField(max_length=100, blank=True, help_text="e.g. Round neck, Collar neck, Half sleeve")
    fit = models.CharField(max_length=80, blank=True)
    material = models.CharField(max_length=120, blank=True)
    care = models.CharField(max_length=240, blank=True)
    price = models.PositiveIntegerField(help_text="Price in INR")
    compare_at_price = models.PositiveIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to="products/", blank=True)
    image_alt = models.CharField(max_length=160, blank=True)
    tags = models.CharField(max_length=240, blank=True, help_text="Comma-separated internal tags")
    featured = models.BooleanField(default=False)
    featured_order = models.PositiveSmallIntegerField(default=0, help_text="Lower numbers appear first in the homepage feature.")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-featured", "-created_at"]

    def clean(self):
        super().clean()
        if self.compare_at_price is None:
            raise ValidationError({"compare_at_price": "Enter the printed MRP for this product."})
        if self.compare_at_price <= self.price:
            raise ValidationError({"compare_at_price": "MRP must be higher than the BFL selling price to show a discount."})

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            candidate, n = base, 2
            while Product.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate, n = f"{base}-{n}", n + 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def available_variants(self):
        return self.variants.filter(active=True, stock__gt=0)

    @property
    def total_stock(self):
        return sum(v.stock for v in self.variants.filter(active=True))

    @property
    def discount_percent(self):
        if not self.compare_at_price or not self.price or self.compare_at_price <= self.price:
            return 0
        return int((self.compare_at_price - self.price) * 100 / self.compare_at_price)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=160, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.product.name} photo {self.order + 1}"

class SizeChartRow(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="size_chart_rows")
    size = models.CharField(max_length=30)
    chest = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Flat width from underarm to underarm in cm")
    shoulder = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Shoulder width in cm")
    garment_length = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Garment length in cm")
    sleeve_length = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Sleeve length in cm")
    waist = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Flat waistband width in cm")
    hip = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Flat hip width in cm")
    rise = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Rise in cm")
    inseam = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Inside leg in cm")
    foot_length = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="Foot length in cm, for socks")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "size"]
        constraints = [models.UniqueConstraint(fields=["product", "size"], name="unique_chart_size_per_product")]

    def __str__(self):
        return f"{self.product.name} size {self.size}"

class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=30, blank=True, help_text="Use One Size for accessories")
    color = models.CharField(max_length=50, blank=True)
    sku = models.CharField(max_length=80, unique=True)
    price = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank to use product price")
    stock = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True, help_text="Turn off to hide this size/color from shoppers")

    class Meta:
        ordering = ["color", "size"]

    @property
    def sale_price(self):
        return self.price if self.price is not None else self.product.price

    def __str__(self):
        details = " / ".join(x for x in [self.color, self.size] if x)
        return f"{self.product.name} — {details or self.sku}"

class Order(models.Model):
    STATUS_CHOICES = [
        ("new", "New"), ("confirmed", "Confirmed"), ("packed", "Packed"),
        ("shipped", "Shipped"), ("delivered", "Delivered"), ("cancelled", "Cancelled"),
    ]
    PAYMENT_CHOICES = [("cod", "Cash on delivery"), ("razorpay", "Online payment")]
    PAYMENT_STATUS = [("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed")]
    number = models.CharField(max_length=24, unique=True, blank=True)
    customer_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=24)
    address = models.TextField()
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    postal_code = models.CharField(max_length=12)
    notes = models.CharField(max_length=240, blank=True)
    subtotal = models.PositiveIntegerField(default=0)
    shipping = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="cod")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="pending")
    payment_id = models.CharField(max_length=100, blank=True)
    gateway_order_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.number:
            from django.utils.crypto import get_random_string
            self.number = "BFL" + get_random_string(9, allowed_chars="ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.number

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=160)
    variant_label = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=80)
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"
