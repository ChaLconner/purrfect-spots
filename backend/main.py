import os, uuid, mimetypes
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import boto3
from boto3.s3.transfer import TransferConfig
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class CatLocation(BaseModel):
    id: str  # เปลี่ยนจาก int เป็น str
    image_url: str
    latitude: float
    longitude: float
    description: str | None = None
    location_name: str | None = None
    uploaded_at: str | None = None
    # image_url: str   # ได้มาจากข้อ 1

@app.post("/api/add-location")
async def add_location(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    latitude: float = Form(...),
    longitude: float = Form(...)
):
    print("[DEBUG] AWS_REGION:", AWS_REGION)
    print("[DEBUG] AWS_BUCKET:", AWS_BUCKET)
    print("[DEBUG] SUPA_URL:", SUPA_URL)
    print("[DEBUG] SUPA_KEY exists:", bool(SUPA_KEY))
    print("[DEBUG] S3_CLIENT:", s3_client)
    print("[DEBUG] SUPABASE:", supabase)
    if not supabase:
        print("[ERROR] Supabase not configured!")
        raise HTTPException(status_code=500, detail="Supabase not configured")
    try:
        # 1. สร้าง unique filename
        file_extension = os.path.splitext(file.filename)[1] or ".jpg"
        unique_filename = f"cats/{uuid.uuid4()}{file_extension}"
        
        # 2. อัพโหลดไฟล์ไปยัง S3
        try:
            s3_client.upload_fileobj(
                file.file,
                AWS_BUCKET,
                unique_filename,
                ExtraArgs={
                    "ContentType": file.content_type,
                    "ACL": "public-read"
                }
            )
        except Exception as s3_error:
            raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(s3_error)}")
        
        # 3. สร้าง public URL
        image_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
        
        # 4. บันทึกข้อมูลลง Supabase
        cat_data = {
            "name": name,
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
            "image_url": image_url
        }
        
        result = supabase.table("cat_locations").insert(cat_data).execute()
        if result.error:
            print("[ERROR] Supabase insert error:", result.error.message)
            raise HTTPException(status_code=500, detail=result.error.message)
        return {"status": "ok", "id": result.data[0]["id"], "image_url": image_url}
    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] Exception in add_location:", str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/locations", response_model=List[CatLocation])
def get_locations():
    try:
        resp = (
            supabase
            .table("cat_photos")
            .select("*")
            .order("uploaded_at", desc=True)
            .execute()
        )
        print("[DEBUG] Supabase resp:", resp)
        print("[DEBUG] Supabase resp.data:", resp.data)
        if not resp.data:
            raise HTTPException(status_code=404, detail="No data returned from Supabase")
        return resp.data
    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] Exception in get_locations:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_extension = file.filename.split(".")[-1]
        key = f"uploads/{uuid.uuid4()}.{file_extension}"  # สร้างชื่อไฟล์ใหม่ไม่ซ้ำ

        # อ่านไฟล์เข้า memory
        file_content = await file.read()

        # อัปโหลดไป S3
        try:
            s3_client.put_object(
                Bucket=AWS_BUCKET,
                Key=key,
                Body=file_content,
                ContentType=file.content_type
            )
        except Exception as s3_error:
            print("[ERROR] S3 upload failed:", str(s3_error))
            raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(s3_error)}")

        s3_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
        return {"url": s3_url}
    except Exception as e:
        print("[ERROR] Exception in /upload:", str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/upload-cat")
async def upload_cat(
    file: UploadFile = File(...),
    lat: float = Form(...),
    lng: float = Form(...),
    description: str = Form(...),
    location_name: str = Form(...),  # เปลี่ยนเป็น location_name
):
    """Upload an image to S3 and save its metadata to Supabase."""

    # 1. ---------- Upload the binary to S3 ----------
    ext = (file.filename.split(".")[-1] if "." in file.filename else "bin")
    key = f"uploads/{uuid.uuid4()}.{ext}"

    try:
        s3_client.put_object(
            Bucket=AWS_BUCKET,
            Key=key,
            Body=await file.read(),
            ContentType=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {str(e)}")

    s3_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"

    # 2. ---------- Insert metadata row into Supabase ----------
    payload = {
        "image_url": s3_url,
        "latitude": lat,
        "longitude": lng,
        "description": description,
        "location_name": location_name,  # ให้ตรงกับ Supabase
    }
    result = supabase.table("cat_photos").insert(payload).execute()

    if getattr(result, 'error', None):
        # Roll back the S3 upload if DB insert failed
        s3_client.delete_object(Bucket=AWS_BUCKET, Key=key)
        raise HTTPException(500, f"Supabase insert failed: {result.error}")

    # --- สำเร็จ ---
    return {"message": "Uploaded", "image_url": s3_url, "row": result.data[0]}