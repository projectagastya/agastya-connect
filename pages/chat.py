import asyncio
import streamlit as st

from frontend_utils import (
    end_chat_dialog,
    formatted_name,
    handle_user_input,
    render_chat_history,
    render_chat_subheader,
    render_next_questions,
    security_check,
    setup_page
)

setup_page(initial_sidebar_state="expanded")

async def render_chat_page():
    security_check()

    if "active_chat_session" not in st.session_state or len(st.session_state["active_chat_session"]) == 0:
        st.switch_page(page="pages/selection.py")
    
    current_chat_session = st.session_state["active_chat_session"]
    student_name = current_chat_session["student_profile"]["name"]
    student_avatar = current_chat_session["student_profile"]["image"]
    chat_history = current_chat_session["chat_history"]

    render_chat_subheader(student_name)

    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(label="End Chat Session", icon=":material/close:", type="primary", use_container_width=True):
            st.session_state["end_chat_dialog"] = True
            st.rerun()
        st.markdown("---")
    
    render_chat_history(chat_history=chat_history)

    if st.session_state["end_chat_dialog"]:
        end_chat_dialog(
            current_chat_session=current_chat_session,
            student_name=student_name
        )

    user_input = st.chat_input(placeholder=f"Ask {formatted_name(student_name).split(' ')[0]} a question")
    await render_next_questions(next_questions=current_chat_session["next_questions"])

    if user_input:
        await handle_user_input(
            user_input=user_input.text,
            current_chat_session=current_chat_session,
            student_name=student_name,
            student_avatar=student_avatar,
            input_type="manual"
        )
        st.rerun()

if __name__ == "__main__":
    asyncio.run(render_chat_page())