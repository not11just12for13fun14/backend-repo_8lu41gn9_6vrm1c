import os
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents

app = FastAPI(title="Unified Product Lifecycle & Service Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Unified Service Platform Backend Running"}


@app.get("/test")
def test_database():
    """Connectivity check for database and envs"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["connection_status"] = "Connected"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# ------------ Schemas for requests/responses (lightweight for endpoints) ---------
class ProductIn(BaseModel):
    user_id: str
    brand: str
    model: str
    serial_number: str
    category: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_months: Optional[int] = 12
    invoice_url: Optional[str] = None


class ProductOut(ProductIn):
    id: Optional[str] = None


class ServiceRequestIn(BaseModel):
    user_id: str
    product_id: str
    issue_description: str
    preferred_date: Optional[date] = None
    city: Optional[str] = None
    media_urls: Optional[List[str]] = None


class ServiceRequestOut(ServiceRequestIn):
    status: str = "pending"
    assigned_center_id: Optional[str] = None
    id: Optional[str] = None


# ------------------------------ Helper functions --------------------------------

def collection(name: str):
    return db[name]


def compute_warranty_end(purchase_date: Optional[date], months: Optional[int]) -> Optional[date]:
    if not purchase_date or not months or months <= 0:
        return None
    # Add months approximately as 30 days blocks for MVP
    return purchase_date + timedelta(days=30 * months)


# -------------------------------- API Endpoints ---------------------------------

@app.post("/api/products", response_model=dict)
def add_product(payload: ProductIn):
    """Create a product in the user's digital vault"""
    from schemas import Product as ProductSchema

    # Insert into DB
    product_id = create_document("product", ProductSchema(**payload.model_dump()))

    # Compute derived fields
    warranty_end = compute_warranty_end(payload.purchase_date, payload.warranty_months)

    return {
        "id": product_id,
        "warranty_end": warranty_end.isoformat() if warranty_end else None,
        "message": "Product added successfully",
    }


@app.get("/api/products", response_model=List[dict])
def list_products(user_id: Optional[str] = None, brand: Optional[str] = None):
    """List products, optionally filtered by user or brand"""
    filt = {}
    if user_id:
        filt["user_id"] = user_id
    if brand:
        filt["brand"] = brand
    docs = get_documents("product", filt, limit=100)
    # Convert ObjectIds
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
        # compute warranty_end on the fly
        pd = d.get("purchase_date")
        wm = d.get("warranty_months")
        try:
            if isinstance(pd, str):
                pd_date = date.fromisoformat(pd)
            elif isinstance(pd, datetime):
                pd_date = pd.date()
            else:
                pd_date = pd
        except Exception:
            pd_date = None
        end = compute_warranty_end(pd_date, wm)
        d["warranty_end"] = end.isoformat() if end else None
    return docs


@app.post("/api/service-requests", response_model=dict)
def create_service_request(payload: ServiceRequestIn):
    from schemas import ServiceRequest as SR
    sr_id = create_document("servicerequest", SR(**payload.model_dump()))
    return {"id": sr_id, "message": "Service request created"}


@app.get("/api/service-centers", response_model=List[dict])
def list_service_centers(city: Optional[str] = None, brand: Optional[str] = None):
    """Geo-filtered and brand-filtered service center listing"""
    filt = {}
    if city:
        filt["city"] = city
    if brand:
        filt["brands"] = {"$in": [brand]}
    centers = get_documents("servicecenter", filt, limit=100)
    for c in centers:
        c["id"] = str(c.pop("_id", ""))
    return centers


@app.get("/schema", response_model=dict)
def get_schema_overview():
    """Expose Pydantic schemas for viewers/tools"""
    from schemas import User, Product, ServiceCenter, ServiceRequest, Warranty

    def model_fields(model):
        return {k: str(v.annotation) for k, v in model.model_fields.items()}

    return {
        "collections": [
            {"name": "user", "fields": model_fields(User)},
            {"name": "product", "fields": model_fields(Product)},
            {"name": "servicecenter", "fields": model_fields(ServiceCenter)},
            {"name": "servicerequest", "fields": model_fields(ServiceRequest)},
            {"name": "warranty", "fields": model_fields(Warranty)},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
