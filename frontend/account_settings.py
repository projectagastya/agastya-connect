import streamlit as st

from frontend.all_utils import add_aligned_text, switch_page

async def load_account_settings_page():
    st.sidebar.markdown("---")
    if st.sidebar.button(label="Back to Main Page", icon=":material/arrow_back:", type="primary", use_container_width=True):
        switch_page(page_name="main")
    add_aligned_text(content="Account Settings", alignment="center", size=39, bold=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("Account settings are currently disabled. Please contact the administrator for any changes.")