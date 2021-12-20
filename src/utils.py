# Mercury: A lightning fast private ShareX uploader coded in Python using FastAPI.
# Copyright (C) 2021 ChecksumDev

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from os import listdir, path, remove
from objects import glob
from fastapi import HTTPException, Request
from fastapi.params import Header
from fastapi.responses import JSONResponse

VALID_USERNAME_REGEX = r"^[a-zA-Z0-9]{3,20}$"
VALID_PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$"

ALLOWED_CONTENT_TYPES = {  # images
    "image/jpeg",
    "image/png",
    "image/gif",  # video
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
    "audio/x-wav",  # text
    "text/plain",
    "text/html",
    "text/css",
    "text/javascript",
    "text/xml",
    "text/csv",
    "text/x-markdown",  # zip
    "application/zip",  #
}

# def init():
# for file in listdir(path.join("data", "uploads")):
#     file_name = file.split(".")[0]
#     if glob.database.users.find_one({"files": file_name}):
#         continue
#     print(f"Removing orphaned file: {file}")
#     try:
#         remove(path.join("data", "uploads", file))
#     except Exception:
#         print(f"Failed to remove orphaned file: {file}")
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
        HTTPException: If the authorization header is not provided
        HTTPException: If the authorization header is not valid
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is not provided",
        )

    if not glob.database.users.find_one({"token": authorization}):
        raise HTTPException(
            status_code=401,
            detail="Authorization header is not valid",
        )
