import html
import streamlit as st


def navigate_to(page: str, **params) -> None:
    """Navigate to a logical page and synchronize URL query parameters."""
    st.session_state["current_page"] = page
    for k, v in params.items():
        st.session_state[k] = v

    qp = {"page": page}
    if page == "products" and st.session_state.get("selected_location_id"):
        qp["loc_id"] = str(st.session_state["selected_location_id"])
    elif page == "track" and st.session_state.get("track_order_id"):
        qp["order_id"] = str(st.session_state["track_order_id"])
    elif page == "admin_edit_item" and st.session_state.get("edit_item_id"):
        qp["item_id"] = str(st.session_state["edit_item_id"])
    elif page == "admin_order_details" and st.session_state.get("selected_admin_order_id"):
        qp["order_id"] = str(st.session_state["selected_admin_order_id"])

    st.query_params.clear()
    for k, v in qp.items():
        st.query_params[k] = v
    st.rerun()


def render_brand_header(subtitle: str = "FAST Delivery · FRESH Promise", location_label: str | None = None) -> None:
    safe_sub = html.escape(subtitle)
    loc_html = (
        f'<div class="dmj-loc-pill">📍 {html.escape(location_label)}</div>'
        if location_label
        else ""
    )
    st.markdown(
        f"""
        <div class="dmj-topbar dmj-animate">
            <div class="dmj-brand-wrap">
                <div class="dmj-logo-badge">DMJ</div>
                <div>
                    <div class="dmj-brand-name">DMJ <span>Daily Bazar</span></div>
                    <div class="dmj-brand-sub">{safe_sub}</div>
                </div>
            </div>
            {loc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
