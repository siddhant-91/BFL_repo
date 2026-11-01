# Deployment outline

This project is designed so the BFL owner controls the code in this repository and the Supabase organization that owns the store database and product photos. Supabase is still a hosted service and processes the data in that project; for infrastructure control without a hosted data provider, self-host Supabase on a VPS instead.

## GitHub and release workflow

The repository includes `.github/workflows/ci.yml`, `.github/dependabot.yml`, and `render.yaml`.

1. Create a **private** GitHub repository under an account or organization you control. Do not initialize it with a README if you plan to push this existing project as the first commit.
2. From the project folder, initialize `main` if needed, commit the project, add the GitHub repository as `origin`, and push `main`. Create and push `develop` from `main`. Example commands after you have the repository URL:

       git init -b main
       git add .
       git commit -m "Initial BFL storefront"
       git remote add origin <your-private-repository-url>
       git push -u origin main
       git switch -c develop
       git push -u origin develop

   Never add `.env`, `db.sqlite3`, `.venv`, uploaded media, or real customer/order exports. `.gitignore` excludes these local files. Check `git status` and the staged file list before the initial commit.
3. In GitHub repository Settings → Rules (or Branches), protect `main`: require a pull request, require the `Django checks and storefront tests` status check, and disallow force pushes/deletion. Consider requiring pull requests for `develop` as well.
4. In Render, create a Blueprint from this repository and select `render.yaml`. It defines `bfl-staging` on `develop` and `bfl-production` on `main`; automatic deployments wait for GitHub checks to pass. Add both services to your Render account and complete the environment values described below.
5. Work on `feature/...` branches from `develop`, then open PRs into `develop`. Test the deployed staging site with sample products and orders. Open a PR from `develop` to `main` to release. Production receives a deployment after CI passes and the PR is merged.

GitHub Actions currently runs migration drift checks, Django configuration checks, static collection, and the storefront test suite on pull requests and pushes to `develop`/`main`. Dependabot opens dependency and workflow update PRs for review. CI does not deploy; Render performs the deployment after checks pass.

The `render.yaml` blueprint uses a free staging web service and a paid starter production web service. Free services can sleep, which makes staging slower to open. Review Render's current plan availability and price before enabling the blueprint. Do not connect staging to the production database or bucket. Use two Supabase projects, each owned by you: enter staging credentials only on `bfl-staging`, and production credentials only on `bfl-production`.

## Login recommendation for the MVP

The existing store dashboard uses Django staff accounts. For shoppers, keep checkout available without an account and add optional customer accounts using Django's built-in authentication when customer login is implemented. This keeps password handling inside the same server-side application and avoids adding a separate auth vendor. Use Django's password hashing, CSRF protection, secure HTTPS cookies, email verification and password reset through a configured SMTP provider. Require unique staff accounts and grant staff permissions only to people who need them; use multi-factor authentication for owner/admin accounts where practical. Do not use one shared staff password.

Supabase Auth remains an option if BFL later needs a separate mobile app or external identity provider. It is not currently wired into this Django storefront. Supabase's default email sender has a low test-only rate limit, so production email login would need a custom SMTP provider. Do not store Supabase service-role keys in browser code.

## Local development

1. Install Python 3.11 or newer.
2. Create and activate a virtual environment; install requirements.txt.
3. Run python manage.py migrate.
4. Run python manage.py setup_store.
5. Run python manage.py createsuperuser for the store owner login.
6. Run python manage.py runserver.
7. Open the storefront at http://127.0.0.1:8000/ and dashboard at /manage/.

Local development uses SQLite and local image files. Production settings switch to Supabase when the corresponding environment values are set.

## Supabase production data

1. Create a Supabase project in an organization owned by BFL.
2. Copy the PostgreSQL connection string from Connect. For a persistent Django app, use the direct connection if the app host supports IPv6; otherwise use Supabase's session pooler connection string. The connection is SSL-required by this project.
3. In Storage, create a product-images bucket and make it public because customers must see catalog photography. Product uploads still go through the Django server. Generate server-side S3 access keys and keep them private.
4. Copy the Storage S3 endpoint, region, access key, and secret from Supabase's S3 configuration page. Set SUPABASE_MEDIA_DOMAIN to the public object URL prefix for that bucket, for example YOUR_PROJECT_REF.supabase.co/storage/v1/object/public/product-images.
5. Add these values to the app host's secret environment: DATABASE_URL, SUPABASE_S3_BUCKET=product-images, SUPABASE_S3_ACCESS_KEY, SUPABASE_S3_SECRET_KEY, SUPABASE_S3_ENDPOINT, SUPABASE_S3_REGION, SUPABASE_MEDIA_DOMAIN, and a long random DJANGO_SECRET_KEY.
6. Do not use the Supabase service-role or S3 secret in browser code or commit either to Git.

The app uses Django staff accounts for the owner dashboard. Supabase Auth is intentionally not in the MVP request path: the storefront and dashboard go through Django, so there is one login system and product/order writes remain server-side. It can be added later for a separate mobile app. The Supabase project dashboard remains available to the owner for backups, data export, and infrastructure settings.

Only catalog photos should go in the public Storage bucket. The browser does not receive Supabase database or S3 credentials. Django talks to Postgres and Storage from the server using secret environment variables; never expose those values in the page source. Orders contain customer contact and delivery details, so limit Django staff access to trusted people.

## App hosting and domain

Host the Django process on a persistent Python application host such as Render, Fly.io, or a VPS. Cloudflare can manage the domain's DNS and provide the public DNS/CDN layer, but it does not run this Django application as a Worker. Use a platform with durable deployments and HTTPS.

Set production environment values:

    DJANGO_DEBUG=false
    DJANGO_ALLOWED_HOSTS=shop.example.com
    DJANGO_SECRET_KEY=<long-random-secret>
    DATABASE_URL=<Supabase Postgres connection string>

For a container deployment, build from the included Dockerfile and set the app's port, DJANGO_ALLOWED_HOSTS, database, media-storage and secret variables in the hosting dashboard. The container runs migrations, ensures starter categories exist, and starts Gunicorn.

For a manual persistent-host deployment, run:

    python manage.py migrate
    python manage.py setup_store
    python manage.py collectstatic --noinput
    gunicorn bfl.wsgi:application --bind 0.0.0.0:8000

Set up the domain's TLS/HTTPS, backups, and an uptime check before accepting orders.

## Online payments

Cash on delivery works without a provider account. To enable online checkout, finish a Razorpay merchant account and add its test keys, verify the hosted checkout and webhook flow, then replace them with live keys. Configure the Razorpay webhook to call /payments/razorpay/webhook/ and subscribe to payment.captured. Live payments must not be enabled until the production domain, support contact, shipping and returns policies, and payment verification have been checked. A pending online order holds its stock until it is paid or cancelled; cancel abandoned payment attempts from the owner dashboard. The app does not issue payment refunds automatically.

## Cost shape

Use Supabase Free for staging and Supabase Pro for production. Free projects may pause after a week of low activity and have no automatic backups; Render's free web service sleeps after 15 minutes idle, so it is appropriate for staging, not a reliable public shop. Supabase Pro currently starts at $25/month, and Render's small paid web service starts at $7/month. That makes a basic always-on production setup roughly $32/month USD, plus domain, email, payment processing and any usage overages. Pricing and plan availability can change, so verify before launch. [Supabase pricing](https://supabase.com/pricing) · [Supabase free project pausing](https://supabase.com/docs/guides/platform/free-project-pausing) · [Render pricing](https://render.com/pricing) · [Render free service limits](https://render.com/docs/free)
