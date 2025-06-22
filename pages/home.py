import streamlit as st

from utils.frontend.all import (
    add_text,
    reset_session_state,
    security_check,
    setup_page
)
from utils.frontend.api_calls import end_all_chats
from utils.shared.errors import get_user_error
from utils.shared.logger import frontend_logger

setup_page(initial_sidebar_state="expanded")

def render_home_page():
    security_check()
    user_first_name = getattr(st.user, "given_name")
    user_last_name = getattr(st.user, "family_name")
    user_email = getattr(st.user, "email")
    user_image = getattr(st.user, "picture", "static/silhouette.png")
    login_session_id = getattr(st.user, "nonce")
    user_full_name = user_first_name + " " + user_last_name
    
    if len(st.session_state) == 0:
        reset_session_state()

    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        image_col = st.columns([1,3])
        with image_col[0]:
            st.image(image=user_image, use_container_width=True)
        with image_col[1]:
            add_text(content=user_full_name, alignment="left", bold=True, size=18)
            add_text(content=user_email, alignment="left", bold=False, size=16, color="blue", underline=True)        
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(label="Sign out", icon=":material/logout:", type="primary", use_container_width=True):
            with st.spinner("Signing out..."):
                st.cache_resource.clear()
                st.logout()
                
                try:
                    end_all_success, end_all_message = end_all_chats(
                        user_email=user_email,
                        login_session_id=login_session_id
                    )
                except Exception as e:
                    frontend_logger.error(f"render_home_page | Error: {str(e)}")
                    st.error(get_user_error())
                    st.stop()
                
                if not end_all_success:
                    frontend_logger.warning(f"render_home_page | Failed to end all chats on logout: {end_all_message}")

        st.markdown("---", unsafe_allow_html=True)

        add_text(content="You may also", alignment="center", bold=True, size=30)
        st.markdown("<br>", unsafe_allow_html=True)
        st.link_button("Volunteer", "https://www.agastya.org/agastya-volunteer-program", icon=":material/emoji_people:", use_container_width=True)
        st.link_button("Donate", "https://www.agastya.org/donate", icon=":material/attach_money:", use_container_width=True)

        st.markdown("---", unsafe_allow_html=True)

        add_text(content="Contact us", alignment="center", bold=True, size=30)
        st.markdown("<br>", unsafe_allow_html=True)
        st.link_button("Email", "mailto:info@agastya.org", icon=":material/email:", use_container_width=True)
        st.link_button("Phone", "tel:+918041124132", icon=":material/phone:", use_container_width=True)

    add_text(content=f"Hello, {user_first_name}!", alignment="center", bold=True, size=40)
    add_text(content="Welcome to your training program", alignment="center", bold=True, size=32)

    st.markdown("<br>", unsafe_allow_html=True)
    add_text(
        content="""
        At Agastya, we empower you for a bright future through engagement with AI-driven student simulations. As an instructor, you'll interact with digital avatars of students from Agastya. These AI-simulated students will provide you with real-world experiences and insights into their learning process. You can choose a student to chat with, ask questions and engage in a conversation to understand the student better.""",
        alignment="left",
        size=20
    )
    st.markdown("<br>", unsafe_allow_html=True)
    add_text(
        content="""
        We hope you enjoy the experience!
        """,
        alignment="center",
        size=20,
        bold=True
    )
    st.markdown("---", unsafe_allow_html=True)
    
    cols = st.columns([4, 2, 4], gap="medium")
    with cols[1]:
        if st.button(label="Our Students", icon=":material/arrow_outward:", type="primary", use_container_width=True):
            st.switch_page(page="pages/students.py")

if __name__ == "__main__":
    render_home_page()