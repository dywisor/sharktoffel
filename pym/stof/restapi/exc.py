# stof -- __init__
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

__all__ = ["APIException", "APICallException"]


class APIException(Exception):
    pass


class APICallException(APIException):
    def __init__(self, status_code=None, response_text=None, message=None, **kwargs):
        self.status_code = status_code
        self.response_text = response_text

        super().__init__((message or response_text), **kwargs)

    # --- end of __init__ (...) ---


# --- end of APICallException ---
