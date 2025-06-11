import streamlit as st
from utils.frontend.all import setup_page, add_text

setup_page(page_title="Agastya Connect", page_icon="static/logo.png", layout="wide")

st.title("Terms and Conditions", anchor=False)
st.caption("Last updated: June 10, 2025")

content = {
    "1. Acceptance of Terms": "Welcome to Agastya Connect. By accessing or using our platform, you agree to be bound by these Terms and Conditions. If you do not agree to these terms, please do not use our services.",
    "2. User Eligibility": "You must be at least 18 years old to use our services. By using our platform, you represent and warrant that you meet the eligibility requirements.",
    "3. Account Registration": "To use our services, you must register an account using Google authentication. You are responsible for maintaining the confidentiality of your account credentials.",
    "4. User Conduct": """
    You agree to use our services only for lawful purposes and in accordance with these Terms and Conditions. You must not:
    - Use our services in any way that could damage, disable, or impair the functioning of our platform.
    - Attempt to gain unauthorized access to our services.
    - Use our services to send spam or unsolicited communications.
    - Use our services to infringe on intellectual property rights.
    """,
    "5. Content Policy": """
    You are solely responsible for the content you post on our platform. You must not post any content that is:
    - Defamatory, obscene, or harmful.
    - Infringing on intellectual property rights.
    - Violating privacy or confidentiality.
    - Promoting hate speech or discrimination.
    """,
    "6. Intellectual Property": "All content on our platform, including but not limited to text, graphics, logos, and software, is the property of Agastya International Foundation and is protected by copyright laws.",
    "7. Limitation of Liability": "Agastya International Foundation shall not be liable for any direct, indirect, incidental, or consequential damages arising from the use of our services.",
    "8. Termination": "We reserve the right to terminate or suspend your access to our services at any time, with or without cause.",
    "9. Changes to Terms": "We may update these Terms and Conditions from time to time. Your continued use of our services after any changes constitutes your acceptance of the modified terms.",
    "10. Governing Law": "These Terms and Conditions shall be governed by and construed in accordance with the laws of the jurisdiction where our services are primarily operated."
}

for header, text in content.items():
    with st.container(border=True):
        st.header(header, anchor=False)
        st.markdown(text)

with st.container(border=True):
    st.header("11. Contact Information", anchor=False)
    st.markdown("If you have any questions about these Terms and Conditions, please contact us at:")
    st.markdown("projectagastya2024@gmail.com")
