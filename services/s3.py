from botocore.exceptions import NoCredentialsError, ClientError
import hashlib
import os
import io
import boto3


s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

def upload_file_to_s3(file_bytes : bytes , filename :str , content_type : str ):
    if not BUCKET_NAME or not os.getenv('AWS_ACCESS_KEY_ID'):
        print("WARNING: AWS Credentials not found. Returning mock URL.")
        return f"https://mock-s3-url.com/{filename}"
    
    file_hash = hashlib.md5(file_bytes).hexdigest()
    unique_filename = f"{file_hash}_{filename}"

    region = os.getenv("AWS_REGION", "us-east-1")
    url = f'https://{BUCKET_NAME}.s3.{region}.amazonaws.com/{unique_filename}'\
    
    try:
        s3_client.head_object(Bucket = BUCKET_NAME , Key =  unique_filename)
        print(f'File already exists in S3 , skipping upload : {unique_filename}')
        return url 
    except ClientError as e:
        error_code = e.response.get('Error',{}).get('Code')
        if error_code != '404':
            raise Exception(f'S3 check failed : {str(e)}')
        
    try:
        file_obj = io.BytesIO(file_bytes)
        s3_client.upload_fileobj(
            file_obj,
            BUCKET_NAME,
            unique_filename,
            ExtraArgs = {'ContentType': content_type}
        )
        return url 
    except NoCredentialsError:
        raise Exception("AWS Credentials not found.")
    except Exception as e:
        raise Exception(f"S3 Upload Failed: {str(e)}")