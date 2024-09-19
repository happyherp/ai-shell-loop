# ai_shell/logger.py

import logging
import os
from datetime import datetime
from appdirs import user_log_dir

def setup_logging():
    app_name = "ai-shell-loop"
    app_author = "Carlos Freund"

    # Allow custom log directory via environment variable
    custom_log_dir = os.getenv("AI_SHELL_LOOP_LOG_DIR")
    if custom_log_dir:
        log_directory = custom_log_dir
    else:
        log_directory = user_log_dir(app_name, app_author)

    os.makedirs(log_directory, exist_ok=True)

    # Create a log file with current date and time
    log_filename = datetime.now().strftime("ai-shell-loop_%Y-%m-%d_%H-%M-%S.log")
    log_filepath = os.path.join(log_directory, log_filename)

    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Default level

    # Create a file handler
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(logging.INFO)  # Set handler level

    # Create a logging format
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(file_handler)

    # Optionally, add a debug handler if needed
    debug_level = os.getenv("AI_SHELL_LOOP_LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, debug_level, logging.INFO))

    return log_filepath
