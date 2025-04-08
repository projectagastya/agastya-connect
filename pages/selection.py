import streamlit as st

from configure_logger import frontend_logger
from frontend_api_calls import get_student_profiles
from frontend_utils import (
    add_aligned_text,
    formatted_name,
    reset_session_state,
    security_check,
    setup_page,
)

setup_page(initial_sidebar_state="collapsed")

def render_selection_page():
    security_check()
    
    if len(st.session_state) == 0:
        reset_session_state()

    cols = st.columns([0.9,10,1.1], gap="small")
    with cols[0]:
        if st.button(label="Back", icon=":material/arrow_back:", type="primary", disabled=st.session_state["loading_page"], use_container_width=True):
            st.switch_page(page="pages/home.py")

    with cols[2]:
        if st.button(label="Refresh", icon=":material/refresh:", type="primary", disabled=st.session_state["loading_page"], use_container_width=True):
            st.cache_resource.clear()
            st.rerun()
    
    success, message, students = get_student_profiles(count=8)
    if not success:
        frontend_logger.error(f"render_selection_page | Error loading student profiles from backend : {message}")
        st.error("Sorry, we're facing an unexpected issue while loading our student profiles. Please try again later.")
        st.stop()
    with cols[1]:
        add_aligned_text(content="Select a student to chat with", alignment="center", bold=True, size=35)
    st.markdown("<br>", unsafe_allow_html=True)

    rows = [students[i:i + 4] for i in range(0, len(students), 4)]

    for _, row in enumerate(rows):
        cols = st.columns(4, gap="small")
        for col_idx, student in enumerate(row):
            with cols[col_idx]:
                student_age = student["age"]
                student_state = student["state"]
                student_sex = "Male" if student["sex"] == "male" else "Female"
                
                with st.container(border=True):
                    add_aligned_text(content=formatted_name(student["name"]), alignment="center", size=20, bold=True)
                    subcols = st.columns([2,2])
                    
                    with subcols[0]:
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.image(image=student["image"], use_container_width=True)
                        if st.button(
                            label=f"Start Chat",
                            key=f"chat_with_{formatted_name(student['name'])}",
                            type="primary",
                            icon=":material/arrow_outward:",
                            use_container_width=True
                        ):
                            st.session_state["student_choice"] = student
                            st.session_state["loading_page"] = True
                            st.switch_page(page="pages/loading.py")
                    
                    with subcols[1]:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(f"**Age:** {student_age}")
                        st.markdown(f"**Sex:** {student_sex}")
                        st.markdown(f"**State:** {formatted_name(student_state)}")
                        st.markdown(" ", unsafe_allow_html=True)

if __name__ == "__main__":
    render_selection_page()