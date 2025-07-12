import streamlit as st

from utils.frontend.all import authenticated, reset_session_state

def main():
    if not authenticated():
        st.switch_page("pages/login.py")
    else:
        reset_session_state()
        st.switch_page("pages/home.py")

if __name__ == "__main__":
    main()