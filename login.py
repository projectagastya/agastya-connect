import os
import pytz
import streamlit as st

from datetime import datetime
from dotenv import load_dotenv
from utils import validate_credentials, generate_uuid, switch_page

load_dotenv()

async def load_login_page():
    col1, col2 = st.columns(spec=[1.0, 0.5], gap="large")

    with col1:
        st.image(image="images/agastya.png", use_container_width=True)
        st.title(body="The world's largest ***'creativity laboratory'***", anchor=False)
        st.header(body="***\"Agastya is a cause - not just an organization\"***", anchor=False)
        st.write("""Agastya's vision is a creative world of tinkerers, innovators and solution-seekers who are humane, anchored and connected.
                    \n\nOur mission is to spark curiosity (Aah!), nurture creativity (Aha!), and instill confidence and caring (Ha-Ha!) in children and teachers through transformative experiential learning.
                """)

    with col2:
        st.header(body="User Login", anchor=False)
        username = st.text_input(label="Username", placeholder="Enter your username")
        password = st.text_input(label="Password", placeholder="Enter your password", type="password")

        if st.button(label="Login", icon= ":material/login:", type="primary", use_container_width=True):
            if validate_credentials(username=username, password=password):
                st.session_state["username"] = username
                st.session_state["login_sessions"] = {
                    "id": generate_uuid(),
                    "login_timestamp": datetime.now(tz=pytz.timezone(zone=os.getenv(key="TIMEZONE", default="US/Central"))),
                    "logout_timestamp": None,
                    "chat_sessions": [],
                    "active_chat_session": None
                }
                switch_page(page_name="main")
            else:
                st.error(body="Invalid credentials.")

        if st.button(label="Sign up", icon=":material/person_add:", use_container_width=True):
            switch_page(page_name="signup")
