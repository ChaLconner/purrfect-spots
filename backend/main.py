import os, uuid, mimetypes
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
from boto3.s3.transfer import TransferConfig
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

AWS_REGION        = os.getenv("AWS_REGION", "ap-southeast-1")
AWS_BUCKET        = os.getenv("AWS_S3_BUCKET", "purrfect-spots-bucket")
AWS_ACCESS_KEY    = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY    = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    config=boto3.session.Config(signature_version="s3v4")
)

class PresignReq(BaseModel):
    filename: str        # "mew.jpg"
    content_type: str    # "image/jpeg"

@app.post("/api/presigned-url")
def create_presigned_url(req: PresignReq):
    # สร้าง key แบบสุ่ม ป้องกันชื่อซ้ำ  /cats/{uuid4}.{ext}
    ext   = mimetypes.guess_extension(req.content_type) or ".jpg"
    key   = f"cats/{uuid.uuid4()}{ext}"

    try:
        url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": AWS_BUCKET,
                "Key": key,
                "ContentType": req.content_type,
                "ACL": "public-read"
            },
            ExpiresIn=60 * 5  # มีอายุ 5 นาที
        )
        public_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
        return {"upload_url": url, "public_url": public_url, "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Purrfect Spots API is running!"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    import datetime as dt
    return {"status": "healthy", "timestamp": dt.datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
