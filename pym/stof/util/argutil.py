# stof -- util/argutil
# -*- coding: utf-8 -*-

import argparse
import pathlib


__all__ = ["ArgTypes"]


class ArgTypes(object):

    @classmethod
    def arg_nonempty(cls, arg: str) -> str:
        if not arg:
            raise argparse.ArgumentTypeError("arg must not be empty")
        return arg

    @classmethod
    def arg_fspath(cls, arg: str) -> pathlib.Path:
        if not arg:
            raise argparse.ArgumentTypeError("arg must not be empty")
        return pathlib.Path(arg).expanduser().absolute()

    @classmethod
    def arg_realpath(cls, arg: str) -> pathlib.Path:
        return cls.arg_fspath(arg).resolve()

    @classmethod
    def arg_existing_realpath(cls, arg: str) -> pathlib.Path:
        return cls.arg_fspath(arg).resolve(strict=True)

    @classmethod
    def arg_existing_file(cls, arg: str) -> pathlib.Path:
        filepath = cls.arg_existing_realpath(arg)
        if not filepath.is_file():
            raise argparse.ArgumentTypeError(f"not a file: {arg}")

        return filepath

    @classmethod
    def arg_existing_dir(cls, arg: str) -> pathlib.Path:
        dirpath = cls.arg_existing_realpath(arg)

        if not dirpath.is_dir():
            raise argparse.ArgumentTypeError(f"not a dir: {arg}")

        return dirpath


# --- end of ArgTypes ---
