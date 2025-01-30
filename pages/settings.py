import streamlit as st

from frontend_utils import add_aligned_text

st.set_page_config(page_title="Agastya Envision", page_icon=":school:", layout="wide", initial_sidebar_state="auto")
st.logo(image="images/logo.png", size="large", icon_image="images/logo.png", link="https://www.agastya.org/")

if "login_sessions" not in st.session_state:
    st.error("You must log in to access this page.")
    if st.button(label="Log in", icon=":material/login:", type="primary"):
        st.switch_page("pages/login.py")
    st.stop()
    
st.sidebar.markdown("---")
if st.sidebar.button(label="Back to Home Page", icon=":material/home:", type="primary", use_container_width=True):
    st.switch_page("pages/home.py")
add_aligned_text(content="Account Settings", alignment="center", size=40, bold=True)
st.markdown("<br>", unsafe_allow_html=True)
cols = st.columns(spec=[1, 5, 1])
with cols[1]:
    st.info("Account settings are currently disabled. Please contact the administrator for any changes.")