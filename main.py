from hashlib import sha512
from os import path, remove
from secrets import token_urlsafe

from aiofiles import open as aioopen
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.params import Depends
from fastapi.responses import ORJSONResponse
from pymongo import MongoClient
from starlette.responses import FileResponse

from config import domain, mongo_settings
from objects import glob
from utils import (ALLOWED_CONTENT_TYPES, VALID_USERNAME_REGEX,
                   check_authorization, http_exception_handler)

mongo = MongoClient(
    f"mongodb+srv://{mongo_settings.get('user')}:{mongo_settings.get('password')}@{mongo_settings.get('host')}/{mongo_settings.get('db')}?retryWrites=true&w=majority")
glob.database = mongo.get_database(f"{mongo_settings.get('db')}")

exception_handlers = {HTTPException: http_exception_handler}

main = FastAPI(title="Mercury", openapi_url="/api/v1/openapi.json", docs_url="/", redoc_url=None,
               exception_handlers=exception_handlers, debug=True, )


@main.get("/favicon.ico")
async def favicon():
    """This endpoint returns the favicon.

    Returns:
        FileResponse: The favicon.
    """
    return FileResponse(path.join("data", "static", "favicon.ico"))


@main.post("/api/v1/auth/register")
async def register(request: Request):
    """This endpoint registers a new user.

    Args:
        request (Request): The request object.

    Returns:
        ORJSONResponse: The response object.
    """

    data = await request.json()
    if not data:
        raise HTTPException(status_code=400, detail="No json data provided.")

    if not data.get("username") or not data.get("password"):
        raise HTTPException(
            status_code=400, detail="Username and password are required.")  # 400 Bad Request

    if glob.database.users.find_one({"safe_username": data.get("username").lower()}):
        raise HTTPException(
            status_code=400, detail="Username is already taken.")

    user = {
        "username": data.get("username"),
        "safe_username": data.get("username").lower(),
        "password": sha512(data.get("password").encode()).hexdigest(),
        "token": token_urlsafe(32),
        "files": []
    }

    glob.database.users.insert_one(user)
    return ORJSONResponse(f"User {user.get('username')} created.", status_code=201)


@main.post("/api/v1/upload", dependencies=[Depends(check_authorization)])
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
            status_code=415, detail="The file type is not allowed.", )

    if size > 1024 * 1024 * 500:  # 500 MB
        raise HTTPException(
            status_code=413, detail="The file is too large to upload.", )

    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted_file = f.encrypt(file)

    file_id = token_urlsafe(32)

    glob.database.uploads.insert_one({"file_id": file_id, "original_name": original_name, "content_type": content_type,
                                      "hash": sha512(file).hexdigest(), "size": size, })

    async with aioopen(path.join("data", "uploads", file_id), "wb") as f:
        await f.write(encrypted_file)

    glob.database.users.update_one({"token": request.headers.get("Authorization")},
                                   {"$push": {"files": file_id}})

    return ORJSONResponse(status_code=201,
                          content={"url": f"https://{domain}/api/v1/uploads/{file_id}?key={key.decode()}"}, )


@main.post("/api/v1/auth/delete")
async def delete_user(request: Request):
    """This endpoint deletes a user.

    Args:
        request (Request): The request object.

    Raises:
        HTTPException: If the request is not authorized.

    Returns:
        ORJSONResponse: The response object.
    """

    token = request.headers.get("Authorization")
    user = glob.database.users.find_one({"token": token})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token.")

    files = glob.database.uploads.find({"file_id": {"$in": user.get("files")}})
    for file in files:
        glob.database.uploads.delete_one({"file_id": file.get("file_id")})
        try:
            remove(path.join("data", "uploads", file.get("file_id")))
        except:
            pass

    glob.database.users.delete_one({"token": token})

    return ORJSONResponse("User deleted.", status_code=200)


@main.get("/api/v1/uploads/{file_id}")
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

    upload = glob.database.uploads.find_one({"file_id": file_id})

    if not upload:
        raise HTTPException(
            status_code=404, detail="The file does not exist.", )

    key = request.query_params.get("key", None)

    if not key:
        raise HTTPException(
            status_code=400, detail="No decryption key was provided.", )

    f = Fernet(key)

    async with aioopen(path.join("data", "uploads", file_id), "rb") as file:
        encrypted_file = await file.read()

    try:
        decrypted_file = f.decrypt(encrypted_file)
    except:
        raise HTTPException(status_code=401, detail="The key is invalid.", )

    if sha512(decrypted_file).hexdigest() != upload["hash"]:
        raise HTTPException(
            status_code=400, detail="The file has either been tampered with or is corrupted.", )

    return Response(content=decrypted_file, media_type=upload["content_type"],
                    headers={"Content-Type": upload["content_type"],
                             "Content-Disposition": f"filename={upload['original_name']}",
                             "Content-Length": f"{len(decrypted_file)}", "Cache-Control": "no-cache", }, )
