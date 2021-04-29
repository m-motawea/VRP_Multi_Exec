from loguru import logger
import sys


class GlobalLogger:
    LOGGER = None

    def __new__(cls, *args, **kwargs):
        if cls.LOGGER:
            return cls.LOGGER
        cls.LOGGER = super().__new__(cls, *args, **kwargs)
        return cls.LOGGER

    def __init__(self, level="info") -> None:
        self.level = level
        self._logger = None

    @property
    def logger(self):
        if not self._logger:
            self._logger = logger
            logger.add(
                sys.stderr,
                colorize=True,
                format="<green>{time}</green> <level>{message}</level>",
                filter=lambda record: record["level"].no >= logger.level(self.level.upper()).no,
                level=self.level.upper(),
                backtrace=True,
                diagnose=True,
            )
        return self._logger

    def __getattr__(self, name):
        return getattr(self._logger, name)
