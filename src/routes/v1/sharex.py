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

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request
from fastapi.responses import ORJSONResponse
from starlette.responses import FileResponse, Response
from objects import glob, logger
from utils import check_authorization
from secrets import token_urlsafe
from cryptography.fernet import Fernet
from aiofiles import open as aioopen
from utils import ALLOWED_CONTENT_TYPES
from hashlib import sha512
from os import path

router = APIRouter()


@router.post("/upload", dependencies=[Depends(check_authorization)])
async def post_file(request: Request):
    """This endpoint is used to upload files to the server.

    Args:
        request (Request): The request object.

    Raises:
        HTTPException: If the request is not authorized.
        HTTPException: If the request is not a multipart/form-data request.

    Returns:
        ORJSONResponse: The response object.
    """

    body = await request.form()

    original_name = body["file"].filename
    content_type = body["file"].content_type

    file = await body["file"].read()
    size = len(file)

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="The file type is not allowed.",
        )

    if size > glob.config.max_file_size:
        raise HTTPException(
            status_code=413,
            detail="The file is too large.",
        )

    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted_file = f.encrypt(file)

    file_id = token_urlsafe(32)
    delete_key = token_urlsafe(8)

    if (user := glob.database.users.find_one(
        {"token": request.headers.get("Authorization")})) is None:
        raise HTTPException(
            status_code=401,
            detail="You are not authorized.",
        )

    try:
        async with aioopen(path.join("data", "uploads", user["safe_username"], f'{file_id}.hg'), "wb") as f:
            await f.write(encrypted_file)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while saving the file. {e}")
    finally:
        glob.database.uploads.insert_one({
            "file_id": file_id,
            "delete_key": delete_key,
            "original_name": original_name,
            "content_type": content_type,
            "hash": sha512(file).hexdigest(),
            "size": size,
        })

        glob.database.users.update_one(
            {"token": request.headers.get("Authorization")},
            {"$push": {
                "files": file_id
            }})

        glob.logger.info(
            f"{user['username']} uploaded {original_name}. ({size * 1.0 / 1024 / 1024:.2f} MB)"
        )
        return ORJSONResponse(
            status_code=201,
            content={
                "file_url":
                f"{glob.config.domain}api/v1/uploads/{file_id}?key={key.decode()}",
                "delete_url":
                f"{glob.config.domain}api/v1/uploads/{file_id}?key={key.decode()}&delete_key={delete_key}"
            })


@router.get("/uploads/{file_id}")
async def get_file(request: Request, file_id: str):
    """This endpoint is used to view a file.

    Args:
        request (Request): The request object.
        file_id (str): The file id.

    Parameters:
        key (str): The decryption key.

    Raises:
        HTTPException: If the file does not exist.
        HTTPException: If the key is not provided.
        HTTPException: If the key is invalid.
        HTTPException: If the file is corrupted.

    Returns:
        Response: The response object. (File)
    """

    if (upload := glob.database.uploads.find_one({"file_id": file_id
                                                  })) is None:
        return FileResponse(
            path.join("data", "static", "404.jpg"),
            status_code=404,
            headers={
                "Content-Type": "image/jpeg",
                "Content-Disposition": 'inline; filename=404.jpg',
            },
        )

    if not (key := request.query_params.get("key", None)):
        raise HTTPException(
            status_code=400,
            detail="No decryption key was provided.",
        )

    if (user := glob.database.users.find_one({"files": file_id})) is None:
        raise HTTPException(
            status_code=401,
            detail="This file is orphaned and cannot be accessed.",
        )

    if (delete_key := request.query_params.get("delete_key",
                                               None)) is not None:
        if upload["delete_key"] != delete_key:
            raise HTTPException(
                status_code=400,
                detail="The delete key is invalid.",
            )

        glob.database.uploads.delete_one({"file_id": file_id})
        glob.database.users.update_one({"files": file_id},
                                       {"$pull": {
                                           "files": file_id
                                       }})

        glob.logger.info(
            f"{user['username']} deleted {upload['original_name']}.")
        return ORJSONResponse(
            status_code=200, content={"message": "File deleted successfully."})

    try:
        f = Fernet(key)
        async with aioopen(path.join("data", "uploads", user["safe_username"], f'{file_id}.hg'), "rb") as file:
            encrypted_file = await file.read()
    except FileNotFoundError:
        return FileResponse(
            path.join("data", "static", "404.jpg"),
            status_code=404,
            headers={
                "Content-Type": "image/jpeg",
                "Content-Disposition": 'inline; filename=404.jpg',
            },
        )

    except:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while reading the file.",
        )

    try:
        decrypted_file = f.decrypt(encrypted_file)
    except:
        raise HTTPException(
            status_code=401,
            detail="The key is invalid.",
        )

    if sha512(decrypted_file).hexdigest() != upload["hash"]:
        raise HTTPException(
            status_code=400,
            detail="The file has either been tampered with or is corrupted.",
        )

    glob.logger.info(
        f"{request.client.host} viewed {upload['original_name']} ({upload['size'] * 1.0 / 1024 / 1024:.2f} MB) from {user['safe_username']}."
    )

    return Response(
        content=decrypted_file,
        media_type=upload["content_type"],
        headers={
            "Content-Type": upload["content_type"],
            "Content-Disposition": f"filename={upload['original_name']}",
            "Content-Length": f"{len(decrypted_file)}",
            "Cache-Control": "no-cache",
        },
    )
