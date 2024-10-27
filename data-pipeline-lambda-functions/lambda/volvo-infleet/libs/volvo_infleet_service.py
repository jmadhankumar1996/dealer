# volvo_infleet_service.py

import logging
from libs.secrets_manager import SecretsManager
from libs.endpoint import Endpoint

# Set up logging
logger = logging.getLogger("OEM_Infleeter")

class VolvoInfleetService:
    def __init__(self, loaner_secret_name: str, order_secret_name: str):
        self.loaner_endpoint = self._get_endpoint_from_secret(loaner_secret_name)
        self.order_endpoint = self._get_endpoint_from_secret(order_secret_name)

    def _get_endpoint_from_secret(self, secret_name: str) -> Endpoint:
        secrets_manager = SecretsManager(secret_name)
        secret_data = secrets_manager.get_secret()
        auth_url = secret_data.get("auth_url")
        base_url = secret_data.get("base_url")
        
        if not auth_url or not base_url:
            logger.error("Secret %s is missing 'auth_url' or 'base_url'.", secret_name)
            raise ValueError(f"Secret {secret_name} is missing required fields.")
        
        return Endpoint(auth_url=auth_url, base_url=base_url)

    def get_loaner_endpoint(self) -> Endpoint:
        return self.loaner_endpoint

    def get_order_endpoint(self) -> Endpoint:
        return self.order_endpoint
