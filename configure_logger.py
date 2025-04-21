import os

from dotenv import load_dotenv
from logging import getLogger, Formatter, INFO
from logging.handlers import TimedRotatingFileHandler

load_dotenv(dotenv_path=".env")

def configure_logger(name: str):
    log_dir = os.path.join(os.getenv("LOGS_FOLDER_PATH", "logs"), f"{name}_logs")
    os.makedirs(name=log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{name}_logs.log")
    logger = getLogger(name=f"{name}_logger")
    logger.setLevel(level=INFO)

    if not logger.handlers:
        file_handler = TimedRotatingFileHandler(filename=log_file, when="midnight", interval=1, utc=True)
        file_handler.setLevel(INFO)
        formatter = Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(fmt=formatter)
        logger.addHandler(hdlr=file_handler)

    logger.propagate = False
    return logger

backend_logger = configure_logger(name="backend")
frontend_logger = configure_logger(name="frontend")