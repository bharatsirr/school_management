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
        logger.info(f"Initialized S3 storage with bucket: {self.bucket_name}, location: {self.location}, region: {self.region_name}")

    def _get_or_create_connection(self):
        if self._connection is None:
            try:
                self._connection = boto3.client(
                    's3',
                    region_name=self.region_name,
                )
                logger.info("Successfully created S3 connection")
            except Exception as e:
                logger.error(f"Error creating S3 connection: {str(e)}")
                raise
        return self._connection

    def _save(self, name, content):
        try:
            logger.info(f"Starting file upload to S3. Original name: {name}")
            name = self._normalize_name(name)
            logger.info(f"Normalized name: {name}")
            
            # Get the S3 client
            s3_client = self._get_or_create_connection()
            
            # Upload the file
            extra_args = {
                'ContentType': getattr(content, 'content_type', None),
                'ACL': 'private'
            }
            
            logger.info(f"Uploading to bucket: {self.bucket_name}, key: {name}")
            s3_client.upload_fileobj(
                content,
                self.bucket_name,
                name,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Successfully uploaded file to S3: {name}")
            return name
        except Exception as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise

    def exists(self, name):
        try:
            name = self._normalize_name(name)
            logger.info(f"Checking if file exists in S3: {name}")
            s3_client = self._get_or_create_connection()
            s3_client.head_object(Bucket=self.bucket_name, Key=name)
            logger.info(f"File exists in S3: {name}")
            return True
        except Exception as e:
            logger.error(f"Error checking file existence in S3: {str(e)}")
            return False

    def url(self, name, parameters=None, expire=900):
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