import streamlit as st

from frontend_api_calls import healthy
from frontend_utils import (
    add_aligned_text,
    authenticated,
    authorize_user,
    reset_session_state,
    setup_page
)

setup_page()

def render_login_page():
    if not healthy():
        st.error("Sorry, we're facing an unexpected issue on our end. Please try again later.")
        st.stop()
    
    if authenticated():
        authorize_user()
        st.warning("You will be logged out. Do you want to continue?")
        if st.button("Logout", type="primary", icon=":material/logout:", use_container_width=True):
            st.logout()
        elif st.button("Cancel", type="secondary", icon=":material/close:", use_container_width=True):
            reset_session_state()
            st.switch_page(page="pages/home.py")

    else:
        add_aligned_text(content="""
                        Welcome to Agastya International Foundation!
                        """,
                        alignment="center",
                        bold=True,
                        size=40
        )
        add_aligned_text(content="""
                        Our vision is to build a new world of tinkerers, creators, innovators, and solution-seekers who are humane, anchored and connected
                        """,
                        alignment="center",
                        bold=False,
                        size=20
        )
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        add_aligned_text(content="""
                        Please sign in to access your onboarding portal
                        """,
                        alignment="center",
                        bold=True,
                        size=30
        )
        st.markdown("<br>", unsafe_allow_html=True)
        button_cols = st.columns([1,1,1,1,1])
        with button_cols[2]:
            if st.button("Sign in with Google",type="primary", use_container_width=True):
                st.login()

if __name__ == "__main__":
    render_login_page()