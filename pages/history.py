import streamlit as st

from frontend_utils import add_aligned_text, generate_word_document, toggle_chat_history
from datetime import datetime

st.set_page_config(page_title="Agastya Envision", page_icon=":school:", layout="wide", initial_sidebar_state="auto")
st.logo(image="images/logo.png", size="large", icon_image="images/logo.png", link="https://www.agastya.org/")

if "login_sessions" not in st.session_state:
    st.error("You must log in to access this page.")
    if st.button(label="Log in", icon=":material/login:", type="primary"):
        st.switch_page(page="pages/login.py")
    st.stop()

current_login_session = st.session_state["login_sessions"]
all_chats = current_login_session["chat_sessions"]

filtered_chats = [chat for chat in all_chats if len(chat["chat_history"]) > 1]

with st.container():
    with st.sidebar:
        st.markdown("---")
        if st.button(label="Back to Home Page", use_container_width=True, icon=":material/home:", type="primary"):
            st.switch_page(page="pages/home.py")

with st.container():
    add_aligned_text(content="Previous Chats", alignment="center", size=35, bold=True)
st.markdown("<br><br>", unsafe_allow_html=True)

cols = st.columns(spec=[1, 5, 1])
with cols[1]:
    if not filtered_chats:
        st.info(body="You have not had any chats yet.")

for index, chat in enumerate(iterable=filtered_chats):
    selected_student = chat["selected_student"]["name"]
    chat_summary = f"{index + 1}. Chat with {selected_student}"

    session_key = f"show_chat_{index}"
    if session_key not in current_login_session:
        current_login_session[session_key] = False

    with st.expander(label=chat_summary, expanded=False):
        st.write(f"Started At: {chat['chat_start_timestamp']}")
        st.write(f"Ended At: {chat['chat_end_timestamp']}")
        st.write(f"Total Messages: {len(chat['chat_history'])}")
        st.markdown(body="---")

        st.button(label="Show Chat History" if not current_login_session[session_key] else "Hide Chat History", key=f"chat_button_{index}", on_click=toggle_chat_history, args=(index,))

        word_buffer = generate_word_document(chat=chat)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{selected_student}_chat_{timestamp}.docx"
        st.download_button(label="Download Chat History",
                           data=word_buffer,
                           file_name=file_name,
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           key=f"{index}_{file_name}_download_button",
        )
        if current_login_session[session_key]:
            add_aligned_text(content=f"Chat History with {selected_student}", alignment="center", size=25, bold=True)
            st.markdown(" ", unsafe_allow_html=True)
            for msg in chat["chat_history"]:
                role = "You" if msg["role"] == "user" else selected_student
                content = msg["content"]
                st.markdown(body=f"**{role}:** {content}")
            st.markdown(body="---")