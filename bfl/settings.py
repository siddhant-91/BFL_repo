import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "store",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "whitenoise.middleware.WhiteNoiseMiddleware", "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "bfl.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
 "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "bfl.wsgi.application"
database_url = os.getenv("DATABASE_URL")
DATABASES = {"default": dj_database_url.parse(database_url, conn_max_age=600, ssl_require=True) if database_url else dj_database_url.parse("sqlite:///" + str(BASE_DIR / "db.sqlite3"))}
AUTH_PASSWORD_VALIDATORS = [
 {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
 {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
 {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
 {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
if os.getenv("SUPABASE_S3_BUCKET"):
    STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": {
        "bucket_name": os.getenv("SUPABASE_S3_BUCKET"), "access_key": os.getenv("SUPABASE_S3_ACCESS_KEY"),
        "secret_key": os.getenv("SUPABASE_S3_SECRET_KEY"), "endpoint_url": os.getenv("SUPABASE_S3_ENDPOINT"),
        "region_name": os.getenv("SUPABASE_S3_REGION", "us-east-1"), "default_acl": None,
        "querystring_auth": False, "addressing_style": "path",
        "custom_domain": os.getenv("SUPABASE_MEDIA_DOMAIN") or None}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/manage/login/"
LOGIN_REDIRECT_URL = "/manage/"
LOGOUT_REDIRECT_URL = "/"
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
BFL_SHIPPING_FEE = int(os.getenv("BFL_SHIPPING_FEE", "99"))
FREE_SHIPPING_THRESHOLD = int(os.getenv("FREE_SHIPPING_THRESHOLD", "2499"))
