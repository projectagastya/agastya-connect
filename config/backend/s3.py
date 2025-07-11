from utils.shared.env import validate_env_var

MAIN_S3_BUCKET_NAME = validate_env_var("MAIN_S3_BUCKET_NAME")
STUDENT_METADATA_FILE_NAME = validate_env_var("STUDENT_METADATA_FILE_NAME")
STUDENT_METADATA_FOLDER_PATH = validate_env_var("STUDENT_METADATA_FOLDER_PATH")