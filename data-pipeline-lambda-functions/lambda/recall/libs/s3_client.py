import boto3
from datetime import datetime
from config import Config
from logger import logger
import re
import os

class S3Client:
    def __init__(self):
        self.client = boto3.client('s3')
        
    def get_s3_key(self, filename, region):
        """Generate S3 key with date-based prefix"""
        # Extract date from the filename using regex
        match = re.search(r'_(\d{8})_', filename)
        if not match:
            logger.error(f"Date not found in filename: {filename}")
            raise ValueError("Date not found in filename")
        date_str = match.group(1)  # This is the YYYYMMDD string
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]

        # Extract only the file name, ignoring the directory structure
        base_filename = os.path.basename(filename)
        
        return f"{Config.S3_BASE_PREFIX}/{region}/{year}/{month}/{day}/{base_filename}"
        
    def file_exists(self, filename, region):
        """Check if file exists in S3"""
        try:
            s3_key = self.get_s3_key(filename, region)
            self.client.head_object(Bucket=Config.S3_BUCKET, Key=s3_key)
            logger.info(f"File exists in S3: {s3_key}")
            return True
        except self.client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.info(f"File does not exist in S3: {s3_key}")
                return False
            raise  # Re-raise if it's a different error
            
    def upload_file(self, local_path, filename, region):
        """Upload file to S3 with date-based prefix"""
        try:
            s3_key = self.get_s3_key(filename, region)

            # Check if the file already exists in S3
            if self.file_exists(filename, region):
                logger.info(f"File already exists in S3: {s3_key}. Skipping upload.")
                return s3_key

            # Proceed with upload if it doesn't exist
            self.client.upload_file(local_path, Config.S3_BUCKET, s3_key)
            logger.info(f"Uploaded file to S3: {s3_key}")
            return s3_key
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise