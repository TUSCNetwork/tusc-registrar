import logging
import sys
import os
__all__ = ["setup_custom_logger"]


class LoggerWriter:
    def __init__(self, level):
        # self.level is really like using log.debug(message)
        # at least in my case
        self.level = level

    def write(self, message):
        # if statement reduces the amount of newlines that are
        # printed to the logger
        if message != '\n':
            self.level(message)

    def flush(self):
        # create a flush method so things can be flushed when
        # the system wants to. Not sure if simply 'printing'
        # sys.stderr is the correct way to do it, but it seemed
        # to work properly for me.
        self.level(sys.stderr)

def setup_custom_logger(name, subdir):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    s_handler = logging.StreamHandler()
    s_handler.setFormatter(formatter)
    f_handler = logging.FileHandler(filename=os.path.join(os.getcwd(), subdir, name + '.log'))
    f_handler.setFormatter(formatter)

    inner_logger = logging.getLogger(name)
    inner_logger.setLevel(logging.DEBUG)
    # sys.stdout = LoggerWriter(inner_logger.debug)
    # sys.stderr = LoggerWriter(inner_logger.debug)
    # inner_logger.addHandler(s_handler)
    # inner_logger.addHandler(f_handler)
    logging.root.handlers = [s_handler, f_handler]

    return inner_logger
