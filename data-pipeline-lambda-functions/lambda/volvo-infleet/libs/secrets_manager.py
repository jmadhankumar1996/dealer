"""
This module provides functionality for managing secrets and configurations
for the Volvo InFleet service integration.
"""

import json
import logging
from pathlib import Path

import boto3
import yaml

from dataclasses import dataclass, field
from typing import Any, Dict
from libs.endpoint import Endpoint

logger = logging.getLogger("OEM_Infleeter")


class SecretsManager:
    """
    A class to manage secrets using AWS Secrets Manager.
    """

    def __init__(self, secret_name: str):
        """
        Initialize the SecretsManager with a secret name.

        Args:
            secret_name (str): The name of the secret to retrieve.
        """
        self.secret_name = secret_name
        logger.info("SecretsManager initialized with secret name: %s", secret_name)

    def get_secret(self) -> Dict[str, Any]:
        """
        Retrieve the secret from AWS Secrets Manager.

        Returns:
            dict: The secret as a dictionary.

        Raises:
            Exception: Various exceptions for specific error cases.
        """
        logger.info("Attempting to retrieve secret: %s", self.secret_name)
        try:
            secrets_client = boto3.client("secretsmanager")
            get_secret_value_response = secrets_client.get_secret_value(
                SecretId=self.secret_name
            )
            if "SecretString" in get_secret_value_response:
                secret = get_secret_value_response["SecretString"]
            else:
                secret = get_secret_value_response["SecretBinary"]

            logger.info("Secret retrieved successfully.")
            return json.loads(secret)
        except Exception as e:
            error_message = str(e)
            if "DecryptionFailureException" in error_message:
                logger.error("Decryption failure for secret %s", self.secret_name)
                raise Exception("Decryption failure") from e
            if "InternalServiceErrorException" in error_message:
                logger.error(
                    "Internal service error when retrieving secret %s", self.secret_name
                )
                raise Exception("Internal service error") from e
            if "InvalidParameterException" in error_message:
                logger.error("Invalid parameter for secret %s", self.secret_name)
                raise Exception("Invalid parameter") from e
            if "InvalidRequestException" in error_message:
                logger.error("Invalid request for secret %s", self.secret_name)
                raise Exception("Invalid request") from e
            if "ResourceNotFoundException" in error_message:
                logger.error("Resource not found for secret %s", self.secret_name)
                raise Exception("Resource not found") from e

            logger.error(
                "Unexpected error retrieving secret %s: %s", self.secret_name, e
            )
            raise

@dataclass
class Tenant:
    """
    A class to represent a tenant with its id and endpoints.
    """

    id: str
    endpoints: Dict[str, Endpoint] = field(default_factory=dict)

@dataclass
class Config:
    """
    A class to represent the overall configuration containing tenants.
    """

    tenants: Dict[str, Tenant] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Config":
        """
        Create a Config object from a dictionary.

        Args:
            data (dict): The configuration data.

        Returns:
            Config: The created Config object.
        """
        logger.info("Converting configuration data from dictionary.")
        tenants = {}
        for tenant_id, tenant_data in data.get("tenants", {}).items():
            endpoints = {
                name: Endpoint(
                    auth_url=endpoint_data["auth_url"],
                    base_url=endpoint_data["base_url"],
                )
                for name, endpoint_data in tenant_data.get("endpoints", {}).items()
            }
            tenants[tenant_id] = Tenant(id=tenant_id, endpoints=endpoints)
        logger.info("Configuration data converted successfully.")
        return Config(tenants=tenants)


def validate_config(config: Config) -> None:
    """
    Validates the loaded configuration to ensure it meets expected formats.

    Args:
        config (Config): Configuration object to validate.

    Raises:
        ValueError: If validation fails.
    """
    logger.info("Validating configuration.")
    if not config.tenants:
        logger.error("No tenants found in configuration.")
        raise ValueError("No tenants found in configuration.")

    for tenant_id, tenant in config.tenants.items():
        if not tenant.endpoints:
            logger.error("No endpoints found for tenant %s", tenant_id)
            raise ValueError(f"No endpoints found for tenant {tenant_id}.")

        for endpoint_name, endpoint in tenant.endpoints.items():
            if not endpoint.auth_url:
                logger.error(
                    "Endpoint %s for tenant %s is missing 'auth_url'.",
                    endpoint_name,
                    tenant_id,
                )
                raise ValueError(
                    f"Endpoint {endpoint_name} for tenant {tenant_id} is missing 'auth_url'."
                )

            if not endpoint.base_url:
                logger.error(
                    "Endpoint %s for tenant %s is missing 'base_url'.",
                    endpoint_name,
                    tenant_id,
                )
                raise ValueError(
                    f"Endpoint {endpoint_name} for tenant {tenant_id} is missing 'base_url'."
                )
    logger.info("Configuration validation successful.")
