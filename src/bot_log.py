import os
import logging
from logging.handlers import TimedRotatingFileHandler
from colorama import Fore, Style, init
from datetime import datetime, time, timedelta

# Initialize colorama for cross-platform compatibility (Windows, etc.)
init(autoreset=True)

class CustomFormatter(logging.Formatter):
    # Define colors for each log level
    LEVEL_COLORS = {
        logging.DEBUG: Fore.WHITE,
        logging.INFO: Fore.BLUE,
        logging.WARNING: Fore.LIGHTYELLOW_EX,  # Orange equivalent in colorama
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED,
    }

    def formatTime(self, record, datefmt=None):
        # Get the current time and round to the nearest second
        record.created = round(record.created)
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        return f"{Style.BRIGHT}{Fore.LIGHTBLACK_EX}{timestamp}{Style.RESET_ALL}"  # Darker color for the timestamp

    def format(self, record):
        # Apply color to levelname
        level_color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)
        record.levelname = f"{Style.BRIGHT}{level_color}{record.levelname}{Style.RESET_ALL}"
        
        # Apply magenta color to logger name
        record.name = f"{Fore.MAGENTA}{record.name}{Style.RESET_ALL}"
        
        # Apply white color to message
        record.msg = f"{Fore.WHITE}{record.msg}{Style.RESET_ALL}"
        
        # Format the final log string
        return super().format(record)

# Ensure the "logs" folder exists
if not os.path.exists("logs"):
    os.makedirs("logs")

# Specify the custom rotation time
rotation_time = time(23, 59, 59)

# Function to determine the correct log file name based on the current time
def get_log_filename():
    now = datetime.now()
    # If the current time is before the rotation time, use today's date
    if now.time() < rotation_time:
        log_date = now
    else:
        # Otherwise, use tomorrow's date
        log_date = now + timedelta(days=1)
    return log_date.strftime("logs/%Y-%m-%d.log")

class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def doRollover(self):
        """
        Override the `doRollover` to reset the log file to the correct new name
        without retaining old logs in the new file.
        """
        # Close the current log file
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Update the log file name dynamically based on the current time
        self.baseFilename = get_log_filename()
        
        # Open a new log file
        self.stream = self._open()

# Create a TimedRotatingFileHandler for daily log rotation
file_handler = CustomTimedRotatingFileHandler(
    filename=get_log_filename(),
    when="midnight",  # Rotate logs at midnight
    interval=1,       # Every 1 day
    atTime=rotation_time,   # Rotate logs at 6:00 AM
    backupCount=7,    # Keep the last 7 log files
    encoding="utf-8"  # Ensure proper encoding
)

file_handler.namer = lambda name: get_log_filename()

# Create a custom formatter for the file handler (no colors for file logs)
file_formatter = logging.Formatter("%(asctime)s %(levelname)s     %(name)s %(message)s")
file_handler.setFormatter(file_formatter)

# Configure the console handler to use the custom formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(CustomFormatter("%(asctime)s %(levelname)s     %(name)s %(message)s"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Log level (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    handlers=[
        file_handler,
        console_handler
    ]
)

# Create a logger instance
log = logging.getLogger("bot")

'''
log.debug("This is a debug message.")
log.info("This is an info message.")
log.warning("This is a warning message.")
log.error("This is an error message.")
log.critical("This is a critical message.")
'''