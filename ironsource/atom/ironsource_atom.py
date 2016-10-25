import json
import hmac
import requests
import hashlib
import ironsource.atom.atom_logger as logger
from ironsource.atom.request import Request
import ironsource.atom.config as config


class IronSourceAtom:
    """
        ironSource Atom low level API. supports put_event() and put_events() methods.
    """

    TAG = "IronSourceAtom"

    def __init__(self, is_debug=False, endpoint=config.ATOM_URL):
        """
        Atom class init function
        :param is_debug: Enable/Disable debug
        :param endpoint: Atom API Endpoint
        """

        self._endpoint = endpoint
        self._auth_key = ""
        self._is_debug = is_debug

        self._headers = {
            "x-ironsource-atom-sdk-type": "python",
            "x-ironsource-atom-sdk-version": config.SDK_VERSION
        }

        # init logger
        self._logger = logger.get_logger(debug=self._is_debug)

    def enable_debug(self, is_debug):  # pragma: no cover
        """
        Enable / Disable debug - this is here for compatibility reasons

        :param is_debug: enable printing of debug info
        :type is_debug: bool
        """
        self.set_debug(is_debug)

    def set_debug(self, is_debug):  # pragma: no cover
        """
        Enable / Disable debug

        :param is_debug: enable printing of debug info
        :type is_debug: bool
        """
        self._is_debug = is_debug if isinstance(is_debug, bool) else False
        self._logger = logger.get_logger(debug=is_debug)

    def set_auth(self, auth_key):
        """
        Set HMAC authentication key

        :param auth_key: HMAC auth key for your stream
        :type auth_key: str
        """
        self._auth_key = auth_key

    def set_endpoint(self, endpoint):
        """
        Set Atom Endpoint url

        :param endpoint: Atom API endpoint
        :type endpoint: str
        """
        self._endpoint = endpoint

    def get_endpoint(self):
        """
        Get current Atom API endpoint

        :rtype: str
        """
        return self._endpoint

    def get_auth(self):
        """
        Get HMAC authentication key

        :rtype: str
        """
        return self._auth_key

    def put_event(self, stream, data, method="POST", auth_key=""):
        """Send a single event to Atom API

        This method exposes two ways of sending your events. Either by HTTP(s) POST or GET.

        :param method: The HTTP(s) method to use when sending data - default is POST
        :type method: str
        :param stream: Atom Stream name
        :type stream: str
        :param data: Data (payload) that should be sent to the server
        :type data: object
        :param auth_key: Hmac auth key
        :type auth_key: str

        :return: requests response object
        """
        if not data or not stream:
            raise Exception("Stream and/or Data are required")
        if len(auth_key) == 0:
            auth_key = self._auth_key

        request_data = self.create_request_data(stream, auth_key, data)

        return self.send_data(url=self._endpoint, data=request_data, method=method,
                              headers=self._headers)

    def put_events(self, stream, data, auth_key=""):
        """Send multiple events (batch) to Atom API

        This method receives a list of dictionaries, transforms them into JSON objects and sends them
        to Atom using HTTP(s) POST.

        :param stream: Atom Stream name
        :type stream: str
        :param data: a string of data to send to the server
        :type data: list(str)
        :param auth_key: a string of data to send to the server
        :type auth_key: str

        :return: requests response object
        """
        if not isinstance(data, list) or not data:
            raise Exception("Data has to be of a non-empty list")
        if not stream:
            raise Exception("Stream is required")
        if len(auth_key) == 0:
            auth_key = self._auth_key

        data = json.dumps(data)
        request_data = self.create_request_data(stream, auth_key, data, batch=True)

        return self.send_data(url=self._endpoint + "bulk", data=request_data, method="post",
                              headers=self._headers)

    @staticmethod
    def create_request_data(stream, auth_key, data, batch=False):
        """
        Create json data string from input data

        :param stream: the stream name
        :type stream: str
        :param auth_key: secret key for stream
        :type auth_key: str
        :param data: data to send to the server
        :type data: object
        :param batch: send data by batch(bulk)
        :type batch: bool

        :return: json data
        :rtype: str
        """
        if not isinstance(data, str):
            try:
                data = json.dumps(data)
            except TypeError:
                raise Exception("Cannot Encode JSON")

        request_data = {"table": stream, "data": data}

        if len(auth_key) != 0:
            request_data["auth"] = hmac.new(bytes(auth_key.encode("utf-8")),
                                            msg=data.encode("utf-8"),
                                            digestmod=hashlib.sha256).hexdigest()

        if batch:
            request_data["bulk"] = True

        return json.dumps(request_data)

    @staticmethod
    def send_data(url, data, method, headers):
        """
        :param headers: HTTP request headers
        :type headers: dict
        :param url: Atom API endpoint
        :type url: str
        :param data: data to send to the server
        :type data: str
        :param method: type of HTTP request
        :type method: str

        :return: response from server
        :rtype: Response
        """
        with requests.Session() as session:
            session.headers.update(headers)
            request = Request(url, data, session)
            if method.lower() == "get":
                return request.get()
            else:
                return request.post()
