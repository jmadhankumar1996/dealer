# lambda_function.py
from libs.config import Config
from libs.sftp_client import SFTPClient
from libs.s3_client import S3Client
from libs.secrets_manager import SecretsManager
from libs.file_processor import FileProcessor
from libs.logger import logger
import os
from contextlib import contextmanager
import tempfile

@contextmanager
def temporary_file():
    """Context manager for handling temporary files"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, dir='/tmp')
    try:
        yield temp_file.name
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

def process_region(region, host, secret_name):
    """Process files for a specific region (US or CA)"""
    logger.info(f"Starting processing for region: {region}")
    
    try:
        # Initialize clients
        secrets = SecretsManager()
        s3 = S3Client()
        
        # Get SFTP credentials
        creds = secrets.get_credentials(secret_name)
        logger.info(f"Retrieved credentials for {region}")
        
        # Initialize and setup SFTP client
        sftp = SFTPClient(host, creds['username'], creds['password'], creds['port'])
        sftp.setup_connection()
        logger.info(f"SFTP connection established for {region}")
        
        # Get latest file
        latest_file = sftp.get_latest_file()
        if not latest_file:
            logger.warning(f"No files found in {region} SFTP server", extra={'region': region})
            return {
                'statusCode': 200,
                'body': f'No files found in {region} SFTP server'
            }
        
        # Extract just the filename from the full path
        filename = os.path.basename(latest_file)  # Get only the filename
        logger.info(f"Found latest file: {filename}", extra={'region': region})
        
        # Check if file already exists in S3
        if s3.file_exists(filename, region.lower()):  # Use the filename here
            logger.info(f"File {filename} already exists in S3", 
                       extra={'region': region, 'file': filename})
            return {
                'statusCode': 200,
                'body': f'File already processed for {region}'
            }

                
        # Use context manager for temporary file handling
        with temporary_file() as local_path:
            logger.info(f"Downloading file to: {local_path}", 
                       extra={'region': region, 'file': latest_file})
            
            # Download and process file
            sftp.download_file(latest_file, local_path)
            
            if FileProcessor.process_csv(local_path):
                # Upload to S3
                s3_key = s3.upload_file(local_path, filename, region.lower())  # Use the filename here
                logger.info(f"File successfully processed and uploaded to S3: {s3_key}", 
                           extra={'region': region, 'file': filename, 's3_key': s3_key})
                return {
                    'statusCode': 200,
                    'body': f'Successfully processed {region} file: {filename}'
                }
            else:
                logger.error(f"Failed to process file: {filename}", 
                           extra={'region': region, 'file': filename})
                return {
                    'statusCode': 500,
                    'body': f'Failed to process {region} file: {filename}'
                }

    except Exception as e:
        logger.error(f"Error processing {region} region: {str(e)}", 
                    extra={'region': region, 'error': str(e)}, exc_info=True)
        return {
            'statusCode': 500,
            'body': f'Error processing {region} region: {str(e)}'
        }



def lambda_handler(event, context):
    """Main Lambda handler"""
    logger.info("Lambda handler started", extra={'event': event})
    
    try:
        # Process US files
        logger.info("Processing US region")
        us_result = process_region(
            'US',
            Config.US_SFTP_HOST,
            Config.US_SECRET_NAME
        )
        
        # Process Canada files
        logger.info("Processing CA region")
        ca_result = process_region(
            'CA',
            Config.CA_SFTP_HOST,
            Config.CA_SECRET_NAME
        )
        
        # Combine results
        response = {
            'statusCode': 200,
            'body': {
                'us_result': us_result,
                'ca_result': ca_result
            }
        }
        
        logger.info("Lambda execution completed successfully", 
                   extra={'us_result': us_result, 'ca_result': ca_result})
        return response
        
    except Exception as e:
        error_msg = f"Lambda execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'statusCode': 500,
            'body': error_msg
        }