import logging
from enum import Enum
from pathlib import Path

from sentinel.helpers import LogHelper

class Platform(Enum):
    android = 1
    iOS = 2
    WebGL = 3

#very explicitly defined methods to soothe extreme path deletion anxiety
def clear_new_resources():
    rmtree(Path("y3/exports/new_assetbundle"))
    rmtree(Path("y3/exports/new_master_data"))
    rmtree(Path("y3/exports/new_sound"))

def clear_extracted():
    rmtree(Path("y3/exports/extracted"))

def rmtree(root):
    global logger
    try:
        for child in root.iterdir():
            if child.is_dir():
                rmtree(child)
            else:
                logger.debug(f"Removing file: [red]{child}[/red].")
                child.unlink()
            logger.debug(f"Removing directory: [red]{child}[/red].")
        root.rmdir()
    except FileNotFoundError as error:
        logger.error(error)

def set_vars(platform_enum: Enum, previous_version: str):
    global PLATFORM
    PLATFORM = platform_enum.name
    global PREVIOUS_VERSION
    PREVIOUS_VERSION = previous_version
    global CURRENT_PATH
    CURRENT_PATH = f"y3/resources/{PLATFORM}/master_data"
    global PREVIOUS_PATH
    PREVIOUS_PATH = f"y3/exports/old_master_data/{PREVIOUS_VERSION}"

logger = LogHelper.new_logger("helpers.[green]PathHelper[/green]")

#defaults
PLATFORM = "android"
PREVIOUS_VERSION = "test"
CURRENT_PATH = f"y3/resources/{PLATFORM}/master_data"
NEW_PATH = "y3/exports/new_master_data"
PREVIOUS_PATH = f"y3/exports/old_master_data/{PREVIOUS_VERSION}"
