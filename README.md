# BFL Store

An owner-operated menswear store built with Django. The source code and store data are under your control, with no Shopify dependency.

## Local setup

Requires Python 3.11+.

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py setup_store
    python manage.py createsuperuser
    python manage.py runserver

Storefront: http://127.0.0.1:8000/  
Owner dashboard: http://127.0.0.1:8000/manage/

Cash on delivery is ready. Razorpay online checkout requires keys in environment variables. See .env.example and DEPLOYMENT.md before publishing.

## GitHub workflow

Use a private GitHub repository owned by you. Keep `main` as the public production branch and `develop` as the staging branch. Create short lived branches from `develop` for experiments, then open a pull request into `develop`. GitHub Actions runs Django checks and storefront tests on every pull request. Once merged, Render deploys the staging app after those checks pass. After reviewing staging, open a pull request from `develop` to `main`; merging it deploys production after checks pass.

Protect `main` in GitHub: require pull requests and the `Django checks and storefront tests` check, and block force pushes and branch deletion. Protect `develop` with pull requests too if you want a review trail for experiments. The first push and GitHub/Render connection are described in DEPLOYMENT.md.

Use separate Supabase projects for staging and production. Staging is for test products, accounts and orders; do not copy real customer data there. Never commit `.env` files, database exports, uploaded customer/order data, or service keys. `.env.example` contains names and safe placeholders only.

The included Dockerfile is the production app container. It runs database migrations, creates the starter categories and starts Django behind Gunicorn. Point it at a Supabase project and persistent image storage before accepting real orders.

## Everyday owner tasks

- Add a product from the dashboard. Choose its category, enter price and details, upload the main image and any gallery photos, then add one variant row for every size/color combination with a unique SKU and stock count.
- Choose a size system on each listing (letter sizes, waist inches, numeric, one size, or custom). Add a size chart row for each sellable size; enter finished garment measurements in cm. BFL displays the matching illustrated measurement guide on the product page.
- Enter the product's printed MRP and the BFL selling price. New products require MRP to be higher than the selling price; the storefront calculates and shows the discount.
- Select “Show in homepage product banner” and set the feature order to choose which products appear in the rotating, clickable home feature. Each banner links to the product page, where shoppers choose a size before adding to bag.
- Remove one size or color from sale by setting its stock to 0 or turning off that variant. Past order records retain their product and size/color snapshot.
- Use the dashboard's quick stock form for low stock, or open the full inventory list for any SKU.
- Update order progress from the recent orders table. Cancelling an order returns its reserved units to stock. Mark a COD order delivered to record it as paid.

The launch defaults assume INR, a ₹99 delivery charge below ₹2,499, and no delivery charge at or above ₹2,499. Change BFL_SHIPPING_FEE and FREE_SHIPPING_THRESHOLD in the app environment if your policy differs. Product photos are public catalog assets; order and address data stay in the database.
