from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("", views.home, name="home"),
    path("shop/", views.shop, name="shop"),
    path("product/<slug:slug>/", views.product_detail, name="product"),
    path("cart/", views.cart, name="cart"),
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/", views.update_cart, name="update_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/payment/<str:number>/", views.payment, name="payment"),
    path("checkout/verify/", views.verify_payment, name="verify_payment"),
    path("payments/razorpay/webhook/", views.razorpay_webhook, name="razorpay_webhook"),
    path("order/<str:number>/", views.order_confirmation, name="order_confirmation"),
    path("manage/", views.dashboard, name="dashboard"),
    path("manage/login/", views.manage_login, name="manage_login"),
    path("manage/logout/", views.manage_logout, name="manage_logout"),
    path("manage/stock/<int:variant_id>/", views.update_stock, name="update_stock"),
    path("manage/orders/<int:order_id>/status/", views.update_order_status, name="update_order_status"),
]
