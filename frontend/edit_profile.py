import streamlit as st

from frontend.all_utils import switch_page

async def load_edit_profile_page():
    if st.sidebar.button(label="Back to Main Page", icon=":material/arrow_back:", type="primary", use_container_width=True):
        switch_page(page_name="main")
    st.title("Profile editing is currently disabled")
    st.info("Please contact the administrator for any changes")