import logging
from logging.handlers import RotatingFileHandler


class Logger:

    """
    A logger class that handles application logging with rotating file handling.

    Attributes:
        LOG_FILE (str): Path to the log file.
        MAX_FILE_SIZE (int): Maximum size of the log file in bytes before rotation.
        BACKUP_COUNT (int): Number of backup log files to keep.
    """

    LOG_FILE = "logs/app.log"
    MAX_FILE_SIZE = 1024**3 # 1 GB
    BACKUP_COUNT = 4

    def __init__(self):

        """
        Initializes the Logger instance by setting up a rotating file handler with a specific log format and level.
        """

        self.handler = RotatingFileHandler(self.LOG_FILE, maxBytes=self.MAX_FILE_SIZE, backupCount=self.BACKUP_COUNT, encoding="utf-8")
        self.handler.setLevel(logging.INFO)

        self.formatter = logging.Formatter(u'%(asctime)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

    def get_logger(self) -> logging.Logger:

        """
        Returns the configured logger instance.

        Returns:
            logging.Logger: The configured logger object.
        """

        return logging.getLogger()