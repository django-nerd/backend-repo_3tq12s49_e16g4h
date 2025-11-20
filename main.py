import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from database import db, create_document, get_documents
from bson.objectid import ObjectId
import hashlib

app = FastAPI(title="EduSphere API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- Utility helpers ----------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


def serialize(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc

# ---------------------- Schemas ----------------------

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr

class Course(BaseModel):
    title: str
    description: str
    price: float = Field(..., ge=0)
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    level: Optional[str] = Field(None, description="Beginner, Intermediate, Advanced")
    tags: List[str] = []

class Product(BaseModel):
    title: str
    description: str
    price: float = Field(..., ge=0)
    image_url: Optional[str] = None
    file_url: Optional[str] = None
    category: Optional[str] = None

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

# ---------------------- Basic routes ----------------------

@app.get("/")
def root():
    return {"name": "EduSphere API", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# ---------------------- Auth ----------------------

@app.post("/auth/register", response_model=UserOut)
def register(payload: RegisterRequest):
    users = db["user"]
    existing = users.find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_doc = {
        "name": payload.name,
        "email": str(payload.email),
        "password_hash": hash_password(payload.password)
    }
    _id = users.insert_one(user_doc).inserted_id
    return {"id": str(_id), "name": payload.name, "email": payload.email}

@app.post("/auth/login")
def login(payload: LoginRequest):
    users = db["user"]
    user = users.find_one({"email": str(payload.email)})
    if not user or user.get("password_hash") != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = hashlib.sha256(str(user["_id"]).encode()).hexdigest()
    users.update_one({"_id": user["_id"]}, {"$set": {"api_token": token}})
    return {"token": token, "user": {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}}

@app.get("/me", response_model=UserOut)
def me(x_token: Optional[str] = Header(default=None, alias="X-Token")):
    if not x_token:
        raise HTTPException(status_code=401, detail="Missing token")
    user = db["user"].find_one({"api_token": x_token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}

# ---------------------- Courses ----------------------

@app.get("/courses")
def list_courses(limit: int = 50):
    docs = get_documents("course", {}, limit)
    return [serialize(d) for d in docs]

@app.post("/courses")
def create_course(course: Course, x_token: Optional[str] = Header(default=None, alias="X-Token")):
    # simple auth gate for creation
    if not x_token or not db["user"].find_one({"api_token": x_token}):
        raise HTTPException(status_code=401, detail="Unauthorized")
    _id = create_document("course", course)
    doc = db["course"].find_one({"_id": ObjectId(_id)})
    return serialize(doc)

@app.get("/courses/{course_id}")
def get_course(course_id: str):
    doc = db["course"].find_one({"_id": to_object_id(course_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Course not found")
    return serialize(doc)

# ---------------------- Products ----------------------

@app.get("/products")
def list_products(limit: int = 50):
    docs = get_documents("product", {}, limit)
    return [serialize(d) for d in docs]

@app.post("/products")
def create_product(product: Product, x_token: Optional[str] = Header(default=None, alias="X-Token")):
    if not x_token or not db["user"].find_one({"api_token": x_token}):
        raise HTTPException(status_code=401, detail="Unauthorized")
    _id = create_document("product", product)
    doc = db["product"].find_one({"_id": ObjectId(_id)})
    return serialize(doc)

@app.get("/products/{product_id}")
def get_product(product_id: str):
    doc = db["product"].find_one({"_id": to_object_id(product_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize(doc)

# ---------------------- Contact ----------------------

@app.post("/contact")
def send_contact(msg: ContactMessage):
    _id = create_document("contactmessage", msg)
    return {"status": "received", "id": _id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
