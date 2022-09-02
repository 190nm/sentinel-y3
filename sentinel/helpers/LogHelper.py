import logging
from enum import Enum

from rich.logging import RichHandler

class AllowedFilter(logging.Filter):
    def __init__(self, *allowedlist):
        self.allowed = [logging.Filter(name) for name in allowedlist]
    
    def filter(self, record):
        return any(item.filter(record) for item in self.allowed)

class DisallowedFilter(AllowedFilter):
    def __init__(self, *allowedlist):
        self.allowed = [logging.Filter(name) for name in allowedlist]
    
    def filter(self, record):
        return not AllowedFilter.filter(self, record)


def set_filter(filter_obj: logging.Filter):
    global console_logger
    console_logger.addFilter(filter_obj)

def new_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

# HTTP_ALLOWED = AllowedFilter("sentinel", "helpers", "httpx")
# HTTP_DISALLOWED = AllowedFilter("sentinel", "helpers")
HTTP_ALLOWED = DisallowedFilter("urllib3")
HTTP_DISALLOWED = DisallowedFilter("urllib3", "httpx")
console_logger = RichHandler(level=logging.DEBUG, show_time=False, rich_tracebacks=True, markup=True)
console_logger.addFilter(HTTP_ALLOWED)
console_logger.setFormatter(logging.Formatter("%(name)s - %(message)s"))

debug_logger = logging.FileHandler("y3/debug.log", "a")
debug_logger.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s", "%Y/%m/%d %H:%M:%S"))

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt="[%X]",
    handlers=[console_logger, debug_logger],
    level=logging.DEBUG)
