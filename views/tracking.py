import html
from urllib.parse import quote
import streamlit as st
from config import SUPPORT_PHONE, SUPPORT_DISPLAY_PHONE, TRACK_AD_YOUTUBE_ID
from services.order_service import get_tracking_order
from components.navigation import navigate_to, render_brand_header


def render_tracking_page() -> None:
    render_brand_header("Order Tracking · Live Status Updates")

    n1, n2, _ = st.columns([1.2, 1.2, 3])
    with n1:
        if st.button("🏠 Home", use_container_width=True):
            navigate_to("locations")
    with n2:
        if st.button("🛍️ Continue Shopping", use_container_width=True):
            navigate_to("locations")

    order_ref = st.session_state.get("track_order_id") or st.session_state.get("last_order_number") or ""
    lookup_col, btn_col = st.columns([3.2, 1])
    with lookup_col:
        entered_ref = st.text_input(
            "Order Number",
            value=str(order_ref),
            placeholder="Enter your DMJ order number (e.g. DMJ...)",
            label_visibility="collapsed",
        )
    with btn_col:
        if st.button("Track Order", type="primary", use_container_width=True):
            st.session_state["track_order_id"] = entered_ref.strip()
            st.rerun()

    target_ref = (entered_ref or "").strip()
    if not target_ref:
        st.info("Enter your Order Number above to view order status and details.")
        return

    order, items = get_tracking_order(target_ref)
    if not order:
        st.error("Order not found. Please check your order number and try again.")
        return

    # Order confirmation banner if just placed
    if st.session_state.get("just_placed_order") == order["order_number"]:
        st.success(f"🎉 Order **#{order['order_number']}** placed successfully! Tap **WhatsApp Support** below to confirm your location for faster delivery.")
        st.session_state["just_placed_order"] = None

    # Exact status step mapping from track.html
    order_status_lower = (order.get("status") or "Order Placed").lower()
    current_step = 0
    if any(k in order_status_lower for k in ("confirm", "process", "prepar")):
        current_step = 1
    elif any(k in order_status_lower for k in ("ready", "picked", "transit", "ship", "out for delivery", "on the way")):
        current_step = 2
    elif any(k in order_status_lower for k in ("deliver", "complete")):
        current_step = 3

    # Build WhatsApp support message (exact match to track.html)
    wa_lines = [
        f"- {it['name']} x {it['quantity']} (₹{it['subtotal']:.2f})"
        for it in items
    ]
    wa_items_str = "\n" + "\n".join(wa_lines) if wa_lines else "\nItem details not available"
    wa_message = (
        f"Hello, I need help with my order.\n\n"
        f"Order Number: #{order['order_number']}\n\n"
        f"Items:{wa_items_str}\n\n"
        f"Total Cost: ₹{order['total']:.2f}"
    )
    wa_url = f"https://wa.me/{SUPPORT_PHONE}?text={quote(wa_message)}"

    # Delivery Progress Card
    with st.container(border=True):
        b1, b2 = st.columns([3, 1.2])
        with b1:
            st.caption("ORDER NUMBER")
            st.markdown(f"## #{order['order_number']}")
        with b2:
            st.markdown(
                f"<div style='text-align:right;padding-top:10px;'>"
                f"<span class='dmj-badge dmj-badge-green'>● {html.escape(order['status'])}</span></div>",
                unsafe_allow_html=True,
            )

        steps = [
            ("🧾", "Order Placed"),
            ("📦", "Preparing"),
            ("🚲", "On the way"),
            ("🏠", "Delivered"),
        ]
        timeline_html = '<div class="dmj-timeline">'
        for i, (ico, lbl) in enumerate(steps):
            cls = "done" if i < current_step else ("current" if i == current_step else "")
            icon_show = "✓" if i < current_step else ico
            timeline_html += (
                f'<div class="dmj-step {cls}">'
                f'<div class="dmj-step-circle">{icon_show}</div>'
                f'<div class="dmj-step-label">{lbl}</div>'
                f"</div>"
            )
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)
        st.progress((current_step + 1) / 4)

        messages = {
            3: "Your order has been marked as delivered. Thank you for shopping with DMJ Daily Bazar!",
            2: "Your order is on its way. Contact support below if you need any delivery assistance.",
            1: "Your order is being prepared. Updates will appear here as your order progresses.",
            0: "Your order has been received. Next updates will appear here when your order status changes.",
        }
        st.info(messages[current_step])

    col_left, col_right = st.columns([1.3, 1], gap="large")

    with col_left:
        with st.container(border=True):
            st.markdown("### 🛍️ Items in your order")
            if items:
                table_data = [
                    {
                        "Item": it["name"],
                        "Qty": it["quantity"],
                        "Price": f"₹{it['price']:.2f}",
                        "Total": f"₹{it['subtotal']:.2f}",
                    }
                    for it in items
                ]
                st.table(table_data)
            else:
                st.info("Item details have not been provided for this order.")

            st.markdown("### 🧾 Payment Summary")
            fee_txt = "FREE" if order["delivery_fee"] == 0 and order["subtotal"] > 0 else f"₹{order['delivery_fee']:.2f}"
            st.markdown(
                f"""
                <div class="dmj-bill-row"><span>Items Subtotal</span><strong>₹{order['subtotal']:.2f}</strong></div>
                <div class="dmj-bill-row"><span>Delivery Fee</span><strong>{fee_txt}</strong></div>
                <div class="dmj-bill-total"><span>Total Payable</span><span>₹{order['total']:.2f}</span></div>
                <div class="dmj-bill-row" style="margin-top:6px;"><span>Payment Method</span><strong>{html.escape(order['payment_method'])}</strong></div>
                """,
                unsafe_allow_html=True,
            )

    with col_right:
        with st.container(border=True):
            st.markdown("### 📍 Delivery Address")
            st.write(f"**Customer:** {order['name'] or 'Not provided'}")
            st.write(f"**Mobile:** {order['mobile'] or 'Not provided'}")
            st.write(f"**Address:** {order['address'] or 'Not provided'}")
            st.caption(f"Placed on: {order['date']}")

        with st.container(border=True):
            st.markdown("### 🛵 Support & Delivery Help")
            st.caption("FAST Delivery · FRESH Promise — Tap below to call or share your location on WhatsApp.")
            st.markdown(
                f"""
                <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;">
                    <a class="dmj-call-btn" href="tel:+{SUPPORT_PHONE}">📞 Call Support</a>
                    <a class="dmj-wa-btn" href="{wa_url}" target="_blank" rel="noopener noreferrer">💬 WhatsApp Support</a>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.container(border=True):
            st.markdown("### 📺 Featured")
            st.markdown(
                f"""
                <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:12px;">
                    <iframe
                        src="https://www.youtube.com/embed/{TRACK_AD_YOUTUBE_ID}?autoplay=1&mute=1&loop=1&playlist={TRACK_AD_YOUTUBE_ID}&controls=0&rel=0&modestbranding=1&playsinline=1"
                        style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
                        allow="autoplay; encrypted-media; picture-in-picture"
                        allowfullscreen>
                    </iframe>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.caption(f"Need help with your order? Contact support team {SUPPORT_DISPLAY_PHONE}.")
