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

The `render.yaml` blueprint uses a free staging web service and a small paid production web service. Free services can sleep, which makes staging slower to open. Do not connect staging to the production database or bucket. Use two Supabase projects, each owned by you: enter staging credentials only on `bfl-staging`, and production credentials only on `bfl-production`.

## Deploy BFL from the connected GitHub repository

The repository is connected to GitHub on `main`. The remaining deployment work needs accounts you control in Supabase and Render; keep all database passwords and S3 keys in those dashboards, never in chat or a Git commit.

1. **Create the staging branch.** Create `develop` from `main` in GitHub (or push a local `develop` branch). The Render blueprint expects this branch for staging. Keep `main` as the live-release branch.
2. **Create two Supabase projects.** Name them clearly, for example `bfl-staging` and `bfl-production`, under your own Supabase organization. Pick the Mumbai region for the database if you want the data close to your India-based customers; choose the nearest supported Render region (Singapore) for the app. If you prefer the app and database in the same region, choose Singapore for both. Region is chosen when creating a Supabase project, so decide before you create it. In each, create a public `product-images` Storage bucket. Public means visitors can read catalog pictures; uploads still go through Django. Generate S3 access keys for server-side uploads. The S3 credentials can access the project's buckets, so do not put them in frontend code. [Supabase regions](https://supabase.com/docs/guides/platform/regions) · [Supabase S3 authentication](https://supabase.com/docs/guides/storage/s3/authentication)
3. **Connect Render to GitHub.** In Render, authorize access to `BFL_repo`, choose **New → Blueprint**, and select this repository and its `render.yaml`. Review the two services before applying the blueprint. It creates a free `bfl-staging` web service from `develop` and a paid `bfl-production` service from `main`. Render can deploy linked repositories after the configured CI checks pass. [Render web services](https://render.com/docs/web-services) · [Render Blueprint spec](https://render.com/docs/blueprint-spec)
4. **Set each service's environment.** Render fills the service's own `RENDER_EXTERNAL_HOSTNAME` automatically, so the initial Render URL is allowed without extra setup. In Render's Environment tab, add these values independently for staging and production:

       DATABASE_URL=<that environment's Supabase Postgres connection string>
       SUPABASE_S3_BUCKET=product-images
       SUPABASE_S3_ACCESS_KEY=<that project's S3 access key>
       SUPABASE_S3_SECRET_KEY=<that project's S3 secret>
       SUPABASE_S3_ENDPOINT=https://<project-ref>.storage.supabase.co/storage/v1/s3
       SUPABASE_S3_REGION=<region shown in Supabase Storage settings>
       SUPABASE_MEDIA_DOMAIN=<project-ref>.supabase.co/storage/v1/object/public/product-images

   Keep `DJANGO_SECRET_KEY` as the independently generated value from the Blueprint. Set `DJANGO_ALLOWED_HOSTS` to any custom domain you connect (hostnames only, no `https://`). Keep the staging database, bucket, Django secret, and allowed hosts separate from production. The database URL is available from that Supabase project's **Connect** panel; use its IPv4 session pooler URL if direct Postgres IPv6 connectivity is unavailable, and keep SSL required. Supabase documents that its shared session pooler works over IPv4 on all plans. [Supabase database connection options](https://supabase.com/docs/guides/database/connecting-to-postgres)
5. **Deploy and check health.** Let each initial deploy finish. Open `https://<service-host>/health/`; it should return `{"status":"ok"}`. Then visit the storefront. If the deploy fails, inspect the Render deploy logs; common first-deploy issues are a missing environment variable, wrong Supabase region/endpoint, or an incorrect database connection string.
6. **Create the store owner account.** The production service is paid, so open its Render **Shell** after a successful deploy and run `python manage.py createsuperuser`. Render does not provide a dashboard shell for free web services. For staging, either temporarily move it to a paid plan to run the command, or run `createsuperuser` locally using the staging `DATABASE_URL` supplied as a temporary local environment variable. Never point that command at production by mistake. [Render shell access](https://render.com/docs/ssh)
7. **Test staging before public release.** Sign in at `/manage/`, add sample products following [PRODUCT_CATALOG.md](PRODUCT_CATALOG.md), check uploaded images load from the staging bucket, place a cash-on-delivery test order, and confirm inventory decreases for the selected size. Do not use real customer records for this test.
8. **Connect the public domain.** Add the domain to the production service in Render, then copy the DNS records Render gives you into Cloudflare. Once HTTPS is active, set `DJANGO_ALLOWED_HOSTS` to the domain (and `www` if used). Test checkout, order confirmation, photos, and the admin login at the domain before announcing it.

This makes staging usable for testing and production a distinct public store. New products entered in staging do not transfer to production; enter the approved catalog in production after validating your workflow, or add a carefully reviewed spreadsheet import later.

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
