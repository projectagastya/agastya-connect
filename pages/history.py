import streamlit as st

from frontend_utils import (
    add_aligned_text,
    end_chat_dialog,
    reset_session_state,
    security_check,
    setup_page
)

setup_page()

def render_history_page():
    security_check()

    if len(st.session_state) == 0:
        reset_session_state()

    if "active_chat_session" in st.session_state and st.session_state["active_chat_session"]["id"] is not None:
        end_chat_dialog(
            current_chat_session=st.session_state["active_chat_session"],
            student_name=st.session_state["active_chat_session"]["student"]["name"]
        )
    
    cols = st.columns([1,12], gap="small")
    with cols[0]:
        if st.button(label="Back", icon=":material/arrow_back:", type="primary", use_container_width=True):
            st.switch_page(page="pages/home.py")

    with cols[1]:
        add_aligned_text(content="Previous Chats", alignment="center", bold=True, size=35)

    st.markdown("<br>", unsafe_allow_html=True)
    
if __name__ == "__main__":
    render_history_page()
