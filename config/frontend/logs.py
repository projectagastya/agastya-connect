from utils.shared.env import validate_env_var

ADMIN_ACCOUNTS = list(validate_env_var("ADMIN_ACCOUNTS", required=False, default="").split(","))