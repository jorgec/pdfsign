import base64
from typing import Dict

import requests

from .http_config import HTTP_GET, HTTPConfig, HTTP_POST
from .http_connection import HTTPConnection


class APIManager:
    public_api_key: str = None
    secret_api_key: str = None
    environment: str = None
    http_headers: Dict = None
    encoded_key: str = None
    token: str = None

    auth_method: str = None

    def __init__(
            self,
            public_api_key: str = None,
            secret_api_key: str = None,
            token: str = None,
            environment: str = "LOCAL",
            encoded_key: str = None,
            auth_method: str = "token"
    ):
        self.public_api_key = public_api_key
        self.secret_api_key = secret_api_key
        self.token = token
        self.environment = environment
        self.http_headers = {"Content-Type": "application/json"}
        if encoded_key:
            self.encoded_key = encoded_key

        self.auth_method = auth_method

    def use_token_auth(self):
        if not self.token:
            raise ValueError("Token required")

        self.http_headers["Authorization"] = f"Token {self.token}"

    def use_basic_auth_with_api_key(self, api_key: str = None):
        if not api_key and not self.encoded_key:
            raise ValueError("API Key is required")

        if self.encoded_key:
            token = self.encoded_key
        else:
            token = base64.b64encode(api_key.encode("utf-8")).decode()
        self.http_headers["Authorization"] = f"Basic {token}:"

    def execute(
            self, url: str, key: str = "secret", method: str = HTTP_POST, payload=None
    ) -> requests.Response:
        if key == "public":
            api_key = self.public_api_key
        else:
            api_key = self.secret_api_key

        if self.auth_method == "token":
            self.use_token_auth()
        else:
            self.use_basic_auth_with_api_key(api_key)

        http_config = HTTPConfig(url=url, method=method, headers=self.http_headers)
        http_connection = HTTPConnection(config=http_config)

        return http_connection.execute(data=payload)

    def query(
            self, key: str = "secret", method: str = HTTP_GET, url: str = None
    ) -> requests.Response:
        if key == "public":
            api_key = self.public_api_key
        else:
            api_key = self.secret_api_key

        self.use_basic_auth_with_api_key(api_key)

        http_config = HTTPConfig(url=url, method=method, headers=self.http_headers)
        http_connection = HTTPConnection(config=http_config)

        response = http_connection.execute(data=None)
        return response
