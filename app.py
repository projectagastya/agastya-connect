import streamlit as st

from utils.frontend.all import authenticated, reset_session_state

from utils.shared.errors import get_user_error
def main():
    if not authenticated():
        st.error(get_user_error())
        st.stop()
    else:
        reset_session_state()
        st.switch_page("pages/home.py")

if __name__ == "__main__":
    main()