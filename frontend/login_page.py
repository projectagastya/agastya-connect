import os
import pytz
import streamlit as st

from datetime import datetime
from dotenv import load_dotenv
from frontend.all_utils import add_aligned_text, generate_uuid, switch_page, validate_credentials

load_dotenv()

async def load_login_page():
    with st.container(border=False):
        col1, col2 = st.columns(spec=[1.0, 0.5], gap="large")

        with col1:
            with st.container(border=False):
                add_aligned_text(content="Welcome to Agastya International Foundation", size=39, alignment="center", bold=True)
                add_aligned_text(content="The world's largest \"creativity laboratory\"", size=28, alignment="center", bold=True, italics=True)
                st.markdown(body=" ", unsafe_allow_html=True)
                add_aligned_text(content="Our vision is a creative world of tinkerers, innovators and solution-seekers who are humane, anchored and connected. Our mission is to spark curiosity (Aah!), nurture creativity (Aha!), and instill confidence and caring (Ha-Ha!) in children and teachers - through transformative experiential learning.", size=18, alignment="justify")
                st.markdown(body="<br>", unsafe_allow_html=True)
                with st.container(height=500, border=False):
                    st.image(image="./frontend/images/main.png", use_container_width=True)

        with col2:
            with st.container(border=False):
                if st.session_state.get("user_just_created") is True:
                    st.success("Account created successfully! You may now log in with your username and password.")
                    st.session_state["user_just_created"] = False
                    
                add_aligned_text(content="User Login", size=39, alignment="center", bold=True)
                username = st.text_input(label="Username", placeholder="Enter your username", type="default")
                password = st.text_input(label="Password", placeholder="Enter your password", type="password")
                st.markdown(body=" ", unsafe_allow_html=True)
                subcols = st.columns(spec=[1, 1], gap="small")
                with subcols[0]:
                    if st.button(label="Login", icon= ":material/login:", type="primary", use_container_width=True):
                        if await validate_credentials(username=username, password=password):
                            st.session_state["username"] = username
                            st.session_state["login_sessions"] = {
                                "id": generate_uuid(),
                                "login_timestamp": datetime.now(tz=pytz.timezone(zone=os.getenv(key="TIMEZONE", default="US/Central"))),
                                "logout_timestamp": None,
                                "chat_sessions": [],
                                "active_chat_session": None
                            }
                            switch_page(page_name="main")
                        elif not (username and password):
                            st.error(body="Missing credentials.")
                        else:
                            st.error(body="Invalid credentials. Please try again")
                with subcols[1]:
                    if st.button(label="Forgot Password ?", icon=":material/lock_reset:", use_container_width=True):
                        switch_page("password_reset")
                if st.button(label="New User ? Sign Up", icon=":material/person_add:", use_container_width=True):
                    switch_page("signup")
                
                with st.container(height=380, border=False):
                    st.image(image="frontend/images/login_pic.png", width=380)