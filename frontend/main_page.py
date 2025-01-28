import streamlit as st

from frontend.all_utils import add_aligned_text, switch_page, logout_and_redirect

async def load_main_page():
    add_aligned_text(content=f"Hello, {st.session_state['username']}!", alignment="center", bold=True, size=48)
    add_aligned_text(content="Welcome to your AI-driven instructor training program", alignment="center", bold=True, size=32)
    add_aligned_text(content="At Agastya, we empower you for a bright future through engagement with AI-driven student simulations", alignment="center", size=20)
    st.markdown("<br>", unsafe_allow_html=True)
    add_aligned_text(content="On the next page, you'll interact with digital avatars of students from Agastya International Foundation.", alignment="center", size=20)
    add_aligned_text(content="You can ask questions and engage in a conversation to understand the student better.", alignment="center", size=20)
    st.markdown("<br>", unsafe_allow_html=True)
    add_aligned_text(content="We hope you enjoy the experience!", alignment="center", bold=True, size=20)
    st.markdown("---", unsafe_allow_html=True)
    cols = st.columns([3, 3], gap="medium")
    with cols[0]:
        add_aligned_text(content="Past Conversations", alignment="center", bold=True, size=32)
        st.markdown("<br>", unsafe_allow_html=True)
        subcols = st.columns([3,4,3])
        with subcols[1]:
            if st.button(label="History", icon=":material/history:", type="primary", use_container_width=True):
                switch_page(page_name="previous_chats")

    with cols[1]:
        add_aligned_text(content="Chat with a student", alignment="center", bold=True, size=32)
        st.markdown("<br>", unsafe_allow_html=True)
        subcols = st.columns([3,4,3])
        with subcols[1]:
            if st.button(label="Get Started", icon=":material/arrow_outward:", type="primary", use_container_width=True):
                switch_page(page_name="choice")
    
    with st.sidebar:
        cols = st.columns([3.5, 7, 1], gap="small")
        add_aligned_text(content="My Profile", alignment="center", bold=True, size=32)
        add_aligned_text(content=f"Username: {st.session_state['username']}", alignment="center", size=16)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(label="Account Settings", icon=":material/settings:", use_container_width=True):
            switch_page(page_name="account_settings")

        st.markdown("---", unsafe_allow_html=True)
        st.markdown(body=f"""

            # Contact
            Email: [info@agastya.org](mailto:info@agastya.org)  
            Phone: (+91) 80411 24132

            # Volunteer with us  
            [Click here to join us](https://www.agastya.org/agastya-volunteer-program)
                                
            # Donate to our cause  
            [Click here to donate](https://www.agastya.org/donate)

            ---
        """)
        
        if st.button(label="Logout", icon=":material/logout:", type="primary", use_container_width=True):
            logout_and_redirect()