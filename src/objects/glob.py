from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pymongo.database import Database
    from objects import logger
__all__ = ("database", )

database: 'Database'
logger: 'logger.Logger'
max_file_size = 50 * 1024 * 1024