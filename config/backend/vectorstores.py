from shared.utils import validate_env_var, validate_int_env_var

LOCAL_VECTORSTORES_DIRECTORY = validate_env_var("LOCAL_VECTORSTORES_DIRECTORY")
MAX_DOCS_TO_RETRIEVE = validate_int_env_var("RAG_MAX_DOC_RETRIEVE")