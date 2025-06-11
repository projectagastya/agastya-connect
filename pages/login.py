import streamlit as st

from utils.frontend.api_calls import healthy
from utils.frontend.all import (
    add_text,
    authenticated,
    reset_session_state,
    setup_page
)

setup_page()

def render_login_page():
    if not healthy():
        st.error("Sorry, we're facing an unexpected issue on our end. Please try again later.")
        st.stop()
    
    if authenticated():
        st.warning("You will be logged out. Do you want to continue?")
        if st.button("Logout", type="primary", icon=":material/logout:", use_container_width=True):
            st.logout()
        elif st.button("Cancel", type="secondary", icon=":material/close:", use_container_width=True):
            reset_session_state()
            st.switch_page(page="pages/home.py")
    else:
        add_text(
            content="Welcome to Agastya International Foundation's Instructor Training Program!",
            alignment="center",
            bold=True,
            size=36
        )
        add_text(
            content="The world's largest \"Creativity Laboratory\"",
            alignment="center",
            bold=True,
            size=24
        )
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        main_cols = st.columns(spec=[1, 1, 1], gap="medium")
        with main_cols[0]:
            with st.container(border=True, height=300):
                add_text(
                    content="Our Vision",
                    alignment="center",
                    bold=True,
                    size=28
                )
                st.markdown("<br>", unsafe_allow_html=True)
                add_text(
                    content="We aim to build a new world of tinkerers, creators, innovators, and solution-seekers who are humane, anchored and connected",
                    alignment="left",
                    bold=False,
                    size=18
                )
                st.markdown("<br>", unsafe_allow_html=True)

        with main_cols[1]:
            with st.container(border=True, height=300):
                add_text(
                    content="Our Mission",
                    alignment="center",
                    bold=True,
                    size=28
                )
                st.markdown("<br>", unsafe_allow_html=True)
                add_text(
                    content="This program is designed to help new instructors understand the learning methodology at Agastya International Foundation through AI-simulated interactions with students.",
                    alignment="left",
                    bold=False,
                    size=18
                )

        with main_cols[2]:
            with st.container(border=True, height=300):
                add_text(
                    content="What we offer",
                    alignment="center",
                    bold=True,
                    size=28
                )
                st.markdown("<br>", unsafe_allow_html=True)
                add_text(
                    content="""
                    <ul>
                        <li><strong>Interactive Learning</strong>: Practice conversations with AI-simulated students</li>
                        <li><strong>Real Scenarios</strong>: Encounter diverse student backgrounds and learning styles</li>
                    </ul>
                    """,
                    size=18
                )
    
        main_2_cols = st.columns([2, 2.5, 2])
        with main_2_cols[1]:
            with st.container():
                st.markdown("---")
                add_text(content="Please sign in to access your portal",
                                alignment="center",
                                bold=True,
                                size=28)
                st.markdown(" ", unsafe_allow_html=True)
                button_cols = st.columns([2, 2.5, 2])
                with button_cols[1]:
                    if st.button("Sign in with Google", type="primary", use_container_width=True):
                        st.login()
                st.markdown("<br>", unsafe_allow_html=True)
        
        footer_cols = st.columns([3, 1, 1, 3], gap="small")
        with footer_cols[1]:
            st.page_link("pages/terms-and-conditions.py", label="Terms & Conditions")
        with footer_cols[2]:
            st.page_link("pages/privacy-policy.py", label="Privacy Policy")
                
if __name__ == "__main__":
    render_login_page()