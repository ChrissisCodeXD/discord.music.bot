import logging
import colorama


class CustomFormatter(logging.Formatter):
    f = colorama.Fore
    grey = f.LIGHTWHITE_EX
    yellow = f.YELLOW
    red = f.RED
    style = f"{colorama.Style.BRIGHT}"
    reset = f.RESET + colorama.Style.RESET_ALL
    format = "%(asctime)s - %(name)s - {0}[ %(levelname)s ]{1} - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format.format(f.GREEN, grey) + reset,
        logging.INFO: grey + format.format(f.GREEN, grey) + reset,
        logging.WARNING: grey + format.format(f.YELLOW, grey) + reset,
        logging.ERROR: grey + format.format(f.RED, grey) + reset,
        logging.CRITICAL: style + grey + format.format(red, grey) + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
