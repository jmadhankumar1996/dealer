import boto3
import json
from logger import logger

class SecretsManager:
    def __init__(self):
        self.client = boto3.client('secretsmanager')
        
    def get_credentials(self, secret_name):
        """Retrieve SFTP credentials from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret = json.loads(response['SecretString'])
            return {
                'username': secret['sftp_username'],
                'password': secret['sftp_password'],
                'port': int(secret.get('sftp_port', 22))
            }
        except Exception as e:
            logger.error(f"Error fetching secret: {str(e)}")
            raise