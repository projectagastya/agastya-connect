import logging
import os

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

log_dir = os.path.abspath(os.getenv("LOG_FILE_PATH"))
os.makedirs(log_dir, exist_ok=True)  

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(log_dir, f"application_logs.log")
agastya_logger = logging.getLogger("agastya_logger")
agastya_logger.setLevel(logging.INFO)

if not agastya_logger.handlers:
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    agastya_logger.addHandler(file_handler)

agastya_logger.propagate = False
