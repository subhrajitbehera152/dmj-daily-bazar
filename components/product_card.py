import html
from urllib.parse import quote
import streamlit as st
from services.cart_service import update_cart_item


def _resolve_image_url(photo: str | None, name: str) -> str:
    if photo and str(photo).strip():
        return str(photo).strip()
    return f"https://via.placeholder.com/400x300.png?text={quote(str(name)[:24])}"


@st.dialog("Product Details")
def show_product_zoom_modal(item: tuple) -> None:
    item_id, name, category, price, photo, is_out_of_stock = item
    img_url = _resolve_image_url(photo, name)
    safe_name = html.escape(str(name))
    safe_cat = html.escape(str(category))

    oos_cls = "is-oos" if is_out_of_stock else ""
    oos_badge = '<div class="dmj-oos-overlay"><span class="dmj-oos-pill">Out of Stock</span></div>' if is_out_of_stock else ""

    st.markdown(
        f"""
        <div class="dmj-prod-img-wrap {oos_cls}" style="height:260px;">
            <img class="dmj-prod-img" src="{html.escape(img_url)}" alt="{safe_name}"
                 onerror="this.onerror=null;this.src='https://via.placeholder.com/400x300.png?text=No+Image';">
            {oos_badge}
        </div>
        <span class="dmj-prod-cat">{safe_cat}</span>
        <h3 style="margin:4px 0 6px 0;font-weight:800;color:#1C2434;">{safe_name}</h3>
        <div style="font-size:1.35rem;font-weight:800;color:#0C831F;margin-bottom:14px;">₹{float(price):.2f}</div>
        """,
        unsafe_allow_html=True,
    )

    if is_out_of_stock:
        st.error("This product is currently out of stock.")
        return

    cart = st.session_state.get("cart", {})
    qty = int(cart.get(str(item_id), 0))

    if qty == 0:
        if st.button("＋ Add to Cart", key=f"modal_add_{item_id}", type="primary", use_container_width=True):
            res = update_cart_item(cart, item_id, "add")
            if res["ok"]:
                st.session_state["cart"] = res["cart"]
                st.toast(f"Added {name} to cart")
            else:
                st.toast(res.get("error", "Out of Stock"))
            st.rerun()
    else:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("−", key=f"modal_dec_{item_id}", use_container_width=True):
                res = update_cart_item(cart, item_id, "remove")
                st.session_state["cart"] = res["cart"]
                st.rerun()
        with c2:
            st.markdown(f'<div class="dmj-qty-badge">{qty}</div>', unsafe_allow_html=True)
        with c3:
            if st.button("+", key=f"modal_inc_{item_id}", type="primary", use_container_width=True):
                res = update_cart_item(cart, item_id, "add")
                if res["ok"]:
                    st.session_state["cart"] = res["cart"]
                else:
                    st.toast(res.get("error", "Out of Stock"))
                st.rerun()


def render_product_card(item: tuple, key_prefix: str = "prod") -> None:
    item_id, name, category, price, photo, is_out_of_stock = item
    img_url = _resolve_image_url(photo, name)
    safe_name = html.escape(str(name))
    safe_cat = html.escape(str(category))
    cart = st.session_state.get("cart", {})
    qty = int(cart.get(str(item_id), 0))

    oos_cls = "is-oos" if is_out_of_stock else ""
    oos_overlay = (
        '<div class="dmj-oos-overlay"><span class="dmj-oos-pill">Out of Stock</span></div>'
        if is_out_of_stock
        else ""
    )
    stock_html = (
        '<span class="dmj-badge dmj-badge-red" style="font-size:0.68rem;padding:2px 7px;">Unavailable</span>'
        if is_out_of_stock
        else '<span class="dmj-stock-dot">● In Stock</span>'
    )

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="dmj-animate">
                <div class="dmj-prod-img-wrap {oos_cls}">
                    <img class="dmj-prod-img" loading="lazy" src="{html.escape(img_url)}" alt="{safe_name}"
                         onerror="this.onerror=null;this.src='https://via.placeholder.com/400x300.png?text=No+Image';">
                    {oos_overlay}
                </div>
                <span class="dmj-prod-cat">{safe_cat}</span>
                <div class="dmj-prod-title" title="{safe_name}">{safe_name}</div>
                <div class="dmj-prod-price-row">
                    <div class="dmj-prod-price">₹{float(price):.2f}</div>
                    {stock_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if is_out_of_stock:
            st.button("Out of Stock", key=f"{key_prefix}_oos_{item_id}", disabled=True, use_container_width=True)
        elif qty == 0:
            c_add, c_zoom = st.columns([3.2, 1])
            with c_add:
                if st.button("ADD", key=f"{key_prefix}_add_{item_id}", type="primary", use_container_width=True):
                    res = update_cart_item(cart, item_id, "add")
                    if res["ok"]:
                        st.session_state["cart"] = res["cart"]
                        st.toast(f"✓ Added {name}")
                    else:
                        st.toast(res.get("error", "Out of Stock"))
                    st.rerun()
            with c_zoom:
                if st.button("🔍", key=f"{key_prefix}_zoom_{item_id}", help="Preview product", use_container_width=True):
                    show_product_zoom_modal(item)
        else:
            b1, b2, b3, b4 = st.columns([1, 1.1, 1, 0.9])
            with b1:
                if st.button("−", key=f"{key_prefix}_dec_{item_id}", use_container_width=True):
                    res = update_cart_item(cart, item_id, "remove")
                    st.session_state["cart"] = res["cart"]
                    st.toast(f"Updated {name}")
                    st.rerun()
            with b2:
                st.markdown(f'<div class="dmj-qty-badge">{qty}</div>', unsafe_allow_html=True)
            with b3:
                if st.button("+", key=f"{key_prefix}_inc_{item_id}", type="primary", use_container_width=True):
                    res = update_cart_item(cart, item_id, "add")
                    if res["ok"]:
                        st.session_state["cart"] = res["cart"]
                        st.toast(f"✓ {name} ({res['qty']})")
                    else:
                        st.toast(res.get("error", "Out of Stock"))
                    st.rerun()
            with b4:
                if st.button("🔍", key=f"{key_prefix}_zoom_{item_id}", help="Preview product", use_container_width=True):
                    show_product_zoom_modal(item)
