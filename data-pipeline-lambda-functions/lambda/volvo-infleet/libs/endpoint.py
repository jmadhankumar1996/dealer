# endpoint.py

from dataclasses import dataclass

@dataclass
class Endpoint:
    auth_url: str
    base_url: str