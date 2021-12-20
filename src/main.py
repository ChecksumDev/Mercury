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

from routes.v1 import auth, sharex
from os import path

from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from starlette.responses import FileResponse

from config import mongo_settings
from objects import glob, logger
from utils import http_exception_handler

glob.logger = logger.Logger()
glob.logger.info("Starting up...")

mongo = MongoClient(
    f"mongodb+srv://{mongo_settings.get('user')}:{mongo_settings.get('password')}@{mongo_settings.get('host')}/{mongo_settings.get('db')}?retryWrites=true&w=majority"
)
glob.logger.info("Connected to MongoDB.")

glob.database = mongo.get_database(f"{mongo_settings.get('db')}")
glob.logger.info(f"Using database {glob.database.name}.")

exception_handlers = {HTTPException: http_exception_handler}
glob.logger.info("Loaded exception handlers.")

main = FastAPI(
    title="Mercury",
    openapi_url="/api/v1/openapi.json",
    docs_url="/",
    redoc_url=None,
    exception_handlers=exception_handlers,
    debug=True,
)

main.include_router(auth.router, prefix="/api/v1")
main.include_router(sharex.router, prefix="/api/v1")
glob.logger.info("Loaded routes.")

glob.logger.info("Listening for connections...")


@main.get("/favicon.ico")
async def favicon():
    """This endpoint returns the favicon.

    Returns:
        FileResponse: The favicon.
    """
    return FileResponse(path.join("data", "static", "favicon.ico"))