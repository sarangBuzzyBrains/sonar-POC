import logging
import os
from .config import PROJECT_WORKING_DIRECTORY
import datetime

def setup_logger(name, file_name='') -> logging.Logger:
    FORMAT = "[%(asctime)s] => %(message)s \n"
    TIME_FORMAT = "%Y-%m-%dT%I:%M:%S"
    FILE_PATH = f"req_logs/{file_name}program.log"

    # Clear existing handlers from the logger
    logger = logging.getLogger(FILE_PATH)
    logger.handlers = []

    file_handler = logging.FileHandler(filename=FILE_PATH, mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(fmt=FORMAT, datefmt=TIME_FORMAT))

    logging.root.addHandler(file_handler)
    logging.root.setLevel(logging.INFO)

    logger = logging.getLogger(FILE_PATH)
    return logger

logger = setup_logger(__file__)


def custom_write_file(prj_key, data):
    current_timestamp = datetime.datetime.now()
    with open(f'{PROJECT_WORKING_DIRECTORY}/req_logs/{prj_key}.log', 'a') as file:
        file.write(f'[{current_timestamp}] {data}\n')
