import logging
import os

log_level = logging.DEBUG
log_directory = "volume/logs"


def setup_logger(name):
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    logfile_path = os.path.join(log_directory, f"{name}.log")

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if not logger.handlers:
        file_handler = logging.FileHandler(filename=logfile_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return logger
