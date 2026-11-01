from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "BFL Store Management"
admin.site.site_title = "BFL Admin"
admin.site.index_title = "Manage products, stock and orders"
urlpatterns = [path("admin/", admin.site.urls), path("", include("store.urls"))]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
