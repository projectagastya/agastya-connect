import streamlit as st

from configure_logger import frontend_logger
from frontend_utils import setup_page, security_check, add_aligned_text

setup_page(initial_sidebar_state="collapsed")

def render_history_page():
    security_check()

    if len(st.session_state) == 0:
        st.switch_page(page="pages/home.py")

    cols = st.columns([0.9,10,1.1], gap="small")
    with cols[0]:
        if st.button(label="Back", icon=":material/arrow_back:", type="primary", disabled=st.session_state["loading_page"], use_container_width=True):
            st.switch_page(page="pages/home.py")
    
    with cols[1]:
        add_aligned_text(content="Previous Conversations", alignment="center", bold=True, size=35)

if __name__ == "__main__":
    render_history_page()
