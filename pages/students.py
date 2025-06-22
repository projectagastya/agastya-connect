import streamlit as st

from config.shared.timezone import get_current_datetime
from utils.frontend.api_calls import get_student_profiles, get_active_sessions
from utils.frontend.all import (
    add_text,
    formatted,
    reset_session_state,
    security_check,
    setup_page,
)
from config.frontend.other import (
    STUDENT_IMAGE_URL
)
from urllib.parse import urlparse
from utils.shared.errors import get_user_error
from utils.shared.logger import frontend_logger

setup_page()

def render_students_page():
    security_check()
    
    if len(st.session_state) == 0:
        reset_session_state()

    user_email = getattr(st.user, "email")
    login_session_id = getattr(st.user, "nonce")

    active_sessions_success, active_sessions_message, active_sessions = get_active_sessions(
        user_email=user_email,
        login_session_id=login_session_id
    )
    
    active_session_map = {}
    if active_sessions_success and active_sessions:
        for session in active_sessions:
            active_session_map[session["student_name"]] = session["chat_session_id"]

    cols = st.columns([0.9,10,1.1], gap="small")
    with cols[0]:
        if st.button(label="", icon=":material/arrow_back:", type="primary", disabled=st.session_state["loading_page"], use_container_width=True):
            st.switch_page(page="pages/home.py")

    success, message, students = get_student_profiles(count=8)
    if not success:
        frontend_logger.error(f"render_students_page | Error loading student profiles from backend : {message}")
        st.error(get_user_error())
        st.stop()
    with cols[1]:
        add_text(content="Select a student to chat with", alignment="center", bold=True, size=35)
    st.markdown("<br>", unsafe_allow_html=True)

    rows = [students[i:i + 4] for i in range(0, len(students), 4)]

    for _, row in enumerate(rows):
        cols = st.columns(4, gap="small")
        for col_idx, student in enumerate(row):
            with cols[col_idx]:
                student_name = student["student_name"]
                student_age = student["student_age"]
                student_state = student["student_state"]
                student_sex = student["student_sex"]
                student_image = STUDENT_IMAGE_URL.format(domain=urlparse(st.context.url).netloc, student_name=student_name)
                
                with st.container(border=True):
                    add_text(content=formatted(student_name), alignment="center", size=20, bold=True)
                    subcols = st.columns([2,2])
                    
                    with subcols[0]:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.image(image=student_image, use_container_width=True)
                        
                        has_active_session = student_name in active_session_map
                        button_label = "Resume Chat" if has_active_session else "Start Chat"
                        
                        if st.button(
                            label=button_label,
                            key=f"{'resume' if has_active_session else 'start'}_chat_{student['student_name']}",
                            type="secondary" if has_active_session else "primary",
                            use_container_width=True
                        ):
                            get_active_sessions.clear()
                            st.session_state["student_choice"] = student
                            if has_active_session:
                                st.session_state["active_chat_session"] = {
                                    "id": active_session_map[student_name],
                                    "chat_history": [],
                                    "next_questions": [],
                                    "recent_questions": [],
                                    "chat_start_timestamp": get_current_datetime(),
                                    "chat_end_timestamp": None,
                                    "student_profile": student
                                }
                            else:
                                if "active_chat_session" in st.session_state:
                                    st.session_state["active_chat_session"]["id"] = None
                            
                            st.session_state["loading_page"] = True
                            st.switch_page(page="pages/loading.py")
                    
                    with subcols[1]:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(f"**Age:** {student_age}")
                        st.markdown(f"**Sex:** {formatted(student_sex)}")
                        st.markdown(f"**State:** {formatted(student_state)}")
                        st.markdown(" ", unsafe_allow_html=True)

if __name__ == "__main__":
    render_students_page()