from storages.backends.s3boto3 import S3Boto3Storage
import boto3
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class S3SignedUrlStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = settings.AWS_LOCATION
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.region_name = settings.AWS_S3_REGION_NAME
        self._connection = None
        logger.info(f"Initialized S3 storage with bucket: {self.bucket_name}, location: {self.location}")

    def _get_or_create_connection(self):
        if self._connection is None:
            self._connection = boto3.client(
                's3',
                region_name=self.region_name,
            )
        return self._connection

    def url(self, name, parameters=None, expire=900):
        """
        Generate a presigned URL for the file.
        """
        try:
            name = self._normalize_name(name)
            logger.info(f"Generating presigned URL for: {name}")
            
            s3_client = self._get_or_create_connection()
            presigned_url = s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': name
                },
                ExpiresIn=expire
            )
            
            logger.info(f"Generated presigned URL: {presigned_url}")
            return presigned_url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise

    def _save(self, name, content):
        logger.info(f"Attempting to save file: {name} to S3")
        try:
            name = self._normalize_name(name)
            logger.info(f"Normalized name: {name}")
            response = super()._save(name, content)
            logger.info(f"File saved successfully to S3: {response}")
            return response
        except Exception as e:
            logger.error(f"Error saving file to S3: {str(e)}")
            raise

    def exists(self, name):
        try:
            name = self._normalize_name(name)
            logger.info(f"Checking if file exists: {name}")
            exists = super().exists(name)
            logger.info(f"File exists check result: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking file existence: {str(e)}")
            return False