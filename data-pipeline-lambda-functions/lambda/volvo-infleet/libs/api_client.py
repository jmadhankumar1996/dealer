"""
This module provides API client classes for interacting with the Volvo InFleet service.
"""

import asyncio
import logging
import os

import pandas as pd
import requests
import aiohttp

from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, RequestException
from libs.secrets_manager import SecretsManager
from typing import Dict
from urllib3.util import Retry

TIMEOUT = 60

logger = logging.getLogger("OEM_Infleeter")


class APIClient:
    """Base API client for making HTTP requests."""

    def __init__(self):
        logger.info("Initializing API client.")
        self.session = self._api_session()

    def _api_session(self) -> requests.Session:
        """Creates a requests session with retry logic."""
        logger.info("Setting up HTTP session with retry logic.")
        session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=5,
            pool_maxsize=10,
            max_retries=Retry(
                total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
            ),
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        logger.info("HTTP session created successfully.")
        return session

    def _generate_token(self, auth_url: str, secrets: Dict[str, str]) -> str:
        """Generates an authorization token."""
        logger.info("Generating authorization token from secrets.")
        secrets["grant_type"] = "client_credentials"

        try:
            logger.debug("Requesting token from auth URL: %s", auth_url)
            response = self.session.get(url=auth_url, data=secrets, timeout=TIMEOUT)
            response.raise_for_status()
            token = response.json()["access_token"]
            logger.info("Token generated successfully.")
            return token
        except requests.exceptions.RequestException as e:
            logger.error("Failed to generate token: %s", e)
            raise


class BaseClient(APIClient):
    """Base client for specific Volvo InFleet services."""

    def __init__(self, secret_prefix: str):
        super().__init__()
        logger.info("Initializing BaseClient for service: %s", secret_prefix)
        self.configs = None
        self.secrets = self._get_secret(secret_prefix)

    def _get_secret(self, secret_prefix: str) -> Dict[str, str]:
        """Retrieves secrets from the secrets manager."""
        secret_env_var = f"VOLVO_INFLEET_{secret_prefix.upper()}"
        logger.info("Fetching secrets using environment variable: %s", secret_env_var)
        secret_name = os.getenv(secret_env_var)
        if not secret_name:
            logger.error(
                "Secret name for %s not found in environment variables.", secret_env_var
            )
            raise ValueError(f"Secret name for {secret_env_var} not set.")
        logger.debug("Secret name obtained: %s", secret_name)
        # Get secrets from AWS Secrets Manager
        secrets_manager = SecretsManager(secret_name)
        secrets = secrets_manager.get_secret()
        # Extract base_url and auth_url from secrets manager
        secrets["auth_url"] = secrets.get("auth_url")
        secrets["base_url"] = secrets.get("base_url")
        logger.info("Secrets retrieved successfully for %s.", secret_prefix)
        return secrets

    def parse_token(self, configs):
        """Parses the token from the given configuration."""
        logger.info("Parsing token for service.")
        self.configs = configs
        url = self.secrets["auth_url"]  # Use auth_url from secrets manager
        secrets = self.secrets.copy()
        secrets.pop("subscription_key", None)
        secrets.pop("vendor_code", None)
        logger.debug("Requesting token from URL: %s with secrets", url)
        return self._generate_token(auth_url=url, secrets=secrets)


class LoanerClient(BaseClient):
    """Client for interacting with the Loaner service."""

    def __init__(self):
        logger.info("Initializing LoanerClient.")
        super().__init__("Loaner")

    def _get_loaners(self, token: str, last_sync_date: str = None) -> pd.DataFrame:
        """
        Fetches loaner vehicles from the Loaner API, handles possible errors,
        and returns a DataFrame with unique VINs and the most recent lastModifiedDate.

        Args:
            token (str): The authorization token for the API request.
            last_sync_date (str): The last synchronization date to filter the results.

        Returns:
            pd.DataFrame: DataFrame containing unique loaner vehicles with the most recent lastModifiedDate.
        """
        base_url = self.secrets["base_url"]  # Use base_url from secrets manager
        params = {"vendorCode": self.secrets.get("vendor_code", None)}
        if last_sync_date:
            logger.info("Filtering loaners since last sync date: %s", last_sync_date)
            params["lastSyncDate"] = last_sync_date

        headers = {
            "Authorization": f"Bearer {token}",
            "Ocp-Apim-Subscription-Key": self.secrets["subscription_key"],
        }

        try:
            logger.debug("Sending request to Loaner API with base URL: %s", base_url)
            response = self.session.get(
                url=base_url, headers=headers, params=params, timeout=TIMEOUT
            )
            response.raise_for_status()
            logger.info("Loaner vehicles fetched successfully.")
        except HTTPError as http_err:
            logger.error(
                "HTTP error occurred while fetching loaner vehicles: %s", http_err
            )
            raise
        except RequestException as req_err:
            logger.error(
                "Request error occurred while fetching loaner vehicles: %s", req_err
            )
            raise
        except Exception as err:
            logger.error(
                "An unexpected error occurred while fetching loaner vehicles: %s", err
            )
            raise

        # Process the response JSON to DataFrame
        response_json = response.json()
        if not response_json:
            logger.info("The response from the Loaner API is empty.")
            return None

        loaners_df = pd.DataFrame(response_json)

        # Convert lastModifiedDate to datetime
        loaners_df["lastModifiedDate"] = pd.to_datetime(loaners_df["lastModifiedDate"])

        # Identify duplicates by VIN and keep the one with the most recent lastModifiedDate
        unique_loaners = loaners_df.sort_values("lastModifiedDate").drop_duplicates(
            subset="vin", keep="last"
        )

        logger.info("Identified %d unique loaner vehicles.", len(unique_loaners))
        
        return unique_loaners
    
