import streamlit as st
from services.authentication import login_admin
from components.navigation import navigate_to, render_brand_header


def render_admin_login_page() -> None:
    render_brand_header("Admin Command Center · Sign In")

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        with st.container(border=True):
            st.markdown("### 🔐 Admin Login")
            st.caption("Sign in with your administrator credentials to manage DMJ Daily Bazar.")
            with st.form("admin_login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

                if submitted:
                    if login_admin(username, password):
                        st.success("Logged in successfully.")
                        navigate_to("admin_dashboard")
                    else:
                        st.error("Invalid credentials")

            if st.button("← Back to Storefront", use_container_width=True):
                navigate_to("locations")
