import re
from urllib.parse import quote
import streamlit as st
from config import (
    VALID_ORDER_STATUSES,
    ADMIN_DETAIL_DELIVERY_THRESHOLD,
    ADMIN_DETAIL_DELIVERY_FEE,
)
from services.authentication import is_admin_logged_in, logout_admin
from services.order_service import (
    get_admin_order_details,
    update_order_status,
    delete_order,
    generate_order_pdf_bytes,
)
from components.navigation import navigate_to, render_brand_header


def render_admin_order_details_page() -> None:
    if not is_admin_logged_in():
        navigate_to("admin_login")
        return

    order_ref = st.session_state.get("selected_admin_order_id")
    if not order_ref:
        navigate_to("admin_orders")
        return

    order, items = get_admin_order_details(str(order_ref))
    if not order:
        st.error("Order not found.")
        if st.button("← Back to All Orders"):
            navigate_to("admin_orders")
        return

    order_num, cust_name, addr, mobile, date_str, status = order
    render_brand_header(f"Order #{order_num} · Order Details")

    n1, n2, n3, _ = st.columns([1.2, 1.2, 1.0, 2.5])
    with n1:
        if st.button("← All Orders", use_container_width=True):
            navigate_to("admin_orders")
    with n2:
        if st.button("🏠 Dashboard", use_container_width=True):
            navigate_to("admin_dashboard")
    with n3:
        if st.button("🚪 Logout", use_container_width=True):
            logout_admin()
            navigate_to("admin_login")

    # Customer Info
    with st.container(border=True):
        st.markdown("### 👤 Customer Information")
        c1, c2, c3, c4 = st.columns(4)
        c1.write(f"**Customer Name**\n\n{cust_name}")
        c2.write(f"**Mobile Number**\n\n{mobile or 'Not provided'}")
        c3.write(f"**Order Date**\n\n{date_str}")
        c4.write(f"**Order Reference**\n\n#{order_num}")
        st.write(f"**Delivery Address:** {addr}")

    # Status Update
    with st.container(border=True):
        st.markdown("### ⚙️ Update Order Status")
        sc1, sc2 = st.columns([2, 1])
        with sc1:
            selected_status = st.selectbox(
                "Order Status",
                options=list(VALID_ORDER_STATUSES),
                index=list(VALID_ORDER_STATUSES).index(status) if status in VALID_ORDER_STATUSES else 0,
                key=f"detail_status_{order_num}",
            )
        with sc2:
            st.write("")
            st.write("")
            if st.button("Save Status", type="primary", use_container_width=True, key=f"detail_save_{order_num}"):
                ok, msg = update_order_status(order_num, selected_status)
                if ok:
                    st.success(f"Status updated to {selected_status}")
                    st.rerun()
                else:
                    st.error(msg)

    # Page-only temporary Out-of-Stock toggle (exact match to order_details.html)
    oos_state_key = f"admin_oos_items_{order_num}"
    if oos_state_key not in st.session_state:
        st.session_state[oos_state_key] = set()
    oos_indices: set[int] = st.session_state[oos_state_key]

    with st.container(border=True):
        st.markdown("### 🛒 Order Items")
        st.caption("Mark any unavailable product as out of stock (temporary calculation, not saved to database).")

        original_subtotal = 0.0
        deduction = 0.0
        available_qty = 0

        for idx, item in enumerate(items):
            item_name, qty, unit_price, sub = item
            sub_val = float(sub or 0)
            qty_val = int(qty or 0)
            original_subtotal += sub_val
            is_oos = idx in oos_indices
            if is_oos:
                deduction += sub_val
            else:
                available_qty += qty_val

            ic1, ic2, ic3, ic4, ic5 = st.columns([2.5, 0.8, 1, 1, 1.5])
            with ic1:
                if is_oos:
                    st.markdown(f"~~{item_name}~~  \n`OUT OF STOCK — deducted`")
                else:
                    st.markdown(f"**{item_name}**")
            ic2.write(f"x{qty_val}")
            ic3.write(f"₹{float(unit_price or 0):.2f}")
            ic4.write(f"**₹{sub_val:.2f}**")
            with ic5:
                btn_txt = "Restore Item" if is_oos else "Mark Out of Stock"
                if st.button(btn_txt, key=f"oos_toggle_{order_num}_{idx}", use_container_width=True):
                    if is_oos:
                        oos_indices.discard(idx)
                    else:
                        oos_indices.add(idx)
                    st.session_state[oos_state_key] = oos_indices
                    st.rerun()

        adjusted_subtotal = max(0.0, original_subtotal - deduction)
        # Exact delivery rule from original order_details.html:
        # No items marked OOS and originalSubtotal < 150 -> ₹30 delivery fee; otherwise Free.
        delivery_fee = (
            ADMIN_DETAIL_DELIVERY_FEE
            if len(oos_indices) == 0 and original_subtotal < ADMIN_DETAIL_DELIVERY_THRESHOLD
            else 0.0
        )
        grand_total = adjusted_subtotal + delivery_fee

        st.divider()
        fee_label = "Free" if delivery_fee == 0 else f"₹{delivery_fee:.2f}"
        st.markdown(
            f"""
            <div class="dmj-bill-row"><span>Available item quantity</span><strong>{available_qty}</strong></div>
            <div class="dmj-bill-row"><span>Original items subtotal</span><strong>₹{original_subtotal:.2f}</strong></div>
            <div class="dmj-bill-row"><span>Out-of-stock deduction</span><strong style="color:#DC2626;">−₹{deduction:.2f}</strong></div>
            <div class="dmj-bill-row"><span>Adjusted items subtotal</span><strong>₹{adjusted_subtotal:.2f}</strong></div>
            <div class="dmj-bill-row"><span>Delivery fee</span><strong>{fee_label}</strong></div>
            <div class="dmj-bill-total"><span>Adjusted Grand Total</span><span style="color:#0C831F;">₹{grand_total:.2f}</span></div>
            """,
            unsafe_allow_html=True,
        )

    summary = {
        "original_subtotal": original_subtotal,
        "deduction": deduction,
        "adjusted_subtotal": adjusted_subtotal,
        "delivery_fee": delivery_fee,
        "grand_total": grand_total,
    }
    pdf_bytes = generate_order_pdf_bytes(order, items, oos_indices, summary)

    wa_digits = re.sub(r"\D", "", str(mobile or ""))
    if len(wa_digits) == 10:
        wa_digits = "91" + wa_digits

    a1, a2, a3 = st.columns([1.5, 1.5, 1])
    with a1:
        st.download_button(
            "📄 Download Order PDF",
            data=pdf_bytes,
            file_name=f"Order-{order_num}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )
    with a2:
        if wa_digits:
            msg = quote(f"Order #{order_num} PDF is ready. Adjusted Grand Total: ₹{grand_total:.2f}")
            st.markdown(
                f'<a class="dmj-wa-btn" style="width:100%;" href="https://wa.me/{wa_digits}?text={msg}" target="_blank">💬 Open Customer WhatsApp</a>',
                unsafe_allow_html=True,
            )
    with a3:
        if st.button("🗑️ Delete Order", use_container_width=True):
            ok, msg = delete_order(order_num)
            if ok:
                st.toast(f"Order #{order_num} deleted.")
                navigate_to("admin_orders")
            else:
                st.error(msg)
