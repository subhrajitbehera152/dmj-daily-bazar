import html
import re
from urllib.parse import quote
import streamlit as st
from config import FREE_DELIVERY_THRESHOLD
from services.cart_service import get_cart_details, update_cart_item
from services.order_service import place_order
from components.navigation import navigate_to, render_brand_header


def render_cart_checkout_page() -> None:
    render_brand_header("Your Cart & Checkout")

    nav1, nav2, _ = st.columns([1.3, 1, 3])
    with nav1:
        if st.button("← Continue Shopping", use_container_width=True):
            if st.session_state.get("selected_location_id"):
                navigate_to("products")
            else:
                navigate_to("locations")
    with nav2:
        if st.button("🏠 Home", use_container_width=True):
            navigate_to("locations")

    cart = st.session_state.get("cart", {})
    cart_info = get_cart_details(cart)
    items = cart_info["items"]

    if not items:
        with st.container(border=True):
            st.markdown("### 🛒 Your cart is empty")
            st.caption("Looks like you haven't added any fresh groceries yet.")
            if st.button("Start Shopping →", type="primary"):
                navigate_to("locations")
        return

    col_items, col_checkout = st.columns([1.3, 1], gap="large")

    with col_items:
        st.markdown(f"### 🛍️ Cart Items ({cart_info['total_qty']})")
        for item in items:
            img_url = (
                item["photo"]
                if item.get("photo")
                else f"https://via.placeholder.com/120x120.png?text={quote(item['name'][:12])}"
            )
            safe_name = html.escape(item["name"])
            safe_cat = html.escape(item.get("category") or "")

            with st.container(border=True):
                c_img, c_info, c_qty, c_tot, c_del = st.columns([0.9, 2.2, 1.6, 1.0, 0.6])
                with c_img:
                    st.markdown(
                        f'<img class="dmj-cart-thumb" src="{html.escape(img_url)}" alt="{safe_name}" '
                        'onerror="this.onerror=null;this.src=\'https://via.placeholder.com/120x120.png?text=Item\';">',
                        unsafe_allow_html=True,
                    )
                with c_info:
                    st.markdown(f"**{item['name']}**")
                    st.caption(f"{safe_cat} · ₹{item['price']:.2f} each")
                    if item["is_out_of_stock"]:
                        st.markdown('<span class="dmj-badge dmj-badge-red">Out of Stock</span>', unsafe_allow_html=True)
                with c_qty:
                    q1, q2, q3 = st.columns([1, 1, 1])
                    with q1:
                        if st.button("−", key=f"cart_dec_{item['id']}", use_container_width=True):
                            res = update_cart_item(cart, item["id"], "remove")
                            st.session_state["cart"] = res["cart"]
                            st.rerun()
                    with q2:
                        st.markdown(f'<div class="dmj-qty-badge">{item["qty"]}</div>', unsafe_allow_html=True)
                    with q3:
                        if st.button("+", key=f"cart_inc_{item['id']}", type="primary", use_container_width=True):
                            res = update_cart_item(cart, item["id"], "add")
                            if res["ok"]:
                                st.session_state["cart"] = res["cart"]
                            else:
                                st.toast(res.get("error", "Out of Stock"))
                            st.rerun()
                with c_tot:
                    st.markdown(f"**₹{item['subtotal']:.2f}**")
                with c_del:
                    if st.button("🗑️", key=f"cart_rm_{item['id']}", help="Remove item", use_container_width=True):
                        res = update_cart_item(cart, item["id"], "delete")
                        st.session_state["cart"] = res["cart"]
                        st.toast(f"Removed {item['name']}")
                        st.rerun()

    with col_checkout:
        # Bill Summary Card
        st.markdown('<div class="dmj-summary-card dmj-animate">', unsafe_allow_html=True)
        st.markdown("### 🧾 Bill Details")
        delivery_str = "FREE" if cart_info["delivery_fee"] == 0 else f"₹{cart_info['delivery_fee']:.2f}"
        st.markdown(
            f"""
            <div class="dmj-bill-row"><span>Items Subtotal</span><strong>₹{cart_info['subtotal']:.2f}</strong></div>
            <div class="dmj-bill-row"><span>Delivery Fee</span><strong>{delivery_str}</strong></div>
            <div class="dmj-bill-total"><span>Total Payable</span><span>₹{cart_info['payable_total']:.2f}</span></div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(min(1.0, cart_info["subtotal"] / FREE_DELIVERY_THRESHOLD))
        if cart_info["delivery_fee"] > 0:
            rem = max(0.0, FREE_DELIVERY_THRESHOLD - cart_info["subtotal"])
            st.markdown(
                f'<div class="dmj-free-banner pending">Add ₹{rem:.2f} more for FREE Delivery!</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="dmj-free-banner">🎉 You unlocked FREE Delivery!</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")

        # Checkout Form
        with st.container(border=True):
            st.markdown("### 🚚 Delivery Details")
            same_as_mobile = st.checkbox("WhatsApp same as mobile number", value=True, key="chk_same_wa")

            with st.form("checkout_form", clear_on_submit=False):
                name = st.text_input("Full Name *", placeholder="e.g. Subhrajit Behera")
                mobile = st.text_input("Mobile Number *", placeholder="10-digit mobile number", max_chars=15)
                whatsapp = st.text_input(
                    "WhatsApp Number (Optional)",
                    placeholder="Optional",
                    disabled=same_as_mobile,
                )
                house_landmark = st.text_input(
                    "Flat / House No. / Building / Landmark *",
                    placeholder="e.g. Flat 302, Green Acres, Near City Mall",
                )
                address = st.text_input(
                    "Street Address / Area *",
                    placeholder="Street, Locality, City, Pincode",
                )

                submitted = st.form_submit_button(
                    f"✅ Place Order · ₹{cart_info['payable_total']:.2f}",
                    type="primary",
                    use_container_width=True,
                )

                if submitted:
                    clean_mobile = re.sub(r"\D", "", mobile or "")
                    if not name.strip() or not house_landmark.strip() or not address.strip():
                        st.error("Please fill in Full Name, Flat/House/Landmark, and Street Address.")
                    elif len(clean_mobile) != 10:
                        st.error("Please enter a valid 10-digit Mobile Number.")
                    else:
                        ok, result = place_order(
                            cart=cart,
                            customer_name=name,
                            house_landmark=house_landmark,
                            customer_address=address,
                            mobile=clean_mobile,
                        )
                        if ok:
                            st.session_state["cart"] = {}
                            st.session_state["last_order_number"] = result
                            st.session_state["just_placed_order"] = result
                            navigate_to("track", track_order_id=result)
                        else:
                            st.error(result)
