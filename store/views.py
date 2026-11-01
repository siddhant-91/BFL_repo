import hashlib
import hmac
import json
import os
import urllib.request
from django.conf import settings

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, connection, transaction
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Category, Order, OrderItem, Product, Variant


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def cart_data(request):
    cart = request.session.get("cart", {})
    ids = [int(k) for k in cart if str(k).isdigit()]
    variants = {v.id: v for v in Variant.objects.select_related("product").filter(id__in=ids, active=True, product__active=True)}
    lines, count, total = [], 0, 0
    for key, raw_qty in cart.items():
        variant = variants.get(int(key)) if str(key).isdigit() else None
        if not variant or variant.stock <= 0:
            continue
        qty = max(1, min(int(raw_qty), variant.stock))
        price = variant.sale_price
        lines.append({"variant": variant, "quantity": qty, "price": price, "line_total": price * qty})
        count += qty
        total += price * qty
    return lines, count, total


def shipping_for(subtotal):
    return 0 if subtotal >= settings.FREE_SHIPPING_THRESHOLD else settings.BFL_SHIPPING_FEE


def base_context(request):
    _, cart_count, _ = cart_data(request)
    return {"categories": Category.objects.all(), "cart_count": cart_count,
            "free_shipping_threshold": settings.FREE_SHIPPING_THRESHOLD}


def home(request):
    context = base_context(request)
    context["featured"] = Product.objects.filter(active=True, featured=True).order_by("featured_order", "-created_at").prefetch_related("variants", "photos")[:8]
    context["new_arrivals"] = Product.objects.filter(active=True).prefetch_related("variants")[:8]
    return render(request, "store/home.html", context)


def shop(request):
    products = Product.objects.filter(active=True).select_related("category").prefetch_related("variants")
    category = request.GET.get("category", "")
    size = request.GET.get("size", "")
    color = request.GET.get("color", "")
    style = request.GET.get("style", "")
    fit = request.GET.get("fit", "")
    query = request.GET.get("q", "").strip()
    if category:
        products = products.filter(category__slug=category)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(tags__icontains=query))
    if size:
        products = products.filter(variants__size__iexact=size, variants__stock__gt=0, variants__active=True).distinct()
    if color:
        products = products.filter(variants__color__iexact=color, variants__stock__gt=0, variants__active=True).distinct()
    if style:
        products = products.filter(style__iexact=style)
    if fit:
        products = products.filter(fit__iexact=fit)
    return render(request, "store/shop.html", {**base_context(request), "products": products, "selected_category": category, "query": query,
        "selected_size": size, "selected_color": color, "selected_style": style, "selected_fit": fit,
        "sizes": Variant.objects.filter(active=True, stock__gt=0).exclude(size="").values_list("size", flat=True).distinct(),
        "colors": Variant.objects.filter(active=True, stock__gt=0).exclude(color="").values_list("color", flat=True).distinct(),
        "styles": Product.objects.filter(active=True).exclude(style="").values_list("style", flat=True).distinct(),
        "fits": Product.objects.filter(active=True).exclude(fit="").values_list("fit", flat=True).distinct()})


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.prefetch_related("variants", "photos", "size_chart_rows"), slug=slug, active=True)
    category_slug = product.category.slug
    chart_type = "bottoms" if category_slug == "jeans" else "accessories" if category_slug == "accessories" else "upper"
    return render(request, "store/product.html", {**base_context(request), "product": product, "variants": product.variants.filter(active=True), "chart_type": chart_type, "chart_image": f"store/size-guide-{chart_type}.svg"})


@require_POST
def add_to_cart(request):
    variant_id = request.POST.get("variant")
    quantity = max(1, min(10, int(request.POST.get("quantity", 1) or 1)))
    variant = get_object_or_404(Variant.objects.select_related("product"), id=variant_id, active=True, product__active=True)
    if variant.stock < quantity:
        messages.error(request, "That quantity is not available right now.")
        return redirect("product", slug=variant.product.slug)
    cart = request.session.get("cart", {})
    cart[str(variant.id)] = min(10, int(cart.get(str(variant.id), 0)) + quantity)
    request.session["cart"] = cart
    messages.success(request, "Added to your bag.")
    return redirect("cart")


def cart(request):
    lines, _, total = cart_data(request)
    shipping = shipping_for(total)
    return render(request, "store/cart.html", {**base_context(request), "lines": lines, "total": total, "shipping": shipping, "grand_total": total + shipping})


