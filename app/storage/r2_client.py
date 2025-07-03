import boto3
import os
from dotenv import load_dotenv
import uuid
from fastapi import UploadFile, HTTPException

load_dotenv()

# Check if R2 is configured
R2_CONFIGURED = bool(
    os.getenv("R2_ENDPOINT_URL") and 
    os.getenv("R2_ACCESS_KEY") and 
    os.getenv("R2_SECRET_KEY") and 
    os.getenv("R2_BUCKET_NAME")
)

if R2_CONFIGURED:
    r2 = boto3.client(
        "s3",
        region_name=os.getenv("R2_REGION", "auto"),
        endpoint_url=os.getenv("R2_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
    )
    BUCKET = os.getenv("R2_BUCKET_NAME")
else:
    r2 = None
    BUCKET = None

async def upload_to_r2(file: UploadFile) -> str:
    if not R2_CONFIGURED:
        raise HTTPException(status_code=500, detail="R2 storage is not configured. Please check R2_ENDPOINT_URL, R2_ACCESS_KEY, R2_SECRET_KEY, and R2_BUCKET_NAME environment variables.")
    
    if not r2 or not BUCKET:
        raise HTTPException(status_code=500, detail="R2 client is not properly initialized")
    
    # Validate file
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided or filename is empty")
    
    try:
        # Reset file pointer to beginning
        await file.seek(0)
        
        file_id = f"{uuid.uuid4()}_{file.filename}"
        
        # Upload file to R2
        r2.upload_fileobj(
            file.file,
            BUCKET,
            file_id,
            ExtraArgs={"ACL": "public-read"}  # Optional: make file public
        )
        
        # Construct the public URL - adjust this based on your R2 domain setup
        endpoint_url = os.getenv('R2_ENDPOINT_URL')
        if endpoint_url:
            # Remove protocol and add file path
            domain = endpoint_url.replace('https://', '').replace('http://', '')
            return f"https://{domain}/{file_id}"
        else:
            return f"https://{BUCKET}.r2.cloudflarestorage.com/{file_id}"
            
    except Exception as e:
        error_msg = str(e)
        
        # Provide more specific error messages for common R2 issues
        if "NoSuchBucket" in error_msg:
            raise HTTPException(status_code=500, detail=f"R2 bucket '{BUCKET}' does not exist")
        elif "AccessDenied" in error_msg:
            raise HTTPException(status_code=500, detail="R2 access denied. Please check your credentials and permissions")
        elif "SignatureDoesNotMatch" in error_msg:
            raise HTTPException(status_code=500, detail="R2 authentication failed. Please check your access key and secret key")
        elif "EndpointConnectionError" in error_msg:
            raise HTTPException(status_code=500, detail="Cannot connect to R2 endpoint. Please check your endpoint URL")
        else:
            raise HTTPException(status_code=500, detail=f"File upload failed: {error_msg}")
