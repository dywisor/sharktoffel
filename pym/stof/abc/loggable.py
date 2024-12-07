# stof -- __init__
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

import abc
import logging

from typing import Optional


__all__ = ["AbstractLoggable"]


class AbstractLoggable(object, metaclass=abc.ABCMeta):
    """Base class for objects with a logger.

    @cvar DEFAULT_LOGGER_NAME:  default logger name,
                                the class name is used if empty/None,
                                see C{get_default_logger_name()}
    @type DEFAULT_LOGGER_NAME:  C{str} or C{None}

    @ivar logger:  logger
    @type logger:  L{logging.Logger}
    """

    __slots__ = ["logger"]

    DEFAULT_LOGGER_NAME: Optional[str] = None

    LOGGABLE_KWARGS = frozenset({"logger", "logger_name", "parent_logger"})

    @classmethod
    def loggable_split_kwargs_inplace(cls, kwargs: dict[str, object]) -> None:
        """
        Removes loggable keyword arguments from the given dict
        and returns them in a new dict.

        @param kwargs:  keyword arguments (packed) -- will be modified in-place
        @type  kwargs:  C{dict} :: C{object} => C{object}

        @return: loggable keyword arguments
        @rtype:  C{dict} :: C{str} => C{object}
        """
        log_kwargs = {}

        for key in cls.LOGGABLE_KWARGS:
            try:
                log_kwargs[key] = kwargs.pop(key)
            except KeyError:
                pass
        # --

        return log_kwargs

    # --- end of loggable_split_kwargs_inplace (...) ---

    def get_default_logger_name(self) -> str:
        """
        Returns the default name for new loggers.

        @return:  default logger name
        @rtype:   C{str}
        """
        return self.DEFAULT_LOGGER_NAME or self.__class__.__name__

    def __init__(
        self,
        *,
        logger: Optional[logging.Logger] = None,
        logger_name: Optional[str] = None,
        parent_logger: Optional[logging.Logger] = None
    ):
        """Constructor.

        @keyword logger:         logger, if this parameter is not None,
                                 then logger_name and parent_logger will be
                                 ignored. Defaults to None.
        @type    logger:         C{logging.Logger} or C{None}
        @keyword logger_name:    logger name, used when creating a new one
        @type    logger_name:    C{str} or C{None}
        @keyword parent_logger:  parent logger, which will be used to create
                                 a child logger if logger is not set.
                                 Defaults to None.
        @type    parent_logger:  L{logging.Logger} or C{None}
        """
        super().__init__()
        self.logger = None
        self.set_logger(
            logger=logger, logger_name=logger_name, parent_logger=parent_logger
        )

    # --- end of __init__ (...) ---

    def get_child_logger(self, *args, **kwargs) -> logging.Logger:
        """Creates a new logger that is a child of this class' logger."""
        return self.logger.getChild(*args, **kwargs)

    # --- end of get_child_logger (...) ---

    def create_loggable(
        self, loggable_cls: type, *args, **kwargs
    ) -> "AbstractLoggable":
        """Creates a new object and attaches a child logger to it."""
        kwargs.setdefault("parent_logger", self.logger)
        return loggable_cls(*args, **kwargs)

    # --- end of create_loggable (...) ---

    def set_logger(
        self,
        logger: Optional[logging.Logger] = None,
        *,
        logger_name: Optional[str] = None,
        parent_logger: Optional[logging.Logger] = None
    ) -> None:
        """Sets the logger to be used by this class.

        Typically, either logger or parent_logger should be specified.
        If both are present, logger takes precedence.
        If none have been given, the root logger is used as parent logger instead.

        @return:  None (implicit)
        """
        if logger is not None:
            self.logger = logger
        else:
            logger_name = logger_name or self.get_default_logger_name()

            if parent_logger is None:
                self.logger = logging.getLogger(logger_name)
            elif isinstance(parent_logger, AbstractLoggable):
                self.logger = parent_logger.get_child_logger(logger_name)
            else:
                self.logger = parent_logger.getChild(logger_name)
            # --
        # --

    # --- end of set_logger (...) ---


# --- end of AbstractLoggable ---
