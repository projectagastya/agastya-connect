import streamlit as st

from frontend.all_utils import add_aligned_text, switch_page

async def load_password_reset_page():
    st.sidebar.markdown("---")
    if st.sidebar.button(label="Back to Login page", icon=":material/arrow_back:", type="primary", use_container_width=True):
        switch_page(page_name="login")

    add_aligned_text(content="Password Reset", alignment="center", size=39, bold=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("Password reset is currently disabled. Please contact the administrator for any changes.")