
import boto3
import os

s3 = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION", "ap-south-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

response = s3.list_buckets()

print([bucket["Name"] for bucket in response["Buckets"]])
