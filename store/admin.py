from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from .models import Category, Product, ProductImage, SizeChartRow, Variant, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "order")

class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price"].label = "BFL selling price (₹)"
        self.fields["price"].help_text = "The price the customer pays."
        self.fields["compare_at_price"].label = "MRP printed on the product (₹)"
        self.fields["compare_at_price"].required = True
        self.fields["featured"].label = "Show in homepage product banner"

class VariantInlineFormSet(BaseInlineFormSet):
    SIZE_OPTIONS = {
        "alpha": ["XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL"],
        "waist": ["26", "28", "30", "32", "34", "36", "38", "40", "42", "44"],
        "numeric": ["36", "38", "40", "42", "44", "46", "48", "50", "52"],
        "one_size": ["One Size"],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = getattr(type(self), "request", None)
        posted_scheme = request.POST.get("size_system") if request and request.method == "POST" else None
        scheme = posted_scheme or getattr(self.instance, "size_system", "alpha")
        self.selected_size_system = scheme
        self.base_price = getattr(self.instance, "price", None)
        self.product_mrp = getattr(self.instance, "compare_at_price", None)
        if request and request.method == "POST":
            try:
                self.base_price = int(request.POST.get("price") or 0)
                self.product_mrp = int(request.POST.get("compare_at_price") or 0)
            except ValueError:
                pass
        options = self.SIZE_OPTIONS.get(scheme, [])
        for form in self.forms:
            form.fields["size"].required = True
            if options:
                current = getattr(form.instance, "size", "")
                choices = [("", "Choose a size")] + [(size, size) for size in options]
                if current and current not in options:
                    choices.append((current, current))
                form.fields["size"].widget = forms.Select(choices=choices)

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        options = self.SIZE_OPTIONS.get(getattr(self, "selected_size_system", "custom"))
        if not options:
            return
        variant_sizes = set()
        for data in self.cleaned_data:
            if data and not data.get("DELETE"):
                size = data.get("size")
                if not size and any(data.get(field) for field in ("sku", "color", "stock")):
                    raise ValidationError("Every product variant needs a size. Choose One size for accessories.")
                if size and size not in options:
                    raise ValidationError("Use sizes from the selected size system for every variant.")
                if size:
                    variant_sizes.add(size)
                variant_price = data.get("price") or self.base_price
                if getattr(self, "validate_variants", True) and self.product_mrp and variant_price and variant_price >= self.product_mrp:
                    raise ValidationError("A variant's selling price must be below the product MRP.")
        if not getattr(self, "validate_variants", True):
            return
        if not variant_sizes:
            raise ValidationError("Add at least one size/color variant before publishing this product.")
        request = getattr(type(self), "request", None)
        chart_sizes = set()
        if request and request.method == "POST":
            try:
                total = int(request.POST.get("size_chart_rows-TOTAL_FORMS", 0))
            except ValueError:
                total = 0
            for i in range(total):
                if not request.POST.get(f"size_chart_rows-{i}-DELETE"):
                    chart_size = request.POST.get(f"size_chart_rows-{i}-size", "").strip()
                    if chart_size:
                        chart_sizes.add(chart_size)
        elif self.instance.pk:
            chart_sizes = set(self.instance.size_chart_rows.values_list("size", flat=True))
        missing = variant_sizes - chart_sizes
        if missing:
            raise ValidationError("Add a size guide measurement row for each sellable size: " + ", ".join(sorted(missing)))

class SizeChartInlineFormSet(VariantInlineFormSet):
    validate_variants = False
    REQUIRED_MEASUREMENTS = {
        "jeans": ("waist", "hip", "rise", "inseam"),
        "accessories": ("foot_length",),
    }

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        request = getattr(type(self), "request", None)
        category = None
        if request and request.method == "POST":
            category = Category.objects.filter(pk=request.POST.get("category")).first()
        if not category and getattr(self.instance, "category_id", None):
            category = self.instance.category
        fields = self.REQUIRED_MEASUREMENTS.get(category.slug if category else "", ("chest", "shoulder", "garment_length", "sleeve_length"))
        rows = [row for row in self.cleaned_data if row and not row.get("DELETE") and row.get("size")]
        if not rows:
            raise ValidationError("Add a size guide measurement row for every sellable size.")
        for row in rows:
            missing = [field.replace("_", " ") for field in fields if row.get(field) is None]
            if missing:
                raise ValidationError(f"Size {row['size']}: enter " + ", ".join(missing) + " measurements in cm.")

class SizeChartInline(admin.TabularInline):
    model = SizeChartRow
    extra = 1
    fields = ("size", "chest", "shoulder", "garment_length", "sleeve_length", "waist", "hip", "rise", "inseam", "foot_length", "order")
    verbose_name = "size measurement row"
    verbose_name_plural = "Size guide measurements (cm, measured on the garment)"
    formset = SizeChartInlineFormSet

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.request = request
        return formset

class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    fields = ("size", "color", "sku", "price", "stock", "active")
    formset = VariantInlineFormSet

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.request = request
        return formset

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ("name", "category", "price", "compare_at_price", "total_stock", "active", "featured")
    list_filter = ("category", "active", "featured")
    search_fields = ("name", "tags", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, SizeChartInline, VariantInline]
    fieldsets = (
        ("Product", {"fields": ("name", "slug", "category", "description", "image", "image_alt")}),
        ("Details & sizing", {"fields": ("style", "fit", "material", "care", "size_system", "tags")}),
        ("Pricing & homepage", {"fields": ("price", "compare_at_price", "featured", "featured_order", "active")}),
    )

    class Media:
        js = ("store/admin_product.js",)

@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "color", "size", "stock", "active")
    list_filter = ("active", "color", "product__category")
    search_fields = ("sku", "product__name", "color", "size")
    list_editable = ("stock", "active")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "variant_label", "sku", "quantity", "unit_price")
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "customer_name", "phone", "total", "status", "payment_method", "payment_status", "created_at")
    list_filter = ("status", "payment_method", "payment_status", "created_at")
    search_fields = ("number", "customer_name", "phone", "email")
    readonly_fields = ("number", "subtotal", "shipping", "total", "payment_id", "gateway_order_id", "created_at", "status")
    inlines = [OrderItemInline]
