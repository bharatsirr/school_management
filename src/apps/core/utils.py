import boto3
import os
import shutil
from django.conf import settings
from django.core.files.storage import default_storage


def delete_files_from_s3(relative_path):
    # Construct the full path using the relative path provided
    user_documents_prefix = os.path.join(settings.AWS_LOCATION, relative_path)

    # Use Django's default storage to list files with a specific prefix (directory)
    bucket = default_storage.bucket

    # List all files that start with the given prefix (i.e., the relative path)
    blobs = bucket.list_blobs(prefix=user_documents_prefix)

    # Loop through the files and delete them
    for blob in blobs:
        try:
            blob.delete()  # Delete the file from S3
            print(f"Deleted file: {blob.name}")
        except Exception as e:
            print(f"Error deleting file {blob.name}: {e}")

def delete_files_from_local(relative_path):
    # Join the relative path with the MEDIA_ROOT to get the absolute path
    user_documents_dir = os.path.join(settings.MEDIA_ROOT, relative_path)

    # Check if the directory exists
    if os.path.exists(user_documents_dir) and os.path.isdir(user_documents_dir):
        # Delete all files in the directory
        for filename in os.listdir(user_documents_dir):
            file_path = os.path.join(user_documents_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Delete individual file
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Delete sub-directory, if any
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
        
        # After deleting files, remove the directory itself
        os.rmdir(user_documents_dir)
        print(f"Deleted all files and the directory for path: {relative_path}")
    else:
        print(f"Directory does not exist: {relative_path}")