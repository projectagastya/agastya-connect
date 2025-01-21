import streamlit as st

from dotenv import load_dotenv
from frontend.all_utils import handle_end_chat_confirmation, handle_user_input, render_chat_history, render_chat_subheader, render_sidebar_buttons, display_predefined_questions

load_dotenv()

async def load_chat_page():
    if not st.session_state["login_sessions"]["chat_sessions"]:
        st.error("No active chat session found.")
        return

    current_chat_session = st.session_state["login_sessions"]["chat_sessions"][-1]
    student_name = current_chat_session["selected_student"]["name"]
    student_avatar = current_chat_session["selected_student"]["image"]
    chat_history = current_chat_session["chat_history"]
    sidebar_buttons_config = [{"label": "Back to Main Page", "action": "main", "icon": ":material/arrow_back:", "type": "primary"}, {"label": "Start new session", "action": "choice", "icon": ":material/arrow_outward:", "type": "secondary"}]

    await render_chat_subheader(student_name)

    if current_chat_session["confirm_end_chat"]:
        await handle_end_chat_confirmation(current_chat_session=current_chat_session)
        return
    
    await render_sidebar_buttons(current_chat_session=current_chat_session, buttons_config=sidebar_buttons_config)

    await render_chat_history(chat_history=chat_history)

    user_input = st.chat_input(placeholder="Enter your message")

    if user_input:
        await handle_user_input(user_input=user_input, current_chat_session=current_chat_session, student_name=student_name, student_avatar=student_avatar)
        st.rerun()
        
    await display_predefined_questions(current_chat_session=current_chat_session, student_name=student_name, student_avatar=student_avatar)