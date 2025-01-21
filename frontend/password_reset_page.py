import streamlit as st

from frontend.all_utils import switch_page

async def load_password_reset_page():
    if st.sidebar.button(label="Back to Login page", icon=":material/arrow_back:", type="primary", use_container_width=True):
        switch_page(page_name="login")

    st.title("Password reset page is currently unavailable.")