import requests
from loguru import logger

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def check_health(self, endpoint):
        """
        Returns (status_code, body_dict).
        body_dict is parsed JSON if available, otherwise empty dict.
        On request exception, returns (500, {}).
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, timeout=10)
            logger.info(f"API Check: {url} -> Status: {response.status_code}")
            try:
                body = response.json()
            except Exception:
                body = {}
            return response.status_code, body
        except Exception as e:
            logger.error(f"API Check Failed: {e}")
            return 500, {}

    def post_login(self, username: str, password: str):
        """
        POST to OrangeHRM JSON login API.
        Returns (status_code, body_dict).
        body_dict is parsed JSON if available, otherwise empty dict.
        """
        url = f"{self.base_url}/api/v2/auth/login"
        payload = {"username": username, "password": password}
        try:
            response = requests.post(url, json=payload, timeout=10)
            logger.info(f"API Login POST: {url} -> Status: {response.status_code}")
            try:
                body = response.json()
            except Exception:
                # Site returned HTML (e.g. redirect) — body is not JSON
                body = {}
            return response.status_code, body
        except Exception as e:
            logger.error(f"API Login POST Failed: {e}")
            return 500, {}