class OrderClient(BaseClient):
    """Client for interacting with the Order service."""

    def __init__(self):
        logger.info("Initializing OrderClient.")
        super().__init__("Order")

    async def _get_inservice_dates(self, token: str, loaners_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fetches in-service dates for loaner vehicles from the Order API and updates the DataFrame.
        Drops records with no customerHandoverDate and logs the process.

        Args:
            token (str): The authorization token for the API request.
            loaners_df (pd.DataFrame): DataFrame containing loaner vehicle information.

        Returns:
            pd.DataFrame: Updated DataFrame with in-service dates and cleaned up columns.
        """
        # Use base_url from secrets manager
        base_url = self.secrets["base_url"]

        headers = {
            "Authorization": f"Bearer {token}",
            "Ocp-Apim-Subscription-Key": self.secrets["subscription_key"],
            "Api-Version": "2.0",
        }

        dropped_records = []
        total_records = len(loaners_df)

        async def fetch_in_service_date(session, index, row):
            url = f"{base_url}/{row['vin']}"
            try:
                async with session.get(url, headers=headers, timeout=timeout) as resp:
                    resp.raise_for_status()
                    response_json = await resp.json()
                    in_service_date = response_json["responseDetails"]["order"]["vehicleOrderDetails"]["customer"].get("customerHandoverDate", None)
                    
                    if in_service_date:
                        loaners_df.at[index, "in_service_date"] = in_service_date
                        logger.info(f"Successfully fetched in-service date for VIN: {row['vin'][:-4]}****")
                    else:
                        dropped_records.append(row['vin'])
                        logger.info(f"No customerHandoverDate for VIN: {row['vin'][:-4]}****. Record will be dropped.")
                        loaners_df.at[index, "in_service_date"] = None

            except aiohttp.ClientResponseError as http_err:
                logger.error(f"HTTP error occurred for VIN {row['vin']}: {http_err}")
                loaners_df.at[index, "in_service_date"] = None
            except Exception as err:
                logger.error(f"An error occurred for VIN {row['vin']}: {err}")
                loaners_df.at[index, "in_service_date"] = None

        # Prepare the connector and session
        connector = aiohttp.TCPConnector(limit=100, ssl=False)
        timeout = aiohttp.ClientTimeout(total=120)
        batch_size = 500  # creating a batch size
        start = 0
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            while start < len(loaners_df):
                tasks = [fetch_in_service_date(session, index, row) for index, row in loaners_df[start: start+batch_size].iterrows()]
                await asyncio.gather(*tasks)
                start += batch_size

        # Drop records with missing in_service_date (i.e., those with no customerHandoverDate)
        loaners_df = loaners_df.dropna(subset=["in_service_date"])

        # Log the summary
        logger.info(f"Total VINs fetched: {total_records}")
        logger.info(f"VINs with missing customerHandoverDate (dropped): {len(dropped_records)}")
        logger.info(f"List of dropped VINs: {', '.join(dropped_records)}")

        # Clean up the DataFrame columns
        loaners_df["oem_dealer_code"] = loaners_df["globalRetailerCode"].str.replace("6US", "")
        loaners_df["out_service_date"] = None
        loaners_df.drop(columns=["statusDate"], inplace=True)
        loaners_df.rename(
            columns={
                "retailerName": "retailer_name",
                "retailerCode": "retailer_code",
                "lastModifiedDate": "last_modified_date",
                "globalRetailerCode": "global_retailer_code",
            },
            inplace=True,
        )
        return loaners_df
