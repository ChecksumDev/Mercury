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