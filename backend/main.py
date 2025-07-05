import os, uuid, mimetypes
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
from boto3.s3.transfer import TransferConfig
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

app = FastAPI()

AWS_REGION        = os.getenv("AWS_REGION", "ap-southeast-1")
AWS_BUCKET        = os.getenv("AWS_S3_BUCKET", "purrfect-spots-bucket")
AWS_ACCESS_KEY    = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY    = os.getenv("AWS_SECRET_ACCESS_KEY")

SUPA_URL   = os.getenv("SUPABASE_URL")
SUPA_KEY   = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # ใช้ service role จะ INSERT ได้

# Initialize Supabase client only if credentials are provided
supabase: Client = None
if SUPA_URL and SUPA_KEY:
    supabase = create_client(SUPA_URL, SUPA_KEY)

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

class AddCatReq(BaseModel):
    name: str
    description: str | None = None
    latitude: float
    longitude: float
    image_url: str   # ได้มาจากข้อ 1

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

@app.post("/api/add-location")
def add_location(cat: AddCatReq):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    result = supabase.table("cat_locations").insert(cat.dict()).execute()
    if result.error:
        raise HTTPException(status_code=500, detail=result.error.message)
    return {"status": "ok", "id": result.data[0]["id"]}

@app.get("/api/locations")
def get_locations():
    """Get all cat locations from Supabase"""
    if not supabase:
        # Return sample data if Supabase not configured
        return {
            "status": "ok", 
            "data": [
                {
                    "id": 1,
                    "name": "แมวตัวอย่าง",
                    "description": "แมวน่ารักที่สวนลุมพินี",
                    "latitude": 13.7367,
                    "longitude": 100.5408,
                    "image_url": "https://example.com/cat.jpg"
                }
            ]
        }
    
    try:
        result = supabase.table("cat_locations").select("*").execute()
        if result.error:
            raise HTTPException(status_code=500, detail=result.error.message)
        return {"status": "ok", "data": result.data}
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
