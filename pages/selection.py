import asyncio
import json
import streamlit as st

from frontend_utils import add_aligned_text, initialize_chat_session
from time import sleep

st.set_page_config(page_title="Agastya Envision", page_icon=":school:", layout="wide", initial_sidebar_state="auto")
st.logo(image="images/logo.png", size="large", icon_image="images/logo.png", link="https://www.agastya.org/")

if "login_sessions" not in st.session_state:
    st.error("You must log in to access this page.")
    if st.button(label="Log in", icon=":material/login:", type="primary"):
        st.switch_page(page="pages/login.py")
    st.stop()

with st.sidebar:
    st.markdown("---")
    if st.button(label="Back to Home Page", icon=":material/home:", type="primary", use_container_width=True):
        st.switch_page(page="pages/home.py")
    if st.button(label="Refresh Students List", icon=":material/refresh:", type="secondary", use_container_width=True):
        pass

try:
    with open("backend/students.json", "r") as file:
        students = json.load(file)
except FileNotFoundError:
    st.error("Students data file not found.")
    st.stop()

rows = [students[i:i + 4] for i in range(0, len(students), 4)]

for row in rows:
    cols = st.columns(spec=[4,1.5,4,1.5,4,1.5,4,1.5], gap="small")
    for idx, student in enumerate(row):
        with cols[2*idx]:
            add_aligned_text(content=student["name"], alignment="center", size = 22, bold=True)
            st.image(image=student["image"], use_container_width=True)
            if st.button(label=f"Start chat", key=f"chat_with_{student['name']}", icon=":material/arrow_outward:", type="primary", use_container_width=True):
                progress_text=f"Loading chat session with {student['name']}..."
                progress_bar = st.progress(0, text=f"{progress_text} ({0}%)")
                asyncio.run(initialize_chat_session(student_profile=student))
                for percent in range(100):
                    progress_bar.progress(percent + 1, text=f"{progress_text} ({percent + 1}%)")
                    sleep(0.05)
                st.switch_page(page="pages/chat.py")

            with st.popover(label="View Details", icon=":material/info:", use_container_width=True):
                st.write(f"**Name:** {student['name']}")
                st.write(f"**Age:** {student['age']}")
                st.write(f"**Sex:** {student['sex']}")
                st.write(f"**Region:** {student['region']}")
    
    if row != rows[-1]:
        st.markdown("--- \n")
    else:
        st.markdown("")