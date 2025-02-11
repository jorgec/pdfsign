import os


class SDKEndpoints:
    env: str = "local"

    LOCAL = "http://192.168.4.27:8000"
    ROBERT = ""
    STAGING = "https://demo.curveph.com"
    PRODUCTION = "https://curveph.app"

    def __init__(self):
        self.env = os.environ.get('curve_sponsors__core_env', 'local')

    def get_base_url(self):
        return getattr(self, self.env.upper())

