from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.params import Header
from config import api_key

ALLOWED_CONTENT_TYPES = {
    # images
    "image/jpeg",
    "image/png",
    "image/gif",
    # video
    "video/mp4",
    "video/webm",
    "video/ogg",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-ms-wmv",
    "video/x-flv",
    # audio (mp3, ogg, etc.)
    "audio/mpeg",
    "audio/ogg",
    "audio/wav",
    "audio/x-wav",
    # text
    "text/plain",
}

async def http_exception_handler(request: Request, exc: HTTPException):
    """This function handles HTTP exceptions

    Args:
        exc (HTTPException): The HTTP exception
        request (Request): The request

    Returns:
        JSONResponse: The JSON response
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


async def check_authorization(authorization: str = Header(default=None)):
    """This function checks if the authorization header is valid

    Args:
        authorization (str, optional): The authorization header. Defaults to None.

    Raises:
        HTTPException: If the authorization header is not valid
        HTTPException: If the authorization header is not provided
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is not provided",
        )

    if authorization != api_key:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )