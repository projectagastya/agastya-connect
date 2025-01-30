import streamlit as st

from frontend_utils import add_aligned_text

st.set_page_config(page_title="Agastya Envision", page_icon=":school:", layout="wide", initial_sidebar_state="auto")
st.logo(image="images/logo.png", size="large", icon_image="images/logo.png", link="https://www.agastya.org/")

st.sidebar.markdown("---")
if st.sidebar.button(label="Back to Login page", icon=":material/arrow_back:", type="primary", use_container_width=True):
    st.switch_page(page="pages/login.py")

add_aligned_text(content="Password Reset", alignment="center", size=35, bold=True)
st.markdown(body="<br>", unsafe_allow_html=True)
st.info(body="Password reset is currently disabled. Please contact the administrator for any changes.")