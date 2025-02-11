from typing import Dict, List
from urllib.parse import urlencode

from django.conf import settings

from .core.endpoints import SDKEndpoints
from .core.http_config import HTTPConfig, HTTP_POST, HTTP_GET, HTTP_DELETE
from .core.http_connection import HTTPConnection


class GenericSDK:
    endpoints: SDKEndpoints = None
    headers: Dict = {}

    def __init__(self):
        self.endpoints = SDKEndpoints()
        self.prep_headers()

    def prep_headers(self):
        API_KEY = None  # settings.CURVE_CORE_API_KEY
        TOKEN = None  # settings.CURVE_APP_TOKEN

        headers = {
            "Authorization": f"Token {TOKEN}",
            "API-KEY": API_KEY
        }
        self.headers = {
            **self.headers,
            **headers
        }

    def execute(self, url: str, method: str, data: Dict = None):
        config = HTTPConfig(
            url=url,
            method=method,
            headers=self.headers
        )
        conn = HTTPConnection(config=config)

        result = conn.execute(data=data)
        return result
