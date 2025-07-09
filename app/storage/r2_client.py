import boto3
import os
import re
from dotenv import load_dotenv
import uuid
from fastapi import UploadFile, HTTPException

# Load environment variables from the Backend directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Check if R2 is configured
R2_CONFIGURED = bool(
    os.getenv("R2_ACCESS_KEY") and 
    os.getenv("R2_SECRET_KEY") and 
    os.getenv("R2_BUCKET_NAME") and
    os.getenv("R2_ENDPOINT_URL")
)

if R2_CONFIGURED:
    # Get the S3 endpoint URL - this should be the account-specific endpoint
    s3_endpoint = os.getenv("R2_ENDPOINT_URL")
    
    # Extract account ID from the endpoint if needed
    account_id = os.getenv("R2_ACCOUNT_ID")
    if not account_id and s3_endpoint and "r2.cloudflarestorage.com" in s3_endpoint:
        # Extract account ID from URL like https://account_id.r2.cloudflarestorage.com
        match = re.search(r'https://([a-f0-9]{32})\.r2\.cloudflarestorage\.com', s3_endpoint)
        if match:
            account_id = match.group(1)
            print(f"Extracted Account ID from endpoint: {account_id}")
    
    if not s3_endpoint:
        if account_id:
            s3_endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
        else:
            print("ERROR: No R2_ENDPOINT_URL provided and cannot determine account ID")
            s3_endpoint = "https://r2.cloudflarestorage.com"
    
    try:
        r2 = boto3.client(
            "s3",
            region_name=os.getenv("R2_REGION", "auto"),
            endpoint_url=s3_endpoint,
            aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
        )
        BUCKET = os.getenv("R2_BUCKET_NAME")
        
        # For public access, we'll use the bucket's public domain if available
        # Otherwise construct it from the account ID
        public_domain = os.getenv("R2_PUBLIC_DOMAIN")
        if public_domain:
            # Don't add https:// if it's already included
            if public_domain.startswith("http"):
                PUBLIC_ENDPOINT = public_domain
            else:
                PUBLIC_ENDPOINT = f"https://{public_domain}"
        elif account_id:
            # Use the standard public R2 URL format
            # The correct format should be: https://pub-{first-16-chars-of-account-id}.r2.dev
            PUBLIC_ENDPOINT = f"https://pub-{account_id[:16]}.r2.dev"
        else:
            PUBLIC_ENDPOINT = None
        
        S3_ENDPOINT = s3_endpoint
        
        print(f"R2 Configuration initialized:")
        print(f"  S3 Endpoint: {s3_endpoint}")
        print(f"  Public Endpoint: {PUBLIC_ENDPOINT}")
        print(f"  Bucket: {BUCKET}")
        print(f"  Account ID: {account_id}")
        
    except Exception as e:
        print(f"Error initializing R2 client: {e}")
        r2 = None
        BUCKET = None
        PUBLIC_ENDPOINT = None
        S3_ENDPOINT = None
        R2_CONFIGURED = False
else:
    r2 = None
    BUCKET = None
    PUBLIC_ENDPOINT = None
    S3_ENDPOINT = None
    print("R2 not configured - missing required environment variables")

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
            ExtraArgs={"ACL": "public-read"}  # Make file public
        )
        
        # Construct the public URL for the uploaded file
        #if PUBLIC_ENDPOINT:
            #return f"{PUBLIC_ENDPOINT}/{file_id}"
        #else:
            # Fallback: try to construct URL from environment variables
            #public_domain = os.getenv("R2_PUBLIC_DOMAIN")
            #if public_domain:
                #if public_domain.startswith("http"):
                    #return f"{public_domain}/{file_id}"
                #else:
                    #return f"https://{public_domain}/{file_id}"
            #else:
        return f"https://pub-ec581fd3be54492190988525aca67c77.r2.dev/{file_id}"
                # Last resort: construct from account ID from environment
                #account_id = os.getenv("R2_ACCOUNT_ID")
                #if account_id:
                #return f"https://pub-{account_id[:16]}.r2.dev/{file_id}"
                #else:
                    # This might not work but provides a URL
                    #return f"https://{BUCKET}.r2.cloudflarestorage.com/{file_id}"
            
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
