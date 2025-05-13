from shared.utils import validate_env_var

GCP_TYPE = validate_env_var("GCP_TYPE")
GCP_PROJECT_ID = validate_env_var("GCP_PROJECT_ID")
GCP_PRIVATE_KEY_ID = validate_env_var("GCP_PRIVATE_KEY_ID")
GCP_PRIVATE_KEY = validate_env_var("GCP_PRIVATE_KEY")
GCP_CLIENT_EMAIL = validate_env_var("GCP_CLIENT_EMAIL")
GCP_CLIENT_ID = validate_env_var("GCP_CLIENT_ID")
GCP_AUTH_URI = validate_env_var("GCP_AUTH_URI")
GCP_TOKEN_URI = validate_env_var("GCP_TOKEN_URI")
GCP_AUTH_PROVIDER_X509_CERT_URL = validate_env_var("GCP_AUTH_PROVIDER_X509_CERT_URL")
GCP_CLIENT_X509_CERT_URL = validate_env_var("GCP_CLIENT_X509_CERT_URL")
GCP_UNIVERSE_DOMAIN = validate_env_var("GCP_UNIVERSE_DOMAIN")

GCP_CREDENTIALS = {
    "type": GCP_TYPE,
    "project_id": GCP_PROJECT_ID,
    "private_key_id": GCP_PRIVATE_KEY_ID,
    "private_key": GCP_PRIVATE_KEY,
    "client_email": GCP_CLIENT_EMAIL,
    "client_id": GCP_CLIENT_ID,
    "auth_uri": GCP_AUTH_URI,
    "token_uri": GCP_TOKEN_URI,
    "auth_provider_x509_cert_url": GCP_AUTH_PROVIDER_X509_CERT_URL,
    "client_x509_cert_url": GCP_CLIENT_X509_CERT_URL,
    "universe_domain": GCP_UNIVERSE_DOMAIN
}