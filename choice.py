import json
import streamlit as st

from time import sleep
from utils import add_student, initialize_chat_session, switch_page

async def load_choice_page():
    if "login_sessions" not in st.session_state:
        st.error(body="You must log in first!", icon="⚠️")
        return

    with st.sidebar:
        if st.button(label="Add a New Student", icon=":material/add_circle:", use_container_width=True):
            await add_student()

        if st.button(label="Back to Main Page", icon=":material/arrow_back:", type="primary", use_container_width=True):
            switch_page("main")
            
    cols = st.columns(spec=[1,5,1], gap="small")
    
    with cols[1]:
        st.title("Pick a student to interact with", anchor=False)
        st.write("")
    st.markdown("---")
    try:
        with open("students.json", "r") as file:
            students = json.load(file)
    except FileNotFoundError:
        st.error("Students data file not found.")
        return

    rows = [students[i:i + 2] for i in range(0, len(students), 2)]

    for row in rows:
        cols = st.columns([7.5, 5, 1, 0.8, 7.5, 5, 1])
        for idx, student in enumerate(row):
            offset = idx * 4
            with cols[offset]:
                st.image(student["image"], use_container_width=True)
                if st.button(f"Chat with {student['name']}", key=student['name'], icon=":material/arrow_outward:", type="primary", use_container_width=True):
                    progress_text=f"Loading chat session with {student['name']}..."
                    progress_bar = st.progress(0, text=f"{progress_text} ({0}%)")
                    await initialize_chat_session(student_profile=student)
                    for percent in range(100):
                        progress_bar.progress(percent + 1, text=f"{progress_text} ({percent + 1}%)")
                        sleep(0.05)
                    if st.session_state["login_sessions"]["active_chat_session"]:
                        progress_bar.progress(100, text="Chat session loaded successfully!")
                    switch_page("chat")

                with st.popover(label="Student Information", icon=":material/info:", use_container_width=True):
                    st.write(f"**Name:** {student['name']}")
                    st.write(f"**Age:** {student['age']}")
                    st.write(f"**Sex:** {student['sex']}")
                    st.write(f"**Region:** {student['region']}")
            
            if idx % 2 == 0:
                st.markdown("---")
