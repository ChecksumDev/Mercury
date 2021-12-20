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

from time import strftime
from sys import stdout

class Colors(object):
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    RESET = "\033[0m"


class LogLevel(object):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    LEVELS = {
        0: "DEBUG",
        1: "INFO",
        2: "WARNING",
        3: "ERROR",
        4: "CRITICAL",
    }


class Logger(object):
    def __init__(self, level=LogLevel.INFO, color=True):
        self.level = level
        self.color = color
        self.time_format = "%H:%M:%S"
        self.date_format = "%Y-%m-%d"

    def log(self, level, message):
        if level >= self.level:
            if self.color:
                color = Colors.RED if level == LogLevel.ERROR else Colors.YELLOW
                stdout.write(
                    f'{color}{strftime(self.time_format)}{Colors.RESET} {color}{LogLevel.LEVELS[level]}:{Colors.RESET} {message}\n'
                )

            else:
                stdout.write(
                    f"{strftime(self.time_format)} {level.name.upper()}: {message}\n"
                )

            stdout.flush()

    def debug(self, message):
        self.log(LogLevel.DEBUG, message)

    def info(self, message):
        self.log(LogLevel.INFO, message)

    def warning(self, message):
        self.log(LogLevel.WARNING, message)

    def error(self, message):
        self.log(LogLevel.ERROR, message)

    def critical(self, message):
        self.log(LogLevel.CRITICAL, message)
