import streamlit as st
from config import VALID_ORDER_STATUSES, FREE_DELIVERY_THRESHOLD, DELIVERY_FEE
from services.authentication import is_admin_logged_in, logout_admin
from services.order_service import get_all_admin_orders, update_order_status, delete_order
from components.navigation import navigate_to, render_brand_header


def _status_badge(status: str) -> str:
    cls_map = {
        "Completed": "dmj-badge-green",
        "In Progress": "dmj-badge-blue",
        "On the way": "dmj-badge-purple",
        "Pending": "dmj-badge-amber",
    }
    cls = cls_map.get(status, "dmj-badge-amber")
    return f'<span class="dmj-badge {cls}">● {status}</span>'


def render_admin_orders_page() -> None:
    if not is_admin_logged_in():
        navigate_to("admin_login")
        return

    render_brand_header("Order Management · Track & Fulfill Orders")

    n1, n2, _ = st.columns([1.3, 1.0, 3.5])
    with n1:
        if st.button("← Back to Dashboard", use_container_width=True):
            navigate_to("admin_dashboard")
    with n2:
        if st.button("🚪 Logout", use_container_width=True):
            logout_admin()
            navigate_to("admin_login")

    orders = get_all_admin_orders()

    pending = sum(1 for o in orders if o[5] == "Pending")
    in_prog = sum(1 for o in orders if o[5] == "In Progress")
    on_way = sum(1 for o in orders if o[5] == "On the way")
    completed = sum(1 for o in orders if o[5] == "Completed")

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.markdown(f'<div class="dmj-kpi"><div class="dmj-kpi-label">Total</div><div class="dmj-kpi-val">{len(orders)}</div></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="dmj-kpi"><div class="dmj-kpi-label">Pending</div><div class="dmj-kpi-val" style="color:#B45309;">{pending}</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="dmj-kpi"><div class="dmj-kpi-label">In Progress</div><div class="dmj-kpi-val" style="color:#1D4ED8;">{in_prog}</div></div>', unsafe_allow_html=True)
    s4.markdown(f'<div class="dmj-kpi"><div class="dmj-kpi-label">On the way</div><div class="dmj-kpi-val" style="color:#6D28D9;">{on_way}</div></div>', unsafe_allow_html=True)
    s5.markdown(f'<div class="dmj-kpi"><div class="dmj-kpi-label">Completed</div><div class="dmj-kpi-val" style="color:#0C831F;">{completed}</div></div>', unsafe_allow_html=True)

    st.write("")

    f1, f2 = st.columns([2.5, 1])
    with f1:
        search = st.text_input("Search orders", placeholder="🔍 Search order ID, customer, address, or mobile...")
    with f2:
        status_filter = st.selectbox("Filter by status", options=["All statuses"] + list(VALID_ORDER_STATUSES))

    q = (search or "").strip().lower()
    filtered = []
    for o in orders:
        haystack = f"{o[0]} {o[2]} {o[3]} {o[4] or ''}".lower()
        if q and q not in haystack:
            continue
        if status_filter != "All statuses" and o[5] != status_filter:
            continue
        filtered.append(o)

    if not filtered:
        st.info("No matching orders found.")
        return

    for order in filtered:
        order_num, date_str, cust_name, addr, mobile, status, item_count, subtotal = order
        subtotal_val = float(subtotal or 0)
        # Exact rule from orders.html: delivery_fee = 30 if subtotal < 199 else 0
        delivery_fee = DELIVERY_FEE if subtotal_val < FREE_DELIVERY_THRESHOLD else 0.0
        total_val = subtotal_val + delivery_fee

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2.3, 1.3, 1.6, 1.1])
            with c1:
                if st.button(f"#{order_num}", key=f"open_ord_{order_num}"):
                    navigate_to("admin_order_details", selected_admin_order_id=order_num)
                st.write(f"**{cust_name}** · 📞 {mobile or '—'}")
                st.caption(f"📍 {addr} · 🕒 {date_str}")
            with c2:
                st.markdown(f"**₹{total_val:.2f}** ({item_count} items)")
                st.markdown(_status_badge(status), unsafe_allow_html=True)
            with c3:
                new_status = st.selectbox(
                    "Status",
                    options=list(VALID_ORDER_STATUSES),
                    index=list(VALID_ORDER_STATUSES).index(status) if status in VALID_ORDER_STATUSES else 0,
                    key=f"ord_status_sel_{order_num}",
                    label_visibility="collapsed",
                )
                if st.button("Save Status", key=f"ord_status_save_{order_num}", type="primary", use_container_width=True):
                    ok, msg = update_order_status(order_num, new_status)
                    if ok:
                        st.toast(f"Order #{order_num} updated to {new_status}")
                        st.rerun()
                    else:
                        st.error(msg)
            with c4:
                if st.button("🗑️ Delete", key=f"ord_del_{order_num}", use_container_width=True):
                    ok, msg = delete_order(order_num)
                    if ok:
                        st.toast(f"Deleted order #{order_num}")
                        st.rerun()
                    else:
                        st.error(msg)
