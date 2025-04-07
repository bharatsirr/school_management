import boto3
from django.core.files.storage import Storage
from school_management_backend import settings


class S3SignedUrlStorage(Storage):
    def __init__(self):
        self.s3 = boto3.client('s3')

    def _save(self, name, content):
        self.s3.upload_fileobj(content, settings.AWS_STORAGE_BUCKET_NAME, name)
        return name

    def delete(self, name):
        self.s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=name)

    def exists(self, name):
        try:
            self.s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=name)
            return True
        except:
            return False