import html
import streamlit as st
from config import INTRO_YOUTUBE_ID, FREE_DELIVERY_THRESHOLD
from services.inventory_service import get_all_locations
from components.navigation import navigate_to, render_brand_header


def render_locations_page() -> None:
    # Preserve optional welcome intro video with immediate Skip button
    if not st.session_state.get("intro_skipped", False):
        with st.container(border=True):
            c_title, c_skip = st.columns([4, 1.2])
            with c_title:
                st.markdown("### 🎬 Welcome to DMJ Daily Bazar")
                st.caption("FAST Delivery · FRESH Promise — Your local grocery shopping starts here")
            with c_skip:
                if st.button("Skip Intro →", type="primary", use_container_width=True):
                    st.session_state["intro_skipped"] = True
                    st.rerun()

            st.markdown(
                f"""
                <div style="position:relative;padding-bottom:42%;height:0;overflow:hidden;border-radius:14px;background:#0F172A;">
                    <iframe
                        src="https://www.youtube.com/embed/{INTRO_YOUTUBE_ID}?autoplay=1&mute=1&controls=0&rel=0&modestbranding=1&playsinline=1"
                        style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
                        allow="autoplay; encrypted-media; picture-in-picture"
                        allowfullscreen>
                    </iframe>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("Tap **Skip Intro →** above at any time to choose your delivery location.")
            return

    render_brand_header("FAST Delivery · FRESH Promise")

    # Blinkit-style Hero Banner (using only real DMJ Daily Bazar service rules)
    st.markdown(
        f"""
        <div class="dmj-hero dmj-animate">
            <div class="dmj-hero-tag">⚡ DMJ Daily Bazar</div>
            <h1>Fresh groceries from your neighborhood shops</h1>
            <p>Select your delivery location below to browse fresh vegetables, fruits, dairy, meats, and daily essentials.</p>
            <div class="dmj-hero-pills">
                <span class="dmj-hero-pill">🥬 Fresh Vegetables & Fruits</span>
                <span class="dmj-hero-pill">🚚 Free Delivery on ₹{int(FREE_DELIVERY_THRESHOLD)}+</span>
                <span class="dmj-hero-pill">⚡ Fast Local Dispatch</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Search & Quick Actions Bar
    c_search, c_track, c_admin = st.columns([3.2, 1.1, 1.1])
    with c_search:
        search_term = st.text_input(
            "Search locations",
            placeholder="🔍 Search your neighborhood or city...",
            label_visibility="collapsed",
            key="location_search_input",
        )
    with c_track:
        if st.button("📦 Track Order", use_container_width=True):
            navigate_to("track")
    with c_admin:
        if st.button("⚙️ Admin", use_container_width=True):
            navigate_to("admin_dashboard")

    locations = get_all_locations()
    term = (search_term or "").strip().lower()
    filtered = [loc for loc in locations if not term or term in loc[1].lower()]

    st.markdown(f"**Available Delivery Locations** · Showing {len(filtered)} of {len(locations)}")

    if not filtered:
        st.warning("No locations found. Try searching for a different area or neighborhood.")
        return

    cols = st.columns(3)
    for idx, (loc_id, loc_name) in enumerate(filtered):
        safe_loc = html.escape(str(loc_name))
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div class="dmj-loc-card dmj-animate">
                    <div class="dmj-loc-icon">📍</div>
                    <div class="dmj-loc-title">{safe_loc}</div>
                    <div class="dmj-loc-sub">Explore local shops & fresh groceries</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Shop in {loc_name} →", key=f"loc_btn_{loc_id}", type="primary", use_container_width=True):
                navigate_to("products", selected_location_id=loc_id, selected_location_name=loc_name)
