from shared.utils import validate_env_var

BACKEND_API_KEY = validate_env_var("BACKEND_API_KEY")
BACKEND_ORIGINS_STR = validate_env_var("BACKEND_ORIGINS", required=False)
BACKEND_ORIGINS = BACKEND_ORIGINS_STR.split(",") if BACKEND_ORIGINS_STR else ["*"]