from utils.shared.env import validate_env_var
from datetime import timezone, datetime

TIMEZONE_NAME = validate_env_var("TIMEZONE", required=False, default="UTC")

TIMEZONE = timezone.utc

def get_current_timestamp() -> str:
    return datetime.now(TIMEZONE).isoformat()

def get_current_datetime():
    return datetime.now(TIMEZONE)