#logger_config.py
import logging


def setup_logger(name, file_name) -> logging.Logger:
    FORMAT = "[%(name)s %(module)s:%(lineno)s]\n\t %(message)s \n"
    TIME_FORMAT = "%d.%m.%Y %I:%M:%S %p"

    logging.basicConfig(
        format=FORMAT, datefmt=TIME_FORMAT, level=logging.DEBUG, filename=f"req_logs/program.log"
    )

    logger = logging.getLogger(name)
    return logger


