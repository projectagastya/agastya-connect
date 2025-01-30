import asyncio
import bcrypt
import streamlit as st

from frontend_utils import add_aligned_text, is_username_taken, load_user_data, save_user_data
from time import sleep

st.set_page_config(page_title="Agastya Envision", page_icon=":school:", layout="wide", initial_sidebar_state="auto")
st.logo(image="images/logo.png", size="large", icon_image="images/logo.png", link="https://www.agastya.org/")

st.sidebar.markdown("---")
if st.sidebar.button(label="Back to Login page", icon=":material/arrow_back:", type="primary", use_container_width=True):
    st.switch_page("pages/login.py")

if not "account_creation_state" in st.session_state:
    st.session_state["account_creation_state"] = None
if not "user_just_created" in st.session_state:
    st.session_state["user_just_created"] = None

if st.session_state["account_creation_state"] == "creating":
    with st.spinner("Creating account..."):
        sleep(2)
    with st.spinner("Redirecting to login page..."):
        sleep(2)
        st.session_state["user_just_created"] = True
        st.session_state["account_creation_state"] = None
    st.switch_page("pages/login.py")

add_aligned_text(content="Create a New Account", alignment="center", size=35, bold=True)
st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    first_name = st.text_input("First Name", placeholder="Enter your first name")
with col2:
    last_name = st.text_input("Last Name", placeholder="Enter your last name")
email = st.text_input("Email", placeholder="Enter your email")
phone = st.text_input("Phone Number", placeholder="Enter your phone number")
username = st.text_input("Username", placeholder="Choose a unique username")
password = st.text_input("Password", placeholder="Create a password", type="password")
confirm_password = st.text_input("Confirm Password", placeholder="Re-enter your password", type="password")
users = asyncio.run(load_user_data())
st.markdown(" ", unsafe_allow_html=True)
button_col = st.columns([8, 3, 8])[1]
with button_col:
    if st.button(label="Submit", type="primary", icon=":material/check_circle:"):
        if not (first_name and last_name and email and phone and username and password):
            st.error(body="All fields are required.")
        elif asyncio.run(is_username_taken(username, users)):
            st.error(body="Username is already taken. Please choose a different one.")
        elif password != confirm_password:
            st.error(body="Passwords do not match.")
        else:
            hashed_password = bcrypt.hashpw(password=password.encode('utf-8'), salt=bcrypt.gensalt()).decode('utf-8')
            new_user = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "username": username,
                "password": hashed_password
            }
            users.append(new_user)
            asyncio.run(save_user_data(users=users))
            st.session_state["account_creation_state"] = "creating"
            st.rerun()