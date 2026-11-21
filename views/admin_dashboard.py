import html
from urllib.parse import quote
import streamlit as st
from config import CATEGORY_GROUPS
from services.authentication import is_admin_logged_in, logout_admin
from services.inventory_service import (
    get_all_locations,
    add_location,
    delete_location,
    get_all_shops,
    add_shop,
    delete_shop,
    get_all_admin_items,
    add_item,
    toggle_item_stock,
    delete_item,
)
from components.navigation import navigate_to, render_brand_header


def render_admin_dashboard_page() -> None:
    if not is_admin_logged_in():
        navigate_to("admin_login")
        return

    render_brand_header("Store Control Center · Inventory, Shops & Locations")

    h1, h2, h3, _ = st.columns([1.3, 1.2, 1.0, 2.5])
    with h1:
        if st.button("🛍️ View Storefront", use_container_width=True):
            navigate_to("locations")
    with h2:
        if st.button("🧾 Manage Orders", type="primary", use_container_width=True):
            navigate_to("admin_orders")
    with h3:
        if st.button("🚪 Logout", use_container_width=True):
            logout_admin()
            navigate_to("admin_login")

    locations = get_all_locations()
    shops = get_all_shops()
    items = get_all_admin_items()
    oos_count = sum(1 for it in items if it[7])

    # KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="dmj-kpi"><div class="dmj-kpi-label">Total Items</div><div class="dmj-kpi-val">{len(items)}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="dmj-kpi"><div class="dmj-kpi-label">Out of Stock</div><div class="dmj-kpi-val" style="color:#DC2626;">{oos_count}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="dmj-kpi"><div class="dmj-kpi-label">Active Shops</div><div class="dmj-kpi-val" style="color:#0C831F;">{len(shops)}</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="dmj-kpi"><div class="dmj-kpi-label">Locations</div><div class="dmj-kpi-val">{len(locations)}</div></div>', unsafe_allow_html=True)

    st.write("")

    tab_inv, tab_add, tab_org = st.tabs(["📦 Inventory", "➕ Add Product", "🏪 Shops & 📍 Locations"])

    # Tab 1: Inventory Management
    with tab_inv:
        inv_search = st.text_input(
            "Search inventory",
            placeholder="🔍 Quick search by product name, category, shop, or location...",
            label_visibility="collapsed",
        )
        q = (inv_search or "").strip().lower()
        filtered_items = [
            it for it in items
            if not q or q in f"{it[1]} {it[2]} {it[5] or ''} {it[6] or ''}".lower()
        ]

        st.caption(f"Showing {len(filtered_items)} of {len(items)} item(s)")

        if not filtered_items:
            st.info("No items found in your inventory database.")
        else:
            for item in filtered_items:
                item_id, name, cat, price, photo, shop_name, loc_name, is_oos = item
                img_url = photo if photo else f"https://via.placeholder.com/100x100.png?text={quote(str(name)[:10])}"
                with st.container(border=True):
                    c_img, c_info, c_price, c_stock, c_act = st.columns([0.7, 2.3, 1.0, 1.3, 1.5])
                    with c_img:
                        st.markdown(
                            f'<img class="dmj-cart-thumb" style="width:54px;height:54px;" src="{html.escape(img_url)}" '
                            'onerror="this.onerror=null;this.src=\'https://via.placeholder.com/100x100.png?text=Img\';">',
                            unsafe_allow_html=True,
                        )
                    with c_info:
                        st.markdown(f"**{name}**")
                        st.caption(f"{cat} · 🏪 {shop_name or '—'} · 📍 {loc_name or '—'}")
                    with c_price:
                        st.markdown(f"**₹{float(price):.2f}**")
                        badge = (
                            '<span class="dmj-badge dmj-badge-red">Out of Stock</span>'
                            if is_oos
                            else '<span class="dmj-badge dmj-badge-green">In Stock</span>'
                        )
                        st.markdown(badge, unsafe_allow_html=True)
                    with c_stock:
                        btn_label = "Mark In Stock" if is_oos else "Mark Out Stock"
                        if st.button(btn_label, key=f"toggle_stock_{item_id}", use_container_width=True):
                            toggle_item_stock(item_id)
                            st.rerun()
                    with c_act:
                        ac1, ac2 = st.columns(2)
                        if ac1.button("✏️ Edit", key=f"edit_btn_{item_id}", use_container_width=True):
                            navigate_to("admin_edit_item", edit_item_id=item_id)
                        if ac2.button("🗑️ Del", key=f"del_item_{item_id}", use_container_width=True):
                            delete_item(item_id)
                            st.toast(f"Deleted '{name}'")
                            st.rerun()

    # Tab 2: Add Product
    with tab_add:
        with st.container(border=True):
            st.markdown("### ➕ Add New Item to Inventory")
            main_cat = st.selectbox("Main Category", options=list(CATEGORY_GROUPS.keys()), key="add_item_main_cat")
            sub_options = [s[0] for s in CATEGORY_GROUPS[main_cat]]

            with st.form("add_item_form", clear_on_submit=True):
                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1:
                    item_name = st.text_input("Item Name *", placeholder="e.g. Organic Apples")
                with r1c2:
                    sub_cat = st.selectbox("Sub-Category (Saved as Category) *", options=sub_options)
                with r1c3:
                    price = st.number_input("Price (₹) *", min_value=0.0, step=0.5, format="%.2f")

                r2c1, r2c2 = st.columns(2)
                with r2c1:
                    photo = st.text_input("Image / Photo Link (URL)", placeholder="https://images.unsplash.com/photo-...")
                with r2c2:
                    shop_options = {sname: sid for sid, sname, _ in shops}
                    selected_shop_label = st.selectbox(
                        "Assign Shop *",
                        options=list(shop_options.keys()) if shop_options else ["No shops available"],
                        disabled=not bool(shop_options),
                    )

                if st.form_submit_button("💾 Save Item to Database", type="primary"):
                    if shop_options and add_item(item_name, sub_cat, price, photo, shop_options[selected_shop_label]):
                        st.success(f"Saved '{item_name}' under '{sub_cat}'.")
                        st.rerun()
                    else:
                        st.error("Please enter item name, category, price, and select a shop.")

    # Tab 3: Locations & Shops
    with tab_org:
        col_loc, col_shop = st.columns([1, 1.5], gap="large")

        with col_loc:
            with st.container(border=True):
                st.markdown("### 📍 Location Management")
                with st.form("add_location_form", clear_on_submit=True):
                    loc_name = st.text_input("Location Name", placeholder="e.g. Damanjodi, Sector 1")
                    if st.form_submit_button("➕ Save Location", type="primary", use_container_width=True):
                        if add_location(loc_name):
                            st.success(f"Added location '{loc_name}'.")
                            st.rerun()
                        else:
                            st.error("Location name is required.")

                st.markdown("**Existing Locations**")
                if not locations:
                    st.caption("No locations created yet.")
                for lid, lname in locations:
                    lc1, lc2 = st.columns([3.2, 1])
                    lc1.write(f"📍 {lname}")
                    if lc2.button("🗑️", key=f"del_loc_{lid}", help=f"Delete {lname} (and its shops/items)"):
                        delete_location(lid)
                        st.toast(f"Deleted location '{lname}'")
                        st.rerun()

        with col_shop:
            with st.container(border=True):
                st.markdown("### 🏪 Shop Management")
                sc_form, sc_list = st.columns(2, gap="medium")
                with sc_form:
                    st.markdown("**Add New Shop**")
                    with st.form("add_shop_form", clear_on_submit=True):
                        shop_name = st.text_input("Shop Name", placeholder="e.g. Fresh Supermarket")
                        loc_options = {lname: lid for lid, lname in locations}
                        selected_loc_label = st.selectbox(
                            "Assign Location",
                            options=list(loc_options.keys()) if loc_options else ["No locations available"],
                            disabled=not bool(loc_options),
                        )
                        if st.form_submit_button("➕ Add Shop", type="primary", use_container_width=True):
                            if loc_options and add_shop(shop_name, loc_options[selected_loc_label]):
                                st.success(f"Added shop '{shop_name}'.")
                                st.rerun()
                            else:
                                st.error("Provide a shop name and valid location.")

                with sc_list:
                    st.markdown("**Existing Shops**")
                    if not shops:
                        st.caption("No shops created yet.")
                    for sid, sname, _ in shops:
                        sl1, sl2 = st.columns([3.2, 1])
                        sl1.write(f"🏪 {sname}")
                        if sl2.button("🗑️", key=f"del_shop_{sid}", help=f"Delete {sname} (and its items)"):
                            delete_shop(sid)
                            st.toast(f"Deleted shop '{sname}'")
                            st.rerun()
