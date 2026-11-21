# DMJ Daily Bazar — Premium Blinkit-Style Streamlit Grocery Application

A modern, mobile-first, light-themed Streamlit grocery delivery application for **DMJ Daily Bazar**, preserving 100% of the existing SQLite database schema, business logic, customer workflows, and admin operations.

## Features Preserved & Enhanced

- **Light Blinkit-Style Storefront**: Crisp white cards, emerald green (`#0C831F`) primary CTAs, warm yellow (`#F8CB46`) brand highlights, smooth micro-animations, and responsive mobile-first layouts.
- **Location Selection**: Searchable location cards + skippable welcome intro video.
- **Product Browsing**: Prominent fixed-ratio product images, Main & Sub-Category filtering, live search, Out-of-Stock visual overlays, Blinkit-style `ADD` -> `− qty +` steppers, and Product Preview modal (`@st.dialog`).
- **Cart & Checkout**: Product thumbnails in cart, quantity adjustments, item removal, free delivery progress bar (`₹30` under `₹199`; Free at/above `₹199`), and validated checkout form.
- **Order Tracking**: 4-step visual delivery timeline, `DMJ...` order lookup (plus legacy numeric ID compatibility), bill summary, and Call/WhatsApp support links.
- **Admin Console**: Secure login, KPI summary cards, tabbed Dashboard (Inventory with thumbnails, Add Product, Shops & Locations), Edit Product with live image preview, Order Management, and Order Details with temporary Out-of-Stock recalculation and downloadable PDF invoice.

## Existing Business-Rule Notes (Preserved As-Is)

1. **Delivery Fee Threshold Difference**: Customer storefront (`cart`, `products`, `track`) and Admin Orders list apply a `₹30` delivery fee when subtotal `< ₹199` (Free at/above `₹199`). Admin Order Details (`admin_order_details.py`) preserves the original `order_details.html` temporary Out-of-Stock rule (`₹30` only when 0 items are marked OOS and original subtotal `< ₹150`).
2. **Legacy `shops.html`**: Not routed in the original Flask backend; customers browse products directly by selected location.

## Installation & Running Locally

```bash
pip install -r requirements.txt
cp .env.example .env
# Place your existing grocery.db in this folder (or set DB_NAME in .env)
streamlit run app.py
```

## Deploying to GitHub & Streamlit Community Cloud

1. Push the `grocery_streamlit/` folder contents to a GitHub repository.
2. In **Streamlit Community Cloud**, select your repository and set the main file path to `app.py`.
3. Add `DB_NAME`, `ADMIN_USER`, and `ADMIN_PASS` in **App Settings → Secrets / Environment Variables**.
