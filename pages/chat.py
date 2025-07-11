import asyncio
import streamlit as st

from urllib.parse import urlparse
from utils.frontend.api_calls import get_student_profiles
from utils.frontend.all import (
    handle_user_input,
    is_kannada,
    render_chat_history,
    render_chat_subheader,
    render_next_questions,
    security_check,
    setup_page
)
from utils.shared.errors import get_user_error
from utils.shared.logger import frontend_logger
from config.frontend.other import (
    STUDENT_IMAGE_URL
)

setup_page(initial_sidebar_state="expanded")

async def render_chat_page():
    security_check()

    if "active_chat_session" not in st.session_state or len(st.session_state["active_chat_session"]) == 0:
        st.switch_page(page="pages/students.py")
    
    current_chat_session = st.session_state["active_chat_session"]
    if current_chat_session:
        student_name = current_chat_session["student_profile"]["student_name"]
        student_avatar = STUDENT_IMAGE_URL.format(domain=urlparse(st.context.url).netloc, student_name=student_name)
    else:
        frontend_logger.error(f"render_chat_page | No active chat session found for user {getattr(st.user, 'email')}")
        st.error(get_user_error())
        st.stop()
    
    render_chat_subheader(student_name)

    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(label="Chat with another student", icon=":material/arrow_back:", type="primary", use_container_width=True):
            get_student_profiles.clear()
            st.switch_page(page="pages/students.py")
        st.markdown("---")
    
    render_chat_history(chat_history=current_chat_session["chat_history"])

    user_input = st.chat_input(placeholder=f"Please type your question here")
    await render_next_questions(next_questions=current_chat_session["next_questions"])

    if user_input:
        if is_kannada(user_input):
            input_type = "manual-kannada"
            frontend_logger.info(f"render_chat_page | Translating Kannada question: {user_input}")
        else:
            input_type = "manual-english"
            frontend_logger.info(f"render_chat_page | Input is English: {user_input}")
        
        if user_input.strip() == "":
            st.error("Please enter a question.")
            return
        
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