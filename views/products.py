import html
import streamlit as st
from config import CATEGORY_GROUPS, MAIN_CATEGORY_ICONS, FREE_DELIVERY_THRESHOLD
from services.inventory_service import get_items_by_location, get_all_locations
from services.cart_service import get_cart_details
from components.navigation import navigate_to, render_brand_header
from components.product_card import render_product_card


def _normalize(val: str) -> str:
    return " ".join((val or "").lower().strip().replace("&", "and").split())


def render_products_page() -> None:
    loc_id = st.session_state.get("selected_location_id")
    if not loc_id:
        navigate_to("locations")
        return

    loc_name = st.session_state.get("selected_location_name")
    if not loc_name:
        for lid, lname in get_all_locations():
            if lid == int(loc_id):
                loc_name = lname
                st.session_state["selected_location_name"] = lname
                break

    render_brand_header(
        subtitle="FAST Delivery · FRESH Promise",
        location_label=loc_name or f"Location #{loc_id}",
    )

    cart_info = get_cart_details(st.session_state.get("cart", {}))

    # Top Action & Search Bar
    c_search, c_loc, c_cart = st.columns([3.4, 1.1, 1.4])
    with c_search:
        search_query = st.text_input(
            "Search items",
            placeholder="🔍 Search for vegetables, rice, milk, paneer, snacks...",
            label_visibility="collapsed",
            key="product_search_query",
        )
    with c_loc:
        if st.button("📍 Locations", use_container_width=True):
            navigate_to("locations")
    with c_cart:
        cart_label = (
            f"🛒 {cart_info['total_qty']} · ₹{cart_info['payable_total']:.0f}"
            if cart_info["total_qty"] > 0
            else "🛒 Cart (0)"
        )
        if st.button(cart_label, type="primary", use_container_width=True, key="top_cart_btn"):
            navigate_to("cart")

    # Quick Cart Strip when items are in cart (especially helpful on mobile)
    if cart_info["total_qty"] > 0:
        if cart_info["delivery_fee"] == 0:
            strip_sub = "🎉 FREE Delivery unlocked!"
        else:
            rem = max(0.0, FREE_DELIVERY_THRESHOLD - cart_info["subtotal"])
            strip_sub = f"Add ₹{rem:.2f} more for FREE delivery"

        st.markdown(
            f"""
            <div class="dmj-mobile-cart-strip dmj-animate">
                <div>
                    <div style="font-weight:800;font-size:0.95rem;">
                        🛍️ {cart_info['total_qty']} item(s) · ₹{cart_info['payable_total']:.2f}
                    </div>
                    <div style="font-size:0.78rem;opacity:0.92;">{html.escape(strip_sub)}</div>
                </div>
                <div style="font-weight:800;font-size:0.84rem;background:rgba(255,255,255,0.2);padding:6px 12px;border-radius:999px;">
                    Tap Cart ↑ to Checkout
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    categories = get_items_by_location(int(loc_id), search_query=search_query)

    # Map sub-categories into the 6 main categories (exact match to original app)
    sub_to_main = {}
    for main_cat, subs in CATEGORY_GROUPS.items():
        for sub_name, _ in subs:
            sub_to_main[_normalize(sub_name)] = main_cat

    grouped_main: dict[str, dict[str, list]] = {m: {} for m in CATEGORY_GROUPS}
    other_categories: dict[str, list] = {}

    for cat_name, items in categories.items():
        main_cat = sub_to_main.get(_normalize(cat_name))
        if main_cat:
            grouped_main[main_cat][cat_name] = items
        else:
            other_categories[cat_name] = items

    # Two-column layout: Product Catalog + Order Summary Card
    col_products, col_summary = st.columns([3.2, 1.15], gap="large")

    with col_summary:
        st.markdown('<div class="dmj-summary-card dmj-animate">', unsafe_allow_html=True)
        st.markdown("#### 🧾 Order Summary")
        st.markdown(
            f"""
            <div class="dmj-bill-row"><span>Items</span><strong>{cart_info['total_qty']}</strong></div>
            <div class="dmj-bill-row"><span>Subtotal</span><strong>₹{cart_info['subtotal']:.2f}</strong></div>
            <div class="dmj-bill-row"><span>Delivery Fee</span><strong>{'FREE' if cart_info['delivery_fee'] == 0 and cart_info['subtotal'] > 0 else f"₹{cart_info['delivery_fee']:.2f}"}</strong></div>
            <div class="dmj-bill-total"><span>Total</span><span>₹{cart_info['payable_total']:.2f}</span></div>
            """,
            unsafe_allow_html=True,
        )

        progress_ratio = min(1.0, cart_info["subtotal"] / FREE_DELIVERY_THRESHOLD) if FREE_DELIVERY_THRESHOLD > 0 else 1.0
        st.progress(progress_ratio)

        if cart_info["subtotal"] == 0:
            st.markdown('<div class="dmj-free-banner pending">Add items to start your order</div>', unsafe_allow_html=True)
        elif cart_info["delivery_fee"] == 0:
            st.markdown('<div class="dmj-free-banner">🎉 You unlocked FREE delivery!</div>', unsafe_allow_html=True)
        else:
            rem = max(0.0, FREE_DELIVERY_THRESHOLD - cart_info["subtotal"])
            st.markdown(
                f'<div class="dmj-free-banner pending">Add ₹{rem:.2f} more for FREE delivery</div>',
                unsafe_allow_html=True,
            )

        st.write("")
        if st.button("Proceed to Checkout →", type="primary", use_container_width=True, key="sidebar_checkout_btn"):
            navigate_to("cart")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_products:
        if not categories:
            st.info("No products found for this location or search query.")
            return

        available_mains = [m for m, subs in grouped_main.items() if subs]
        if other_categories:
            available_mains.append("Other Categories")

        filter_options = ["All"] + available_mains
        selected_main = st.radio(
            "Category",
            options=filter_options,
            horizontal=True,
            format_func=lambda m: f"{MAIN_CATEGORY_ICONS.get(m, '✨' if m == 'All' else '📦')} {m}",
            label_visibility="collapsed",
            key="selected_main_category",
        )

        st.divider()

        for main_cat in available_mains:
            if selected_main != "All" and selected_main != main_cat:
                continue

            if main_cat == "Other Categories":
                for cat_name, items in other_categories.items():
                    st.markdown(f"#### 📦 {cat_name} ({len(items)})")
                    grid = st.columns(3)
                    for idx, item in enumerate(items):
                        with grid[idx % 3]:
                            render_product_card(item, key_prefix=f"other_{cat_name}")
                continue

            subs_dict = grouped_main[main_cat]
            icon = MAIN_CATEGORY_ICONS.get(main_cat, "🛒")
            st.markdown(f"### {icon} {main_cat}")

            sub_names = list(subs_dict.keys())
            if len(sub_names) > 1:
                sub_filter = st.radio(
                    f"{main_cat} sections",
                    options=["All"] + sub_names,
                    horizontal=True,
                    label_visibility="collapsed",
                    key=f"sub_filter_{main_cat}",
                )
            else:
                sub_filter = "All"

            for sub_name, items in subs_dict.items():
                if sub_filter != "All" and sub_filter != sub_name:
                    continue
                st.markdown(f"**{sub_name}** · {len(items)} item(s)")
                grid = st.columns(3)
                for idx, item in enumerate(items):
                    with grid[idx % 3]:
                        render_product_card(item, key_prefix=f"sub_{sub_name}")
