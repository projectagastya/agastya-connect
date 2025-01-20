import os
import pytz
import streamlit as st

from datetime import datetime
from dotenv import load_dotenv
from frontend.all_utils import add_aligned_text, generate_uuid, switch_page, validate_credentials

load_dotenv()

async def load_login_page():
    with st.container():
        col1, col2 = st.columns(spec=[1.0, 0.5], gap="large")

        with col1:
            add_aligned_text(content="Welcome to Agastya International Foundation", size=48, alignment="center", bold=True)
            add_aligned_text(content="The world's largest \"creativity laboratory\"", size=40, alignment="center")
            add_aligned_text(content="\"Agastya is a cause - not just an organization\"", size=24, alignment="center", bold=True, italics=True)
            st.markdown(body="<br>", unsafe_allow_html=True)
            add_aligned_text(content="Our vision is a creative world of tinkerers, innovators and solution-seekers who are humane, anchored and connected. Our mission is to spark curiosity (Aah!), nurture creativity (Aha!), and instill confidence and caring (Ha-Ha!) in children and teachers - through transformative experiential learning.", size=24, alignment="justify")
            st.markdown(body="<br>", unsafe_allow_html=True)
            cols = st.columns(spec=[0.1,1,0.01], gap="small")
            with cols[1]:
                st.image(image="./frontend/images/main.png", width=950)

        with col2:
            add_aligned_text(content="User Login", size=48, alignment="center", bold=True)
            username = st.text_input(label="Username", placeholder="Enter your username", type="default")
            password = st.text_input(label="Password", placeholder="Enter your password", type="password")
            st.markdown(body=" ", unsafe_allow_html=True)
            subcols = st.columns(spec=[1, 1], gap="small")
            with subcols[0]:
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
            with subcols[1]:
                if st.button(label="Forgot Password ?", icon=":material/lock_reset:", use_container_width=True):
                    switch_page(page_name="signup")
            if st.button(label="New User? Sign Up", icon=":material/assignment_ind:", use_container_width=True):
                switch_page(page_name="signup")
            st.markdown(body="<br>", unsafe_allow_html=True)
            st.image(image="frontend/images/login_pic.png",width=500)