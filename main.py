from hashlib import sha512
from os import path
from secrets import token_urlsafe

from aiofiles import open as aioopen
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.params import Depends
from fastapi.responses import ORJSONResponse
from pymongo import MongoClient
from starlette.responses import FileResponse

from config import domain, mongo_settings
from utils import (ALLOWED_CONTENT_TYPES, check_authorization,
                   http_exception_handler)

database = MongoClient(
    f"mongodb+srv://{mongo_settings.get('user')}:{mongo_settings.get('password')}@{mongo_settings.get('host')}/{mongo_settings.get('db')}?retryWrites=true&w=majority").get_database(f'{mongo_settings.get("db")}')

exception_handlers = {HTTPException: http_exception_handler}

main = FastAPI(
    title="Mercury",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url=None,
    exception_handlers=exception_handlers,
    debug=True,
)


@main.get("/favicon.ico")
async def favicon():
    """This endpoint returns the favicon.

    Returns:
        FileResponse: The favicon.
    """
    return FileResponse(path.join("data", "static", "favicon.ico"))


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

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="The file type is not allowed.",
        )

    if len(file) > 1024 * 1024 * 10:  # 10MB
        raise HTTPException(
            status_code=413,
            detail="The file is too large.",
        )

    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted_file = f.encrypt(file)

    file_id = token_urlsafe(32)

    database.uploads.insert_one({
        "file_id": file_id,
        "original_name": original_name,
        "content_type": content_type,
        "hash": sha512(file).hexdigest(),
    })

    async with aioopen(path.join("data", "uploads", file_id), "wb") as f:
        await f.write(encrypted_file)

    return ORJSONResponse(
        status_code=201,
        content={
            "url": f"https://{domain}/api/v1/uploads/{file_id}?key={key.decode()}"},
    )


@main.get("/api/v1/uploads/{file_id}")
async def get_file(request: Request, file_id: str):
    upload = database.uploads.find_one({"file_id": file_id})

    if not upload:
        raise HTTPException(
            status_code=404,
            detail="The file does not exist.",
        )

    key = request.query_params.get("key", None)

    if not key:
        raise HTTPException(
            status_code=400,
            detail="No decryption key was provided.",
        )

    f = Fernet(key)
    async with aioopen(path.join("data", "uploads", file_id), "rb") as file:
        encrypted_file = await file.read()

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
