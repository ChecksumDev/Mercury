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

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import ORJSONResponse
from objects import glob
from secrets import token_urlsafe
from hashlib import sha512
from os import mkdir, path

router = APIRouter()

@router.post("/auth/register")
async def register(request: Request):
    """This endpoint registers a new user.

    Args:
        request (Request): The request object.

    Returns:
        ORJSONResponse: The response object.
    """
    try:
        data = await request.json()
    except Exception:
        return ORJSONResponse({"message": "Invalid JSON"}, status_code=400)

    if not data.get("username") or not data.get("password"):
        raise HTTPException(
            status_code=400,
            detail="Username and password are required.")  # 400 Bad Request

    if glob.database.users.find_one(
        {"safe_username": data.get("username").lower()}):
        raise HTTPException(status_code=400,
                            detail="Username is already taken.")

    user = {
        "username": data.get("username"),
        "safe_username": data.get("username").lower(),
        "password": sha512(data.get("password").encode()).hexdigest(),
        "priv": 0,  # 0 = user, 1 = admin
        "token": token_urlsafe(32),  # 32 bytes
        "files": []  # list of file ids
    }

    safe_user = user.copy()
    safe_user.pop("safe_username")
    safe_user.pop("password")
    safe_user.pop("files")

    glob.database.users.insert_one(user)
    mkdir(path.join("data", "uploads", user["safe_username"]))
    
    glob.logger.info(f"{user['username']} registered.")
    return ORJSONResponse(safe_user, status_code=201)