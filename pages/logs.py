import streamlit as st
import os
import glob
import traceback

from config.frontend.logs import ADMIN_ACCOUNTS
from utils.frontend.all import security_check, add_text, setup_page
from utils.shared.logger import frontend_logger

def is_admin():
    return getattr(st.user, "email") in ADMIN_ACCOUNTS

def render_logs_page():
    security_check()
    
    if not is_admin():
        st.switch_page(page="pages/home.py")
    else:
        setup_page()
        
        cols = st.columns([0.9, 10, 1.1], gap="small")
        with cols[0]:
            if st.button(label="", icon=":material/arrow_back:", type="primary", use_container_width=True):
                st.switch_page(page="pages/home.py")
        
        log_dir = os.getenv("LOGS_FOLDER_PATH", "logs")
        log_types = ["frontend", "backend"]
        
        log_type = st.selectbox("Select Log Type", log_types)
        
        log_path = os.path.join(log_dir, f"{log_type}_logs", f"{log_type}_logs.log")
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    file_size = os.path.getsize(log_path)
                    if file_size > 10 * 1024 * 1024:  # 10MB limit
                        st.warning(f"Log file is large ({file_size/1024/1024:.1f} MB). Showing only the last portion.")
                    
                    log_content = f.readlines()
                    frontend_logger.info(f"Accessed {log_type} logs via admin panel by {getattr(st.user, 'email')}")
            except Exception as e:
                error_msg = f"Error reading log file: {str(e)}"
                frontend_logger.error(f"Log viewer error: {error_msg}\n{traceback.format_exc()}")
                st.error(error_msg)
                log_content = []
                
            num_lines = st.slider("Number of lines to show", 10, 1000, 100)
            search_term = st.text_input("Search logs")
            
            filtered_logs = log_content[-num_lines:]
            if search_term:
                filtered_logs = [line for line in filtered_logs if search_term.lower() in line.lower()]
            
            log_text = "".join(filtered_logs)
            st.text_area("Log Content", log_text, height=500)
            
            if st.button("Download Logs"):
                st.download_button(
                    label="Download Full Log",
                    data="".join(log_content),
                    file_name=f"{log_type}_logs.log",
                    mime="text/plain"
                )
        else:
            st.error(f"Log file not found: {log_path}")

if __name__ == "__main__":
    render_logs_page()