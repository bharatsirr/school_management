from storages.backends.s3boto3 import S3Boto3Storage
import boto3
from django.conf import settings

class S3SignedUrlStorage(S3Boto3Storage):
    def url(self, name, parameters=None, expire=900):
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        return s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': name
            },
            ExpiresIn=expire
        )