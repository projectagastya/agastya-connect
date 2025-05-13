from shared.utils import validate_env_var

AWS_ACCESS_KEY_ID = validate_env_var("AWS_ACCESS_KEY_ID") 
AWS_SECRET_ACCESS_KEY = validate_env_var("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = validate_env_var("AWS_DEFAULT_REGION")
AWS_REGION = validate_env_var("AWS_REGION", required=False, default=AWS_DEFAULT_REGION)