@require_POST
def update_cart(request):
    cart = request.session.get("cart", {})
    for key in list(cart):
        try:
            qty = int(request.POST.get("qty_" + key, 0))
        except ValueError:
            qty = 0
        if qty <= 0:
            cart.pop(key, None)
        else:
            variant = Variant.objects.filter(pk=key, active=True).first()
            if not variant or variant.stock <= 0:
                cart.pop(key, None)
            else:
                cart[key] = min(qty, variant.stock, 10)
    request.session["cart"] = cart
    return redirect("cart")


def checkout(request):
    lines, _, subtotal = cart_data(request)
    shipping = shipping_for(subtotal)
    if not lines:
        return redirect("shop")
    online_ready = bool(os.getenv("RAZORPAY_KEY_ID") and os.getenv("RAZORPAY_KEY_SECRET"))
    if request.method == "GET":
        return render(request, "store/checkout.html", {**base_context(request), "lines": lines, "subtotal": subtotal, "shipping": shipping, "grand_total": subtotal + shipping, "online_ready": online_ready})
    fields = ["customer_name", "phone", "email", "address", "city", "state", "postal_code"]
    data = {key: request.POST.get(key, "").strip() for key in fields}
    if not all(data[k] for k in ["customer_name", "phone", "address", "city", "state", "postal_code"]):
        messages.error(request, "Please fill in your name, phone, address, city, state and PIN code.")
        return render(request, "store/checkout.html", {**base_context(request), "lines": lines, "subtotal": subtotal, "shipping": shipping, "grand_total": subtotal + shipping, "online_ready": online_ready, "form_data": data})
    method = request.POST.get("payment_method", "cod")
    if method not in ("cod", "razorpay"):
        method = "cod"
    if method == "razorpay" and not online_ready:
        messages.error(request, "Online payment is not configured yet. Please choose cash on delivery.")
        return redirect("checkout")
    try:
        with transaction.atomic():
            locked = {}
            for line in lines:
                variant = Variant.objects.select_for_update().get(pk=line["variant"].pk)
                if not variant.active or variant.stock < line["quantity"]:
                    raise ValueError("A selected size just sold out. Please update your bag.")
                locked[variant.pk] = variant
            order = Order.objects.create(**data, notes=request.POST.get("notes", "").strip()[:240],
                subtotal=subtotal, shipping=shipping, total=subtotal + shipping, payment_method=method,
                payment_status="pending" if method == "razorpay" else "pending")
            for line in lines:
                v = locked[line["variant"].pk]
                OrderItem.objects.create(order=order, variant=v, product_name=v.product.name,
                    variant_label=" / ".join(x for x in [v.color, v.size] if x), sku=v.sku,
                    quantity=line["quantity"], unit_price=v.sale_price)
            for line in lines:
                v = locked[line["variant"].pk]
                v.stock -= line["quantity"]
                v.save(update_fields=["stock"])
        if method == "razorpay":
            return start_online_payment(request, order)
        request.session["cart"] = {}
        return redirect("order_confirmation", number=order.number)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("cart")


