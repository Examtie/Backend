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
    
    try:
        file_id = f"{uuid.uuid4()}_{file.filename}"
        r2.upload_fileobj(
            file.file,
            BUCKET,
            file_id,
            ExtraArgs={"ACL": "public-read"}  # Optional: make file public
        )
        return f"{os.getenv('R2_ENDPOINT_URL')}/{file_id}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
