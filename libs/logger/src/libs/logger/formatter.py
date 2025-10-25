"""Custom log formatter.

Format: YYYYMMDD HHMMSS.000 L 0x00001a2b 0x00007f3c module.name "message"
"""

import logging
import os
import threading
from datetime import datetime


class CustomFormatter(logging.Formatter):
    """Custom formatter with process ID, thread ID, and structured format.

    Format: YYYYMMDD HHMMSS.000 L 0xPROCID__ 0xTHREAD__ module.name "message"

    Level mapping:
        C = CRITICAL
        E = ERROR
        W = WARNING
        I = INFO
        D = DEBUG
    """

    LEVEL_MAP = {
        logging.CRITICAL: "C",
        logging.ERROR: "E",
        logging.WARNING: "W",
        logging.INFO: "I",
        logging.DEBUG: "D",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record.

        Args:
            record: LogRecord to format

        Returns:
            Formatted log string
        """
        # Get timestamp with milliseconds
        dt = datetime.fromtimestamp(record.created)
        timestamp = dt.strftime("%Y%m%d %H%M%S")
        milliseconds = int((record.created - int(record.created)) * 1000)
        timestamp_full = f"{timestamp}.{milliseconds:03d}"

        # Get level as single character
        level_char = self.LEVEL_MAP.get(record.levelno, "I")

        # Get process and thread IDs in hex with 8-char padding
        process_id = f"0x{os.getpid():08x}"
        thread_id = f"0x{threading.get_ident():08x}"

        # Get module name
        module_name = record.name

        # Get message
        message = record.getMessage()

        # Build formatted log line
        return f'{timestamp_full} {level_char} {process_id} {thread_id} {module_name} "{message}"'
