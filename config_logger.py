import os

from dotenv import load_dotenv
from logging import getLogger, Formatter, INFO, TimedRotatingFileHandler

load_dotenv()

log_dir = os.path.abspath(os.getenv("LOG_FOLDER_PATH", default="logs"))
os.makedirs(name=log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "application_logs.log")

agastya_logger = getLogger(name="agastya_logger")
agastya_logger.setLevel(level=INFO)

if not agastya_logger.handlers:
    file_handler = TimedRotatingFileHandler(filename=log_file, when="midnight", interval=1, utc=True)
    file_handler.setLevel(INFO)
    formatter = Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(fmt=formatter)
    agastya_logger.addHandler(hdlr=file_handler)

agastya_logger.propagate = False