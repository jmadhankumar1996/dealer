# config.py
import os
from datetime import datetime

class Config:
    ENV = os.getenv("ENV", "tst")
    S3_BUCKET = f"madhan-data-{ENV}-landing-zone"
    S3_BASE_PREFIX = "data/recall/output"
    
    # SFTP Configuration
    SFTP_PORT = 22
    SFTP_PATH = "/outgoing"
    # SFTP_OUTGOING_PATH = "/outgoing"
    # SFTP_INCOMING_PATH = "/incoming"
    
    # US SFTP Config
    US_SFTP_HOST = "ftp.recallmasters.com"
    US_SFTP_USERNAME = "dealerware_invmon"
    US_SECRET_NAME = "sftp-us-server-details"
    US_FILE_PREFIX = "DEALERWARE-INV"
    
    # Canada SFTP Config
    CA_SFTP_HOST = "ftp.recallmasters.com"
    CA_SFTP_USERNAME = "dealerware_ca_invmon"
    CA_SECRET_NAME = "sftp-ca-server-details"
    CA_FILE_PREFIX = "DEALERWARE-C-INV"
    
    @staticmethod
    def get_file_pattern(region: str) -> str:
        """Get the expected file pattern for a given region"""
        prefix = Config.US_FILE_PREFIX if region.upper() == 'US' else Config.CA_FILE_PREFIX
        return f"{prefix}_\\d{{8}}_\\d{{6}}_output\\.csv"