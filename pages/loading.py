import asyncio
import streamlit as st

from frontend.utils import (
    add_aligned_text,
    formatted_name,
    initialize_chat_session,
    security_check,
    setup_page
)
from shared.logger import frontend_logger

setup_page(initial_sidebar_state="collapsed")

async def render_loading_page():
    security_check()

    if len(st.session_state) == 0:
        st.switch_page(page="pages/home.py")

    if "student_choice" not in st.session_state or st.session_state["student_choice"] is None:
        st.switch_page(page="pages/selection.py")

    if not st.session_state["loading_page"]:
        st.session_state["loading_page"] = True

    student_choice = st.session_state["student_choice"]

    with st.container(border=True):
        st.markdown("<br>", unsafe_allow_html=True)
        add_aligned_text(content=f"Setting up chat session with {formatted_name(student_choice['student_name'])}", alignment="center", size=36, bold=True)
        st.markdown("<br>", unsafe_allow_html=True)
        cols = st.columns([1, 1, 1, 1, 1])
        with cols[2]:
            st.image(image=student_choice["student_image"], use_container_width=True)
            st.markdown(f"**Name:** {formatted_name(student_choice['student_name'])}")
            st.markdown(f"**Age:** {student_choice['student_age']}")
            st.markdown(f"**State:** {formatted_name(student_choice['student_state'])}")
            st.markdown(f"**Gender:** {formatted_name(student_choice['student_sex'])}")

            with st.spinner(text="Loading..."):
                await initialize_chat_session(student_choice=student_choice)

    st.session_state["student_choice"] = None
    st.cache_resource.clear()
    st.session_state["loading_page"] = False
    st.switch_page(page="pages/chat.py")

asyncio.run(render_loading_page())