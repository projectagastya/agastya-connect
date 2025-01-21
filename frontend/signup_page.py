import streamlit as st
import bcrypt

from frontend.all_utils import add_aligned_text, is_username_taken, load_user_data, save_user_data, switch_page
from time import sleep

async def load_signup_page():
    if st.sidebar.button(label="Back to Login page", icon=":material/arrow_back:", type="primary", use_container_width=True):
        switch_page(page_name="login")
    
    if not "account_creation_state" in st.session_state:
        st.session_state["account_creation_state"] = None
    if not "user_just_created" in st.session_state:
        st.session_state["user_just_created"] = None

    if st.session_state["account_creation_state"] == "creating":
        with st.spinner("Creating account..."):
            sleep(2)
            st.session_state["user_just_created"] = True
        with st.spinner("Redirecting to login page..."):
            sleep(2)
            st.session_state["account_creation_state"] = None
        switch_page(page_name="login")
        return

    add_aligned_text(content="Sign Up", alignment="center", size=30, bold=True)
    first_name = st.text_input("First Name", placeholder="Enter your first name")
    last_name = st.text_input("Last Name", placeholder="Enter your last name")
    email = st.text_input("Email", placeholder="Enter your email")
    phone = st.text_input("Phone Number", placeholder="Enter your phone number")
    username = st.text_input("Username", placeholder="Choose a unique username")
    password = st.text_input("Password", placeholder="Create a password", type="password")
    confirm_password = st.text_input("Confirm Password", placeholder="Re-enter your password", type="password")
    users = await load_user_data()

    if st.button(label="Submit", type="primary"):
        if not (first_name and last_name and email and phone and username and password):
            st.error(body="All fields are required.")
        elif await is_username_taken(username, users):
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
            await save_user_data(users=users)
            st.session_state["account_creation_state"] = "creating"
            st.rerun()