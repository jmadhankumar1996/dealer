# sftp_client.py
import pysftp
import subprocess
import os
import re
from datetime import datetime
from typing import Optional, List
from config import Config
from logger import logger

class SFTPClient:
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.cnopts = None
        
    def setup_connection(self):
        """Setup SFTP connection with host key verification"""
        rsa_key = self._get_rsa_key()
        if not rsa_key:
            raise Exception("Failed to retrieve RSA key")
        
        host_key_path = self._save_host_key_to_file(rsa_key)
        self.cnopts = pysftp.CnOpts(knownhosts=host_key_path)
        
    def _get_rsa_key(self):
        """Retrieve RSA key using ssh-keyscan"""
        try:
            result = subprocess.run(['ssh-keyscan', '-t', 'rsa', self.host],
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"ssh-keyscan failed: {result.stderr}")
                return None
                
            for line in result.stdout.splitlines():
                if 'ssh-rsa' in line:
                    return line.split('ssh-rsa ')[1]
            
            return None
        except Exception as e:
            logger.error(f"Error getting RSA key: {str(e)}")
            raise
            
    def _save_host_key_to_file(self, rsa_key):
        """Save host key to known_hosts file"""
        try:
            host_key_path = '/tmp/known_hosts'
            with open(host_key_path, 'w') as f:
                f.write(f"{self.host} ssh-rsa {rsa_key}")
            os.chmod(host_key_path, 0o644)
            return host_key_path
        except Exception as e:
            logger.error(f"Error saving host key: {str(e)}")
            raise
            
    def get_latest_file(self):
        """Get the latest file from SFTP server"""
        try:
            with pysftp.Connection(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                cnopts=self.cnopts
            ) as sftp:
                sftp.cwd(Config.SFTP_PATH)
                logger.info(f"Changed to SFTP directory: {Config.SFTP_PATH}")
                files = sftp.listdir_attr()
                
                if not files:
                    logger.info("No files found in SFTP directory")
                    return None
                    
                # Sort files by modification time
                files.sort(key=lambda x: x.st_mtime, reverse=True)
                latest_file = files[0].filename
                
                # Return the full path of the latest file
                full_path = f"{Config.SFTP_PATH}/{latest_file}"
                logger.info(f"Latest file found: {latest_file}")
                return full_path
                
        except Exception as e:
            logger.error(f"Error getting latest file: {str(e)}")
            raise
            
    def download_file(self, remote_path, local_path):
        """Download file from SFTP server"""
        try:
            logger.info(f"Attempting to download from {remote_path} to {local_path}")
            with pysftp.Connection(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                cnopts=self.cnopts
            ) as sftp:
                sftp.get(remote_path, local_path)
                logger.info(f"Downloaded file: {remote_path}")
        except IOError as e:
            logger.error(f"File not found: {remote_path}")
            return  # Handle error appropriately
        except Exception as e:
            logger.error(f"Error downloading file from {remote_path} to {local_path}: {str(e)}")
            raise