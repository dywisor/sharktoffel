# stof -- abstract base class for API clients
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

import json
import requests

from . import _abc

# from . import exc


__all__ = ["APIClient"]


class APIClient(_abc.AbstractAPIClient):
    """
    A base class for implementing API clients using python-requests.
    The data format defaults to JSON, but can be adjusted if necessary.

    @ivar session: api client session (only when client is active)
    @type session: L{requests.Session}
    """

    __slots__ = ["_session"]

    DEFAULT_CONTENT_TYPE = "application/json"
    DEFAULT_ACCEPT_CONTENT_TYPE = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = None

    # --- end of __init__ (...) ---

    @property
    def session(self):
        session = self._session

        if session is None:
            raise AssertionError("no active session found")

        else:
            return session

    # --- end of property session (...) ---

    def open_connection(self):
        session = requests.Session()

        try:
            session.verify = self.verify_cert

            session.headers["Host"] = self.real_host

            content_type = self.DEFAULT_CONTENT_TYPE
            if content_type:
                session.headers["Content-Type"] = content_type

            accept_content_type = self.DEFAULT_ACCEPT_CONTENT_TYPE
            if accept_content_type is True:
                session.headers["Accept"] = content_type or "*/*"
            elif accept_content_type:
                session.headers["Accept"] = accept_content_type
            # --

            session.headers.update(self.headers)

        except:
            session.close()
            raise

        else:
            self._session = session

    # --- end of open_connection (...) ---

    def close_connection(self):
        session = self._session
        if session is not None:
            session.close()
            self._session = None
        # --

    # --- end of close_connection (...) ---

    def convert_response_text(self, text):
        return json.loads(text)

    def _request(self, method, url, *, nolog_url=False, **kwargs):
        url_log_value = "NOT_LOGGING_URL" if nolog_url else url

        self.logger.debug("API %s request: %s", method, url_log_value)

        response = self.session.request(method, url, **kwargs)

        self.logger.debug(
            "API %s response status: %s: %s",
            method,
            response.status_code,
            url_log_value,
        )

        return response

    # --- end of _request (...) ---


# --- end of APIClient ---
