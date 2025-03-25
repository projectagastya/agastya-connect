import asyncio
import streamlit as st

from frontend_utils import (
    add_aligned_text,
    formatted_name,
    initialize_chat_session,
    security_check,
    setup_page
)
from time import sleep

setup_page(initial_sidebar_state="collapsed")

async def load_progress_bar(student_choice):
    progress_text = f"Loading chat session with {formatted_name(student_choice['name'])}..."
    progress_bar = st.progress(value=0, text=progress_text)
    for percent in range(100):
        progress_bar.progress(value=percent + 1, text=f"{progress_text} ({percent + 1}%)")
        sleep(0.05)

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
        add_aligned_text(content=f"Setting up chat session with {formatted_name(student_choice['name'])}", alignment="center", size=36, bold=True)
        st.markdown("<br>", unsafe_allow_html=True)
        cols = st.columns([1, 1, 1, 1, 1])
        with cols[2]:
            st.image(image=student_choice["image"], use_container_width=True)
            st.markdown(f"**Name:** {formatted_name(student_choice['name'])}")
            st.markdown(f"**Age:** {student_choice['age']}")
            st.markdown(f"**State:** {formatted_name(student_choice['state'])}")
            st.markdown(f"**Gender:** {formatted_name(student_choice['sex'])}")

            with st.spinner(text="Loading..."):
                await initialize_chat_session(student_choice=student_choice)
                sleep(2)

    st.session_state["student_choice"] = None
    st.cache_resource.clear()
    st.session_state["loading_page"] = False
    st.switch_page(page="pages/chat.py")

asyncio.run(render_loading_page())