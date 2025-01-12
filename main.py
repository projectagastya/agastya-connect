import streamlit as st

from utils import switch_page, logout_and_redirect

async def load_main_page():
    st.title(body=f"Hello {st.session_state['username']}!", anchor=False)

    st.header(body="Welcome to your AI-driven instructor training program", anchor=False)
    st.subheader(body="At Agastya, we empower instructors for a bright future to engage with AI-driven student simulations", anchor=False)
    st.write(
        """
        On the next page, you'll interact with a digital avatar of a student from Agastya International Foundation.
        
        This session aims to help you understand how an Agastya student engages and learns.
        
        Feel free to ask your own questions or choose one from the sidebar options.
        
        ---
        """,
        unsafe_allow_html=False)
    
    cols = st.columns(spec=[4, 2, 4, 4], gap="small", vertical_alignment="center")
    with cols[0]:
        st.subheader(body="Proceed to chat with a student:", anchor=False)
    
    with cols[1]:
         if st.button(label="Proceed", icon=":material/arrow_outward:", type="primary", use_container_width=True):
            switch_page(page_name="choice")
    
    with st.sidebar:
        cols = st.columns([3.5, 7, 1], gap="small")
        with cols[1]:
            st.title(body="My Profile", anchor=False)
            st.markdown(body=f"""Username: **{st.session_state['username']}**""")

        if st.button(label="Edit Profile", icon=":material/edit:", use_container_width=True):
            st.write("Edit button clicked")

        if st.button(label="Previous chats", icon=":material/history:", type="primary", use_container_width=True):
            switch_page(page_name="previous_chats")

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