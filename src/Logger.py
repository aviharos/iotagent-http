# -*- coding: utf-8 -*-
"""
A module for configuring all loggers identically
All the options are set in environment variables

Environment variables (defaults are starred):
LOGGING_LEVEL:
    DEBUG*
    INFO
    WARNING
    ERROR
    CRITICAL
    meaning the same as in python's logging module

LOG_TO_FILE:
    TRUE*
    FALSE

LOG_TO_STDOUT:
    TRUE*
    FALSE
"""
# Standard Library imports
import logging
import os
import sys

# get environment variables
# if they are missing, set default values
LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL")
if LOGGING_LEVEL is None:
    LOGGING_LEVEL = "DEBUG"

LOG_TO_FILE = os.environ.get("LOG_TO_FILE")
if LOG_TO_FILE is None:
    LOG_TO_FILE = True
elif LOG_TO_FILE.lower() == "false":
    LOG_TO_FILE = False
else:
    LOG_TO_FILE = True

LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
if LOG_TO_STDOUT is None:
    LOG_TO_STDOUT = True
elif LOG_TO_STDOUT.lower() == "false":
    LOG_TO_STDOUT = False
else:
    LOG_TO_STDOUT = True


def getLogger(name: str):
    """Return a configured logger

    Args:
        name (str): the invoking module's __name__

    Returns:
        A logger for a specific file.
    """
    logging_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    logger = logging.getLogger(name)
    formatter = logging.Formatter("%(asctime)s:%(name)s:%(message)s")
    logger.setLevel(logging_levels[LOGGING_LEVEL])
    if LOG_TO_FILE:
        file_handler = logging.FileHandler(f"{__name__}.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    if LOG_TO_STDOUT:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    return logger
