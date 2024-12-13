# stof -- abstract base class for API clients
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

import abc

import urllib.parse


from ..abc import loggable
from . import exc


__all__ = ["AbstractAPIClient"]


class AbstractAPIClient(loggable.AbstractLoggable):
    """A base class for implementing API clients.

    @ivar base_url:     base URL for api calls
    @type base_url:     C{str}
    @ivar real_host:    real api host
                        (may deviate from the host in base_url
                        when the connection is tunneled e.g. via SSH)
    @type real_host:    C{str}
    @ivar verify_cert:  True/False to enable/disable SSL certificate checking
                        or a path to a CA file
    @type verify_cert:  C{bool} or C{str}
    @ivar headers:      default request headers
    @type headers:      C{dict} : C{str} => C{str}
    """

    __slots__ = [
        "base_url",
        "real_host",
        "verify_cert",
        "headers",
    ]

    HTTP_STATUS_CODES_SUCCESS = {200, 201, 202, 203, 204, 205, 206, 207}

    DEFAULT_API_PROTOCOL = "https"
    DEFAULT_API_PORT = None
    DEFAULT_API_BASEPATH = None

    @classmethod
    def parse_api_host_arg(cls, host, *, real_host=None):
        if not cls.DEFAULT_API_PORT:

            def append_default_port(arg):
                return arg

        else:

            def append_default_port(arg, *, port=cls.DEFAULT_API_PORT):
                parts = arg.rpartition(":")

                if arg[0] == "[":
                    # rudimentary IPv6 support
                    if parts[0][-1] == "]":
                        return "{}:{}".format(arg, port)
                    else:
                        return arg

                elif parts[1]:
                    # separator found, could check for non-empty other parts
                    return arg

                else:
                    return "{}:{}".format(arg, port)

            # --- end of append_default_port (...) ---
        # -- end if

        parsed_base_url = None
        parsed_real_host = None

        parts = urllib.parse.urlparse(host)

        if parts.scheme and parts.netloc:
            # assume complete URL
            parsed_base_url = host
            parsed_host = parts.netloc.rpartition("@")[-1]

        else:
            # assume host[:port] only
            parsed_host = append_default_port(host)

            parsed_base_url = "{proto}://{host}/{basepath}".format(
                proto=cls.DEFAULT_API_PROTOCOL,
                host=parsed_host,
                basepath=(cls.DEFAULT_API_BASEPATH or "").lstrip("/"),
            )
        # -- end if

        if not real_host:
            parsed_real_host = parsed_host

        else:
            # append default port to api host?
            parsed_real_host = append_default_port(real_host)
        # --

        return (parsed_base_url, parsed_real_host)

    # --- end of parse_api_host_arg (...) ---

    def __init__(self, host, *, real_host=None, verify_cert=True, **logger_kwargs):
        super().__init__(**logger_kwargs)

        (parsed_base_url, parsed_real_host) = self.__class__.parse_api_host_arg(
            host=host, real_host=real_host
        )

        self.base_url = parsed_base_url
        self.real_host = parsed_real_host
        self.verify_cert = verify_cert
        self.headers = {}

    # --- end of __init__ (...) ---

    def join_url(self, endpoint=None):
        base_url = self.base_url

        if endpoint:
            return "/".join((base_url, endpoint.lstrip("/")))
        else:
            return base_url

    # --- end of join_url (...) ---

    def __enter__(self):
        self.open_connection()

        try:
            self.login()

        except:
            self.close_connection()
            raise

        else:
            return self

    # --- end of __enter__ (...) ---

    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:
            self.logout()
        finally:
            self.close_connection()

    # --- end of __exit__ (...) ---

    @abc.abstractmethod
    def login(self):
        raise NotImplementedError(self)

    @abc.abstractmethod
    def logout(self):
        raise NotImplementedError(self)

    @abc.abstractmethod
    def open_connection(self):
        raise NotImplementedError(self)

    @abc.abstractmethod
    def close_connection(self):
        raise NotImplementedError(self)

    @abc.abstractmethod
    def convert_response_text(self, text):
        raise NotImplementedError(self)

    def add_header(self, name, value):
        self.headers[name] = value

    def unset_header(self, name, *, ignore_missing=True):
        try:
            del self.headers[name]

        except KeyError:
            if not ignore_missing:
                raise

    # --- end of unset_header (...) ---

    def render_response_error(self, text):
        return text

    # --- end of render_response_error (...) ---

    def process_response(self, response, *, errors_ok=False):
        if response.status_code in self.HTTP_STATUS_CODES_SUCCESS:
            return (True, self.convert_response_text(response.text))

        elif errors_ok:
            return (False, None)

        else:
            raise exc.APICallException(
                status_code=response.status_code,
                response_text=response.text,
                message=self.render_response_error(response.text),
            )

    # --- end of process_response (...) ---

    @abc.abstractmethod
    def api_call(self, *args, **kwargs):
        raise NotImplementedError(self)

    @abc.abstractmethod
    def gen_api_query(self, *args, **kwargs):
        raise NotImplementedError(self)

    @abc.abstractmethod
    def api_query(self, *args, **kwargs):
        raise NotImplementedError(self)


# --- end of AbstractAPIClient ---
