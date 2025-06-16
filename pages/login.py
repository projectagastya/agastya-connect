import streamlit as st

from utils.frontend.api_calls import healthy
from utils.frontend.all import (
    add_text,
    authenticated,
    reset_session_state,
    setup_page
)
from utils.shared.errors import get_user_error
setup_page()

def render_login_page():
    if not healthy():
        st.error(get_user_error())
        st.stop()
    
    if authenticated():
        reset_session_state()
        st.switch_page(page="pages/home.py")
    else:
        st.markdown("<br><br>", unsafe_allow_html=True)
        main_2_cols = st.columns([2, 2.5, 2])
        with main_2_cols[1]:
            with st.container():
                st.markdown("<br><br>", unsafe_allow_html=True)
                add_text(content="Please sign in to access your portal",
                                alignment="center",
                                bold=True,
                                size=28)
                st.markdown(" ", unsafe_allow_html=True)
                button_cols = st.columns([2, 2.5, 2])
                with button_cols[1]:
                    if st.button("Sign in with Google", type="primary", use_container_width=True):
                        st.login()
                st.markdown("<br><br>", unsafe_allow_html=True)
                
if __name__ == "__main__":
    render_login_page()