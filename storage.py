import os
import io
import mimetypes
from datetime import datetime

try:
    import boto3
    from botocore.exceptions import ClientError
    boto3_available = True
except ImportError:
    boto3 = None
    boto3_available = False

LOCAL_STORAGE_DIR = os.path.join('/tmp', 'uploads') if (os.environ.get('VERCEL') or not os.access(os.path.dirname(os.path.abspath(__file__)), os.W_OK)) else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
try:
    os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
except Exception:
    pass

def is_s3_storage_enabled():
    return bool(
        boto3_available and
        os.environ.get('AWS_ACCESS_KEY_ID') and
        os.environ.get('AWS_SECRET_ACCESS_KEY') and
        os.environ.get('AWS_ENDPOINT_URL_S3')
    )

def get_s3_client():
    if not is_s3_storage_enabled():
        return None
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL_S3')
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    region_name = os.environ.get('AWS_REGION', 'us-east-2')

    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region_name
    )

def upload_document_file(file_bytes, filename, content_type=None):
    """
    Uploads a file to Neon S3 Cloud Object Storage (or local storage fallback).
    Returns file metadata including storage key and URL.
    """
    if not content_type:
        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or 'application/octet-stream'

    bucket_name = os.environ.get('NEON_BUCKET_NAME', 'excuseai-documents')
    timestamp_prefix = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    storage_key = f"documents/{timestamp_prefix}_{filename}"

    if is_s3_storage_enabled():
        try:
            s3 = get_s3_client()
            s3.put_object(
                Bucket=bucket_name,
                Key=storage_key,
                Body=file_bytes,
                ContentType=content_type
            )
            return {
                'storage_type': 'neon_s3',
                'bucket': bucket_name,
                'key': storage_key,
                'filename': filename,
                'content_type': content_type
            }
        except Exception as e:
            print(f"[Storage] S3 upload error: {e}, falling back to local storage")

    # Local storage fallback
    local_path = os.path.join(LOCAL_STORAGE_DIR, f"{timestamp_prefix}_{filename}")
    with open(local_path, 'wb') as f:
        f.write(file_bytes)

    return {
        'storage_type': 'local',
        'key': f"{timestamp_prefix}_{filename}",
        'path': local_path,
        'filename': filename,
        'content_type': content_type
    }