def start_online_payment(request, order):
    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    payload = json.dumps({"amount": order.total * 100, "currency": "INR", "receipt": order.number,
                          "notes": {"order_number": order.number}}).encode()
    req = urllib.request.Request("https://api.razorpay.com/v1/orders", data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    import base64
    req.add_header("Authorization", "Basic " + base64.b64encode((key_id + ":" + secret).encode()).decode())
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            gateway = json.loads(res.read())
        order.gateway_order_id = gateway["id"]
        order.save(update_fields=["gateway_order_id"])
    except Exception:
        with transaction.atomic():
            failed_order = Order.objects.select_for_update().get(pk=order.pk)
            for item in failed_order.items.filter(variant__isnull=False):
                variant = Variant.objects.select_for_update().get(pk=item.variant_id)
                variant.stock += item.quantity
                variant.save(update_fields=["stock"])
            failed_order.delete()
        messages.error(request, "Payment could not be started. Please try again or choose cash on delivery.")
        return redirect("checkout")
    return redirect("payment", number=order.number)


def payment(request, number):
    order = get_object_or_404(Order, number=number, payment_method="razorpay", payment_status="pending")
    return render(request, "store/payment.html", {**base_context(request), "order": order, "razorpay_key": os.getenv("RAZORPAY_KEY_ID", "")})


@require_POST
def verify_payment(request):
    try:
        body = json.loads(request.body)
        number = body["order_number"]
        order = Order.objects.get(number=number, payment_method="razorpay", payment_status="pending")
        payment_id, gateway_order_id, signature = body["razorpay_payment_id"], body["razorpay_order_id"], body["razorpay_signature"]
        if gateway_order_id != order.gateway_order_id:
            return JsonResponse({"error": "Order mismatch"}, status=400)
        message = (gateway_order_id + "|" + payment_id).encode()
        expected = hmac.new(os.getenv("RAZORPAY_KEY_SECRET", "").encode(), message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return JsonResponse({"error": "Payment verification failed"}, status=400)
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order.pk)
            if order.payment_status != "pending":
                return JsonResponse({"url": reverse("order_confirmation", args=[order.number])})
            order.payment_status = "paid"
            order.payment_id = payment_id
            order.save(update_fields=["payment_status", "payment_id"])
        request.session["cart"] = {}
        return JsonResponse({"url": reverse("order_confirmation", args=[order.number])})
    except (KeyError, Order.DoesNotExist, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Could not verify payment"}, status=400)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    if not secret:
        return HttpResponse(status=503)
    signature = request.headers.get("X-Razorpay-Signature", "")
    expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return HttpResponse(status=400)
    try:
        payload = json.loads(request.body)
        if payload.get("event") != "payment.captured":
            return HttpResponse(status=200)
        payment_entity = payload["payload"]["payment"]["entity"]
        gateway_order_id = payment_entity["order_id"]
        with transaction.atomic():
            order = Order.objects.select_for_update().get(gateway_order_id=gateway_order_id)
            if order.payment_status == "pending":
                if payment_entity.get("amount") != order.total * 100 or payment_entity.get("currency") != "INR":
                    return HttpResponse(status=400)
                order.payment_status = "paid"
                order.payment_id = payment_entity.get("id", "")
                order.save(update_fields=["payment_status", "payment_id"])
        return HttpResponse(status=200)
    except (KeyError, Order.DoesNotExist, ValueError):
        return HttpResponse(status=200)


def order_confirmation(request, number):
    order = get_object_or_404(Order.objects.prefetch_related("items"), number=number)
    return render(request, "store/confirmation.html", {**base_context(request), "order": order})


def manage_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username", ""), password=request.POST.get("password", ""))
        if user and user.is_staff:
            login(request, user)
            return redirect(request.GET.get("next") or "dashboard")
        messages.error(request, "Those login details didn’t work.")
    return render(request, "store/manage_login.html", base_context(request))


def manage_logout(request):
    logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    if not request.user.is_staff:
        return redirect("home")
    return render(request, "store/dashboard.html", {**base_context(request),
        "products": Product.objects.select_related("category").prefetch_related("variants"),
        "orders": Order.objects.prefetch_related("items")[:12],
        "low_stock": Variant.objects.select_related("product").filter(active=True, stock__lte=3).order_by("stock")[:12],
        "order_count": Order.objects.exclude(status="cancelled").count(),
        "sales": Order.objects.filter(payment_status="paid").aggregate(total=Sum("total"))["total"] or 0})


@login_required
@require_POST
def update_stock(request, variant_id):
    if not request.user.is_staff:
        return redirect("home")
    variant = get_object_or_404(Variant, pk=variant_id)
    try:
        stock = int(request.POST.get("stock", ""))
        if stock < 0:
            raise ValueError()
        variant.stock = stock
        variant.save(update_fields=["stock"])
        messages.success(request, f"{variant} stock updated to {stock}.")
    except ValueError:
        messages.error(request, "Enter a stock quantity of zero or more.")
    return redirect("dashboard")


@login_required
@require_POST
def update_order_status(request, order_id):
    if not request.user.is_staff:
        return redirect("home")
    order = get_object_or_404(Order, pk=order_id)
    allowed = dict(Order.STATUS_CHOICES)
    status = request.POST.get("status")
    if status in allowed and order.status != "cancelled":
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order.pk)
            if order.status == "cancelled":
                return redirect("dashboard")
            if status == "cancelled" and order.status not in ("new", "confirmed", "packed"):
                messages.error(request, "Only orders that have not shipped can be cancelled from here.")
                return redirect("dashboard")
            if status == "cancelled":
                for item in order.items.filter(variant__isnull=False):
                    variant = Variant.objects.select_for_update().get(pk=item.variant_id)
                    variant.stock += item.quantity
                    variant.save(update_fields=["stock"])
            order.status = status
            changed = ["status"]
            if status == "delivered" and order.payment_method == "cod":
                order.payment_status = "paid"
                changed.append("payment_status")
            order.save(update_fields=changed)
        messages.success(request, f"Order {order.number} marked {allowed[status].lower()}.")
    return redirect("dashboard")
