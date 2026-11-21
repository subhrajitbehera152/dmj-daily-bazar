import streamlit as st
from database import init_db
from components.styles import inject_styles
from views.locations import render_locations_page
from views.products import render_products_page
from views.cart_checkout import render_cart_checkout_page
from views.tracking import render_tracking_page
from views.admin_login import render_admin_login_page
from views.admin_dashboard import render_admin_dashboard_page
from views.admin_edit_item import render_admin_edit_item_page
from views.admin_orders import render_admin_orders_page
from views.admin_order_details import render_admin_order_details_page

st.set_page_config(
    page_title="DMJ Daily Bazar — Online Grocery",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Non-destructive DB initialization & Blinkit-style light CSS injection
init_db()
inject_styles()

# Session state defaults
st.session_state.setdefault("cart", {})
st.session_state.setdefault("admin_logged_in", False)
st.session_state.setdefault("intro_skipped", False)

# Query param routing support (?page=track&order_id=DMJ...)
qp = st.query_params
if "current_page" not in st.session_state:
    st.session_state["current_page"] = qp.get("page", "locations")

if "loc_id" in qp and qp.get("page") == "products":
    try:
        st.session_state["selected_location_id"] = int(qp["loc_id"])
    except ValueError:
        pass
if "order_id" in qp and qp.get("page") == "track":
    st.session_state["track_order_id"] = qp["order_id"]
if "item_id" in qp and qp.get("page") == "admin_edit_item":
    try:
        st.session_state["edit_item_id"] = int(qp["item_id"])
    except ValueError:
        pass
if "order_id" in qp and qp.get("page") == "admin_order_details":
    st.session_state["selected_admin_order_id"] = qp["order_id"]

ROUTES = {
    "locations": render_locations_page,
    "products": render_products_page,
    "cart": render_cart_checkout_page,
    "track": render_tracking_page,
    "admin_login": render_admin_login_page,
    "admin_dashboard": render_admin_dashboard_page,
    "admin_edit_item": render_admin_edit_item_page,
    "admin_orders": render_admin_orders_page,
    "admin_order_details": render_admin_order_details_page,
}

current_page = st.session_state.get("current_page", "locations")
renderer = ROUTES.get(current_page, render_locations_page)
renderer()
