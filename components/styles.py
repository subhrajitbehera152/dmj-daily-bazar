import os
import streamlit as st

_CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "css", "blinkit_theme.css")


def inject_styles() -> None:
    try:
        with open(_CSS_PATH, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except OSError:
        pass
