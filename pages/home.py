import streamlit as st

from configure_logger import frontend_logger
from frontend_utils import (
    add_aligned_text,
    reset_session_state,
    security_check,
    setup_page
)

setup_page(initial_sidebar_state="expanded")

def render_home_page():
    security_check()
    if hasattr(st.experimental_user, "given_name"):
        user_first_name = getattr(st.experimental_user, "given_name")
    else:
        frontend_logger.error("render_home_page | User first name not found in user object")
        st.error("Sorry, we're facing an unexpected internal issue. Please contact support")
        st.stop()
    if hasattr(st.experimental_user, "family_name"):
        user_last_name = getattr(st.experimental_user, "family_name")
    else:
        frontend_logger.error("render_home_page | User last name not found in user object")
        st.error("Sorry, we're facing an unexpected internal issue. Please contact support")
        st.stop()
    if hasattr(st.experimental_user, "email"):
        user_email = getattr(st.experimental_user, "email")
    else:
        frontend_logger.error("render_home_page | User email not found in user object")
        st.error("Sorry, we're facing an unexpected internal issue. Please contact support")
        st.stop()
    if hasattr(st.experimental_user, "picture"):
        user_image = getattr(st.experimental_user, "picture", "static/silhouette.png")
    else:
        frontend_logger.error("render_home_page | User image not found in user object")
        st.error("Sorry, we're facing an unexpected internal issue. Please contact support")
        st.stop()
    
    user_full_name = user_first_name + " " + user_last_name
    
    if len(st.session_state) == 0:
        reset_session_state()

    with st.sidebar:
        add_aligned_text(content="My Profile", alignment="center", bold=True, size=30)
        st.markdown("<br>", unsafe_allow_html=True)
        image_col = st.columns([1,3])
        with image_col[0]:
            st.image(image=user_image, use_container_width=True)
        with image_col[1]:
            add_aligned_text(content=user_full_name, alignment="left", bold=True, size=18)
            add_aligned_text(content=user_email, alignment="left", bold=False, size=16, color="blue", underline=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(label="Logout", icon=":material/logout:", type="primary", use_container_width=True):
            st.cache_resource.clear()
            st.logout()

        st.markdown("---", unsafe_allow_html=True)
        add_aligned_text(content="Contact us", alignment="center", bold=True, size=30)
        st.markdown("<br>", unsafe_allow_html=True)
        contact_cols = st.columns(2)
        with contact_cols[0]:
            st.link_button("Email", "mailto:info@agastya.org", icon=":material/email:", use_container_width=True)

        with contact_cols[1]:
            st.link_button("Phone", "tel:+918041124132", icon=":material/phone:", use_container_width=True)
        
        st.markdown("---", unsafe_allow_html=True)
        add_aligned_text(content="You may also", alignment="center", bold=True, size=30)
        st.markdown("<br>", unsafe_allow_html=True)
        other_cols = st.columns(2)
        with other_cols[0]:
            st.link_button("Volunteer", "https://www.agastya.org/agastya-volunteer-program", icon=":material/emoji_people:", use_container_width=True)
        with other_cols[1]:
            st.link_button("Donate", "https://www.agastya.org/donate", icon=":material/attach_money:", use_container_width=True)

    add_aligned_text(content=f"Hello, {user_first_name}!", alignment="center", bold=True, size=40)
    add_aligned_text(content="Welcome to your instructor training program", alignment="center", bold=True, size=32)
    add_aligned_text(content="At Agastya International Foundation, we empower you for a bright future through engagement with AI-driven student simulations", alignment="center", size=20)
    st.markdown("<br>", unsafe_allow_html=True)
    add_aligned_text(content="On the next page, you'll interact with digital avatars of students from Agastya International Foundation.", alignment="center", size=20)
    add_aligned_text(content="You can ask questions and engage in a conversation to understand the student better.", alignment="center", size=20)
    st.markdown("<br>", unsafe_allow_html=True)
    add_aligned_text(content="We hope you enjoy the experience!", alignment="center", size=20)
    st.markdown("---", unsafe_allow_html=True)
    
    cols = st.columns([4, 4], gap="medium")
    with cols[0]:
        add_aligned_text(content="Chat with a student", alignment="center", bold=True, size=32)
        st.markdown("<br>", unsafe_allow_html=True)
        subcols = st.columns([3,4,3])
        with subcols[1]:
            if st.button(label="Get Started", icon=":material/arrow_outward:", type="primary", use_container_width=True):
                st.switch_page(page="pages/selection.py")
    with cols[1]:
        add_aligned_text(content="Past Conversations", alignment="center", bold=True, size=32)
        st.markdown("<br>", unsafe_allow_html=True)
        subcols = st.columns([3,4,3])
        with subcols[1]:
            if st.button(label="History", icon=":material/history:", type="secondary", use_container_width=True, disabled=True, help="Coming soon"):
                st.switch_page(page="pages/history.py")

if __name__ == "__main__":
    render_home_page()