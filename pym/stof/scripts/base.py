# stof -- scripts/base
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = ["ExitCodes", "MainScript"]

import abc
import argparse
import contextlib
import enum
import logging
import os
import signal
import sys

from typing import Optional, Union

from ..abc import loggable
from ..util import argutil


class ExitCodes(enum.IntEnum):
    EX_OK = getattr(os, "EX_OK", 0)
    EX_ERR = EX_OK ^ 1
    EX_BROKEN_PIPE = 11
    EX_USAGE = getattr(os, "EX_USAGE", 64)
    EX_KEYBOARD_INTERRUPT = EX_OK ^ 130


# --- end of ExitCodes ---


class MainScript(loggable.AbstractLoggable):
    __slots__ = ["prog", "stdin", "stdout", "stderr", "setup_logger"]

    EXIT_CODES = ExitCodes

    ARG_TYPES = argutil.ArgTypes

    CONSOLE_LOG_FMT = "%(levelname)-8s [%(name)s] %(message)s"

    @classmethod
    def main(cls, prog=None, argv=None, **kwargs) -> None:
        if prog is None:
            prog = sys.argv[0]

        if argv is None:
            argv = sys.argv[1:]

        main_script = cls(prog=prog, **kwargs)
        exit_code = main_script.run(argv)
        sys.exit(exit_code)

    # --- end of main (...) ---

    @abc.abstractproperty
    def VERSION(cls) -> str:
        raise NotImplementedError(cls)

    @abc.abstractproperty
    def DESCRIPTION(cls) -> str:
        """Returns a one-liner describing this script."""
        raise NotImplementedError(cls)

    @property
    def LONG_DESCRIPTION(cls) -> Optional[str]:
        """Optionally, a long description may be defined using this property."""
        return None

    @abc.abstractmethod
    def __call__(self, arg_config: argparse.Namespace) -> Union[None, bool, int]:
        """
        This method should implement the actual main script functionality.

        @param arg_config:  parsed arguments
        @type  arg_config:  C{argparse.Namespace}

        @return:  None, True, False or exit code
        @rtype:   C{None} or C{bool} or C{int}
        """
        raise NotImplementedError(self)

    # --- end of __call__ (...) ---

    @abc.abstractmethod
    def setup_argument_parser(self, arg_parser: argparse.ArgumentParser) -> None:
        pass

    # --- end of setup_argument_parser (...) ---

    def cleanup(self) -> None:
        """Performs necessary cleanup actions."""
        pass

    # --- end of cleanup (...) ---

    def prepare(self) -> None:
        """Performs script init actions."""
        pass

    # --- end of prepare (...) ---

    def load_config(self, arg_config: argparse.Namespace) -> None:
        """Loads script configuration. (no-op unless overridden)."""
        pass

    # --- end of load_config (...) ---

    def get_prog_name(self) -> str:
        return os.path.basename(self.prog)

    # --- end of get_prog_name (...) ---

    prog_name = property(get_prog_name)

    def __init__(
        self, prog, stdin=None, stdout=None, stderr=None, setup_logger=None, **kwargs
    ):
        self.prog = prog
        self.stdin = stdin if stdin is not None else sys.stdin
        self.stdout = stdout if stdout is not None else sys.stdout
        self.stderr = stderr if stderr is not None else sys.stderr

        if "logger_name" not in kwargs:
            kwargs["logger_name"] = self.get_prog_name()
        # --

        self.setup_logger = bool(
            "logger" not in kwargs and "parent_logger" not in kwargs
        )

        super().__init__(**kwargs)

    # ---

    def __enter__(self):
        self.prepare()
        return self

    # ---

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.cleanup()

    # ---

    def get_arg_log_level(self, arg_config: argparse.Namespace) -> int:
        log_levels = [
            logging.CRITICAL,
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            logging.DEBUG,
        ]

        # default to WARNING, increase/decrease depending on cmdline -v/-q
        verbosity = 2 + arg_config.verbose - arg_config.quiet

        if verbosity < 0:
            return log_levels[0]
        elif verbosity >= len(log_levels):
            return log_levels[-1]
        else:
            return log_levels[verbosity]

    def setup_logging(self, arg_config: argparse.Namespace) -> None:
        """
        Set up logging.
        The default implementation initialized console stderr logging
        and removes any previous log handlers.
        """
        log_level = self.get_arg_log_level(arg_config)
        self.zap_log_handlers()
        self.setup_console_logging(log_level=log_level)

    # --- end of setup_logging (...) ---

    def zap_log_handlers(self) -> None:
        """Removes all handlers from the logger."""
        log_handlers = list(self.logger.handlers)
        for log_handler in log_handlers:
            self.logger.removeHandler(log_handler)

    # ---

    def setup_console_logging(self, log_level, outstream=None) -> None:
        """Attaches a stream handler to the logger.
        By default, it writes to stderr.

        @param   log_level:  log level
        @keyword outstream:  output stream. Defaults to None (-> stderr).
        """
        streamhandler = logging.StreamHandler(
            self.stderr if outstream is None else outstream
        )
        streamhandler.setLevel(log_level)

        streamhandler.setFormatter(logging.Formatter(fmt=self.CONSOLE_LOG_FMT))

        self.logger.addHandler(streamhandler)
        self.logger.setLevel(log_level)

    # ---

    def run(self, argv: list[str]) -> int:
        exit_code = None

        try:
            arg_parser = self.get_argument_parser()
            arg_config = arg_parser.parse_args(argv)

            self.load_config(arg_config)

            if self.setup_logger:
                self.setup_logging(arg_config)

            with self:
                exit_code = self(arg_config)

        except KeyboardInterrupt:
            exit_code = self.EXIT_CODES.EX_KEYBOARD_INTERRUPT

        except BrokenPipeError:
            exit_code = self.EXIT_CODES.EX_BROKEN_PIPE

            for fh in [self.stdout, self.stderr]:
                if fh:
                    with contextlib.suppress(IOError):
                        fh.close()

        else:
            if exit_code is None or exit_code is True:
                exit_code = self.EXIT_CODES.EX_OK
            elif exit_code is False:
                exit_code = self.EXIT_CODES.EX_ERR
            # --

        finally:
            signal.signal(signal.SIGUSR1, signal.SIG_DFL)
        # --

        return exit_code

    # --- end of run (...) ---

    def get_argument_parser(self) -> argparse.ArgumentParser:
        kwargs = {
            "prog": self.get_prog_name(),
            "description": self.DESCRIPTION,
        }

        long_desc = self.LONG_DESCRIPTION
        if long_desc:
            kwargs["epilog"] = long_desc

        arg_parser = argparse.ArgumentParser(**kwargs)

        # common parameters
        arg_parser.add_argument(
            "-V", "--version", action="version", version=self.VERSION
        )

        arg_parser.add_argument(
            "-v", "--verbose", action="count", default=0, help="increase verbosity"
        )

        arg_parser.add_argument(
            "-q", "--quiet", action="count", default=0, help="decrease verbosity"
        )

        self.setup_argument_parser(arg_parser)
        return arg_parser

    # --- end of get_argument_parser (...) ---


# --- end of MainScript ---
