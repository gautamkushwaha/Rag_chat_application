import boto3
import os
import tempfile
from botocore.exceptions import ClientError
import uuid

AWS_REGION = os.getenv("AWS_REGION")
BUCKET ="gautam-rag-pdf-storage"

s3 = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION", "ap-south-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

def upload_file_to_s3(local_path: str, s3_key: str):
    try:
        s3.upload_file(local_path, BUCKET, s3_key)
        return f"s3://{BUCKET}/{s3_key}"
    except ClientError as e:
        raise RuntimeError(f"S3 upload failed: {e}")

def download_file_from_s3(s3_key: str, local_path: str):
    try:
        s3.download_file(BUCKET, s3_key, local_path)
    except ClientError as e:
        raise RuntimeError(f"S3 download failed: {e}")

def generate_presigned_url(filename: str, content_type: str):
    """Generate presigned URL for direct frontend upload"""
    s3_key = f"uploads/{uuid.uuid4()}_{filename}"
    
    try:
        presigned_url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': BUCKET,
                'Key': s3_key,
                'ContentType': content_type,
            },
            ExpiresIn=300  # 5 minutes
        )
        
        return {
            "upload_url": presigned_url,
            "s3_key": s3_key,
            "s3_uri": f"s3://{BUCKET}/{s3_key}"
        }
    except ClientError as e:
        raise RuntimeError(f"Failed to generate presigned URL: {e}")

def ingest_from_s3(s3_key: str):
    """Download from S3 and process"""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name
            
        # Download from S3
        download_file_from_s3(s3_key, tmp_path)
        
        # Process the file
        from .ingestion import ingest_pdf
        chunks_added, chunk_types = ingest_pdf(tmp_path)
        
        # Cleanup
        os.unlink(tmp_path)
        
        return chunks_added, chunk_types
        
    except Exception as e:
        raise RuntimeError(f"Failed to ingest from S3: {str(e)}") 