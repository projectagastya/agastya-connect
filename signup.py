import streamlit as st

from utils import switch_page

def load_signup_page():
    st.title("Page under construction")

    if st.button("I want to login", type="primary"):
        switch_page("login")