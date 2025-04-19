import asyncio
import streamlit as st

from configure_logger import frontend_logger
from frontend_utils import (
    end_chat_dialog,
    formatted_name,
    handle_user_input,
    is_kannada,
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
    if current_chat_session:
        student_name = current_chat_session["student_profile"]["student_name"]
        student_avatar = current_chat_session["student_profile"]["student_image"]
    else:
        frontend_logger.error(f"render_chat_page | No active chat session found for user {getattr(st.experimental_user, "email")}")
        st.error("Sorry, we're facing an unexpected issue on our end. Please try again later.")
        st.stop()
    
    render_chat_subheader(student_name)

    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(label="Chat with another student", icon=":material/arrow_back:", type="primary", use_container_width=True):
            st.switch_page(page="pages/selection.py")
        st.markdown("---")
    
    render_chat_history(chat_history=current_chat_session["chat_history"])

    user_input = st.chat_input(placeholder=f"Ask {formatted_name(student_name).split(' ')[0]} a question")
    await render_next_questions(next_questions=current_chat_session["next_questions"])

    if is_kannada(user_input):
        input_type = "manual-kannada"
        frontend_logger.info(f"render_chat_page | Translating Kannada question: {user_input}")
    else:
        input_type = "manual-english"
        frontend_logger.info(f"render_chat_page | Input is English: {user_input}")

    if user_input:
        await handle_user_input(
            user_input=user_input,
            current_chat_session=current_chat_session,
            student_name=student_name,
            student_avatar=student_avatar,
            input_type=input_type
        )
        st.rerun()

if __name__ == "__main__":
    asyncio.run(render_chat_page())