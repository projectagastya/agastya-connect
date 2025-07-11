from config.backend.api import (
    BACKEND_API_KEY,
    BACKEND_ORIGINS
)
from api.models import (
    ChatMessageRequest,
    ChatMessageResponse
)
from fastapi import FastAPI, HTTPException, Depends, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from utils.shared.errors import get_user_error
from utils.shared.logger import backend_logger

# Check if BACKEND_API_KEY is set. If not, raise an HTTP exception.
if BACKEND_API_KEY is None:
    backend_logger.error("BACKEND_API_KEY is not set")
    raise HTTPException(status_code=500, detail=get_user_error())

app = FastAPI(title="Agastya API", description="API for the Agastya application")

# Define the API key header.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Add CORS middleware to allow cross-origin requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in BACKEND_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key"]
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    backend_logger.error(f"Unhandled exception: {str(exc)} | Path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": get_user_error()}
    )

# Function to validate the provided API key from the X-API-Key header.
def get_api_key(api_key: str = Security(api_key_header)):
    # Check if the API key is provided. If not, raise an HTTP exception.
    if not api_key:
        backend_logger.error("API key not provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_user_error()
        )
    # Check if the API key is valid. If not, raise an HTTP exception.
    if api_key != BACKEND_API_KEY:
        backend_logger.error("Invalid BACKEND API key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_user_error()
        )
    return api_key

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=FileResponse, summary="Serve the welcome page")
async def get_welcome_page():
    return 'static/welcome.html'

@app.get("/privacy", response_class=FileResponse, summary="Serve the privacy policy")
async def get_privacy_page():
    return 'static/privacy.html'

@app.get("/terms-of-service", response_class=FileResponse, summary="Serve the terms of service")
async def get_terms_of_service_page():
    return 'static/terms-of-service.html'