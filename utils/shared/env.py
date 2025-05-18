import os

from dotenv import load_dotenv
from utils.shared.logger import backend_logger

load_dotenv()

def validate_env_var(var_name: str, required: bool = True, default: str = None, allowed_values: list = None) -> str:
    value = os.getenv(var_name)
    if not value or value.strip() == "" or not isinstance(value, str):
        if required:
            backend_logger.error(f"{var_name} not set in .env")
            exit(1)
        return default
    if allowed_values and value not in allowed_values:
        return default
    return value

def validate_int_env_var(var_name: str, required: bool = True, default: int = None) -> int:
    value = os.getenv(var_name)
    try:
        int_value = int(value)
        if not int_value and required:
            backend_logger.error(f"{var_name} not set in .env")
            exit(1)
        return int_value
    except (ValueError, TypeError):
        if required:
            backend_logger.error(f"{var_name} not set in .env")
            exit(1)
        return default

def validate_float_env_var(var_name: str, required: bool = True, default: float = None) -> float:
    value = os.getenv(var_name)
    try:
        float_value = float(value)
        if not float_value and required:
            backend_logger.error(f"{var_name} not set in .env")
            exit(1)
        return float_value
    except (ValueError, TypeError):
        if required:
            backend_logger.error(f"{var_name} not set in .env")
            exit(1)
        return default