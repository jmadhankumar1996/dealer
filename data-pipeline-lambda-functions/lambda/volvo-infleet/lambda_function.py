"""
This module provides functionality for managing secrets and configurations
for the Volvo InFleet service integration.
"""

import os
import sys

import boto3
import json
from botocore.exceptions import ClientError

from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
import asyncio

from libs.api_client import LoanerClient, OrderClient
from libs.volvo_infleet_service import VolvoInfleetService
from libs.structured_logging import StructuredLoggerBuilder

CURRENT_TIME = datetime.now(timezone.utc)
logger = StructuredLoggerBuilder("OEM_Infleeter").build()

def parse_sync_date(sync_date: str) -> datetime:
    """
    Parses a sync date string into a UTC datetime object at the start of the day.

    :param sync_date: Date string in the format "YYYY-MM-DD".
    :return: A datetime object representing the start of the given date in UTC.
    """
    logger.info("Parsing sync date: %s", sync_date)
    try:
        sync_date_parsed = datetime.strptime(sync_date, "%Y-%m-%d").date()
        parsed_date = datetime.combine(sync_date_parsed, datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        logger.info("Parsed sync date as UTC datetime: %s", parsed_date)
        return parsed_date
    except ValueError as e:
        logger.error("Error parsing sync date: %s", e)
        raise


def calculate_last_sync_date() -> str:
    """
    Calculates the date two weeks prior to the current time, formatted as an ISO string.

    :return: A string representing the date two weeks ago from the current time,
             formatted as "YYYY-MM-DDTHH:MM:SS.000Z".
    """
    logger.info("Calculating last sync date from current time: %s", CURRENT_TIME)
    start_time = CURRENT_TIME - timedelta(days=360)
    last_sync_date = start_time.replace(
        hour=0, minute=0, second=0, microsecond=0
    ).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    logger.info("Calculated last sync date: %s", last_sync_date)
    return last_sync_date


def load_environment_variables() -> dict:
    """
    Loads environment variables necessary for the application.

    :return: A dictionary containing the environment ('env'), S3 bucket name ('lz_bucket'),
    and target directory ('target_dir'). Defaults are used if environment variables are not set.
    """
    logger.info("Loading environment variables.")
    env_vars = {
        "env": os.getenv("ENV", "tst"),
        "lz_bucket": os.getenv("LZ_BUCKET", "unknown"),
        "target_dir": os.getenv("TARGET_DIR", "unknown"),
    }
    logger.debug("Loaded environment variables: %s", env_vars)
    return env_vars


def get_secret(secret_name: str) -> dict:
    """
    Retrieves a secret from AWS Secrets Manager.

    :param secret_name: The name of the secret to retrieve.
    :return: A dictionary containing the secret values.
    """
    logger.debug("Fetching secret from Secrets Manager: %s", secret_name)
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])
        return secret
    except ClientError as e:
        logger.error("Failed to retrieve secret: %s", e)
        raise


def payload_to_s3(inv_df):
    """
    Saves the DataFrame to a CSV file in an S3 bucket with a timestamp in the filename.

    :param inv_df: Pandas DataFrame to save
    :return: Dictionary with statusCode and message
    """
    try:
        logger.info("Starting save to S3 process.")
        env_vars = load_environment_variables()
        bucket_name = env_vars["lz_bucket"]
        target_dir = env_vars["target_dir"]

        year = CURRENT_TIME.strftime('%Y')
        month = CURRENT_TIME.strftime('%m')
        day = CURRENT_TIME.strftime('%d')
        time = CURRENT_TIME.strftime('%H%M%S')

        # Construct the S3 path
        s3_key = f"{target_dir}{year}/{month}/{day}/volvo_inventories_{time}.csv"

        # Convert DataFrame to CSV in memory
        csv_buffer = BytesIO()
        inv_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        s3_client = boto3.client("s3")
        s3_client.put_object(
            Bucket=bucket_name, Key=s3_key, Body=csv_buffer.getvalue()
        )

        s3_url = f"s3://{bucket_name}/{s3_key}"
        logger.info("Inventory Items saved to %s", s3_url)
        return {
            "statusCode": 200,
            "body": f"Inventory Items successfully saved to {s3_url}",
        }

    except Exception as e:
        logger.error("Error saving DataFrame to S3: %s", str(e))
        return {
            "statusCode": 500,
            "body": f"Error saving file to S3 bucket: {str(e)}",
        }


def lambda_handler(event, context):
    """
    Lambda function handler for the Volvo InFleet service integration.

    :param event: AWS Lambda event object
    :param context: AWS Lambda context object
    """
    env_vars = load_environment_variables()
    env = env_vars["env"]

    sync_date = event.get("sync_date", None)
    last_sync = None

    try:
        logger.info(
            "OEM Auto-fleeter Started on env %s at : %s", env.upper(), CURRENT_TIME
        )

        if sync_date:
            last_sync = parse_sync_date(sync_date).isoformat()
        else:
            last_sync = calculate_last_sync_date()

        logger.info("Last sync date: %s", last_sync)
    except ValueError as e:
        logger.error("Error Building LastSyncDate: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error while building LastSyncDate: %s", e)
        sys.exit(1)

    try:
        # Retrieve secret names from environment variables
        loaner_secret_name = os.getenv("VOLVO_INFLEET_LOANER")
        order_secret_name = os.getenv("VOLVO_INFLEET_ORDER")

        if not loaner_secret_name or not order_secret_name:
            logger.error("Missing environment variables for secret names.")
            raise ValueError("Missing required environment variables for secrets.")

        # Initialize the VolvoInfleetService to get the endpoints
        volvo_service = VolvoInfleetService(
            loaner_secret_name=loaner_secret_name,
            order_secret_name=order_secret_name
        )

        # Accessing the endpoints
        loaner_endpoint = volvo_service.get_loaner_endpoint()
        order_endpoint = volvo_service.get_order_endpoint()


        # Pass the secrets to initialize the clients
        loaner_client = LoanerClient()
        lnr_token = loaner_client.parse_token(configs=None)
        loaners_df = loaner_client._get_loaners(lnr_token, last_sync)
        
        if loaners_df is None:
            logger.debug(
                "Exiting Since No-Loaners found Since LastSyncDate, %s", last_sync
            )
            return {
                "statusCode": 200,
                "body": f"Terminated : No-Loaners found Since LastSyncDate {last_sync}",
            }

        order_client = OrderClient()
        odr_token = order_client.parse_token(configs=None)
        inv_df = asyncio.run(order_client._get_inservice_dates(odr_token, loaners_df))

        logger.info("Processing complete, saving results to S3.")
        return payload_to_s3(inv_df)
    except Exception as e:
        logger.error("Error in Lambda handler: %s", e)
        return {
            "statusCode": 500,
            "body": f"Internal server error: {str(e)}",
        }
    