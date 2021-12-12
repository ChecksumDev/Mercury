from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pymongo.database import Database
    
__all__ = ("database",)


database: 'Database'