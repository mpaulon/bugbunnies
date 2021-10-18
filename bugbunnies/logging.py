import logging
import colorlog

def getLogger(name, verbose=0, log_path=None):
    logger = logging.getLogger(name)

    format_string = "%(asctime)s - %(levelname)s - %(message)s"

    stdout_handler = logging.StreamHandler()
    stdout_formatter = colorlog.ColoredFormatter(f"%(log_color)s {format_string}")
    stdout_handler.setFormatter(stdout_formatter)
    logger.addHandler(stdout_handler)


    if log_path is not None:
        file_handler = logging.FileHandler(log_path)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    if verbose == 0:
        logger.setLevel(logging.INFO)
    elif verbose >= 1:
        logger.setLevel(logging.DEBUG)


    return logger