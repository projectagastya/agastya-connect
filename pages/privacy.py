import streamlit as st
from utils.frontend.all import setup_page, add_text

setup_page(page_title="Agastya Connect", page_icon="static/logo.png", layout="wide")

st.title("Privacy Policy", anchor=False)
st.caption("Last updated: June 10, 2025")

content = {
    "1. Introduction": "Welcome to Agastya Connect. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our services. We are committed to protecting your privacy and ensuring the security of your personal data.",
    "2. Information We Collect": """
#### 2.1 Google Authentication
We use Google's OAuth 2.0 authentication system to allow users to sign in to our platform. When you sign in with Google, we collect the following information:
- Your Google Profile ID
- Your email address
- Your basic profile information (name, profile picture)

We do not collect or store your Google password or any other sensitive authentication credentials.

#### 2.2 Usage Data
When you use our services, we may collect certain information automatically, including:
- Chat history

""",
    "3. How We Use Your Information": """
We use the information we collect to:
- Provide and maintain our services
- Improve our services and develop new features
- Analyze usage patterns and enhance user experience
- Communicate with you about our services
""",
    "4. Data Security": """
We implement appropriate security measures to protect your personal information against unauthorized access, alteration, display, or destruction. This includes:
- Encryption of sensitive data
- Secure authentication mechanisms
- Regular security audits and updates
""",
    "5. Your Rights": """
You have the right to:
- Access the personal information we hold about you
- Request corrections to your personal information
- Request deletion of your personal information
- Opt out of certain uses of your information
""",
    "6. Third Party Services": "We use third-party services (like Google) to provide certain features of our services. When you use these services, your information may be shared with them according to their privacy policies.",
    "7. Changes to This Privacy Policy": "We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the \"Last updated\" date."
}

for header, text in content.items():
    with st.container(border=True):
        st.header(header, anchor=False)
        st.markdown(text)

with st.container(border=True):
    st.header("8. Contact Us", anchor=False)
    st.markdown("If you have any questions about this Privacy Policy, please contact us at:")
    st.markdown("Email: projectagastya2024@gmail.com")
