import hmac
import streamlit as st
from config import ADMIN_USER, ADMIN_PASS


def verify_admin_credentials(username: str, password: str) -> bool:
    return hmac.compare_digest(username or "", ADMIN_USER) and hmac.compare_digest(password or "", ADMIN_PASS)


def is_admin_logged_in() -> bool:
    return bool(st.session_state.get("admin_logged_in", False))


def login_admin(username: str, password: str) -> bool:
    if verify_admin_credentials(username, password):
        st.session_state["admin_logged_in"] = True
        return True
    return False


def logout_admin() -> None:
    st.session_state["admin_logged_in"] = False
