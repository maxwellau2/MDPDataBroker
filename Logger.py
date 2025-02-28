import logging
from colorama import Fore, Style, init
from datetime import datetime

# Initialize colorama
init(autoreset=True)

# Custom Formatter for Colors
class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA + Style.BRIGHT,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)

        # Format the timestamp (ISO 8601 format)
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        return f"{log_color}[{timestamp}] {record.levelname}: {record.getMessage()}{Style.RESET_ALL}"

def createLogger() -> logging.Logger:
    """Simple factory method to create logger with predefined rule sets"""
    # Create Logger
    logger = logging.getLogger("ColoredLogger")
    logger.setLevel(logging.DEBUG)


    # Create File Handler
    file_handler = logging.FileHandler("custom.log")
    file_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Create Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter())

    # Add Handler to Logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Example Logs
    # logger.debug("Debugging info")
    # logger.info("System is running")
    # logger.warning("Low disk space")
    # logger.error("Failed to connect to database")
    # logger.critical("System crash!")
    return logger
