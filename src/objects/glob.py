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

try:
    import config
except ModuleNotFoundError as e:
    print("\033[91m[!] Error: Could not find config.py. Please create one.")
    exit(0)
    
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pymongo.database import Database
    from objects import logger

__all__ = ("database", "logger", "config")

database: 'Database'
logger: 'logger.Logger'