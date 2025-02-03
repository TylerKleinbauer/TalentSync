import logging
from config.settings import LOGGING_FILES, LOGGING_LEVEL, LOGGING_FORMAT
import requests
import os
from dotenv import load_dotenv

class TelegramBotHandler(logging.Handler):
    """
    Custom logging handler that sends logs to a Telegram chat via a bot.
    """
    def __init__(self, bot_token, chat_id, level=logging.ERROR):
        super().__init__(level)
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def emit(self, record):
        try:
            log_entry = self.format(record)
            payload = {
                'chat_id': self.chat_id,
                'text': log_entry,
                'parse_mode': 'Markdown'
            }
            response = requests.post(self.api_url, data=payload, timeout=5)
            response.raise_for_status()
        except Exception:
            self.handleError(record)


def setup_logging():
    """
    Configures logging for the application with separate handlers for INFO, ERROR, and console output.

    This function sets up a centralized logging configuration that:
    - Logs INFO-level and above messages to an `info.log` file.
    - Logs ERROR-level and above messages to an `error.log` file.
    - Logs DEBUG-level and above messages to the console (stream).

    Features:
    ----------
    1. **INFO File Handler**:
       - Writes logs of level INFO and above (INFO, WARNING, ERROR, CRITICAL) to a dedicated log file.
    2. **ERROR File Handler**:
       - Writes logs of level ERROR and above (ERROR, CRITICAL) to a separate error log file.
    3. **Stream Handler**:
       - Outputs logs of level DEBUG and above (DEBUG, INFO, WARNING, ERROR, CRITICAL) to the console.

    Steps:
    ----------
    1. Clears any existing handlers to avoid duplicate logs.
    2. Creates and assigns a `Formatter` to format log messages consistently.
    3. Configures file handlers for `info.log` and `error.log`, and sets their levels and formats.
    4. Configures a stream handler for console logging and sets its level and format.
    5. Attaches all handlers to the root logger.

    Logging Levels:
    ----------
    - DEBUG: Used for detailed diagnostic output (console only).
    - INFO: General informational messages about program operation (info.log and console).
    - WARNING: Messages indicating potential issues (info.log and console).
    - ERROR: Errors that disrupt the flow but do not crash the application (error.log, info.log, and console).
    - CRITICAL: Serious errors requiring immediate attention (error.log, info.log, and console).

    Notes:
    ----------
    - Log file paths, levels, and formats are configurable via external settings or constants.
    - Ensures the root logger is not misconfigured with duplicate handlers.

    Example:
    ----------
    >>> setup_logging()
    >>> logging.info("Application started successfully.")
    >>> logging.error("An error occurred during execution.")
    """

    load_dotenv()
    
    # Create the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOGGING_LEVEL)

    # Create the formatter
    formatter = logging.Formatter(LOGGING_FORMAT)

    # Create handlers
    info_handler = logging.FileHandler(LOGGING_FILES["info"])
    info_handler.setLevel(logging.INFO)  # Logs INFO and above (INFO, WARNING, ERROR, CRITICAL)
    info_handler.setFormatter(formatter)

    error_handler = logging.FileHandler(LOGGING_FILES["error"])
    error_handler.setLevel(logging.ERROR)  # Logs ERROR and above (ERROR, CRITICAL)
    error_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()  # Optional: To display logs in the console
    stream_handler.setLevel(logging.DEBUG)  # Adjust this level as needed
    stream_handler.setFormatter(formatter)

    # Clear any existing handlers to prevent duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Add the handlers to the root logger
    root_logger.addHandler(info_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(stream_handler)

   # Add Telegram handler (only for ERROR and above)
    bot_token = os.getenv("TELEGRAM_API_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if bot_token and chat_id:
      telegram_handler = TelegramBotHandler(bot_token, chat_id, level=logging.ERROR)
      telegram_handler.setFormatter(formatter)
      root_logger.addHandler(telegram_handler)
      logging.debug("[setup_logging] Telegram handler added successfully.")
    else:
      logging.warning("[setup_logging] Telegram bot token or chat ID not set. Telegram notifications disabled.")
