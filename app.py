"""
app.py
FastAPI application entry point for the MongoCatalogApp.

Implements:
- /health endpoint
- Full CRUD routes for the products collection
- Inline Pydantic models for validation (no external models.py required)
- Integration with MongoDB via db.py and services/products.py
"""

from fastapi import FastAPI
from typing import List, Optional
from pydantic import BaseModel, Field, condecimal, conint
from datetime import datetime
from services import products  # CRUD logic lives in services/products.py


# ================================================================
# FastAPI Application Initialization
# ================================================================

app = FastAPI(
    title="MongoDB Web Catalog",
    description="Demo app for CST8276 - Advanced Database Topics",
    version="0.1.0",
)


# ================================================================
# Inline Pydantic Models (validation for requests/responses)
# ================================================================

class Review(BaseModel):
    """Represents a single review inside a product."""
    review_id: str
    author: Optional[str] = None
    rating: conint(ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProductCreate(BaseModel):
    """Model for creating a new product."""
    sku: str
    name: str
    price: condecimal(ge=0, max_digits=10, decimal_places=2)
    category: Optional[str] = None
    reviews: List[Review] = []


class ProductUpdate(BaseModel):
    """Model for updating an existing product."""
    name: Optional[str] = None
    price: Optional[condecimal(ge=0, max_digits=10, decimal_places=2)] = None
    category: Optional[str] = None


class ProductOut(BaseModel):
    """Model returned in API responses."""
    sku: str
    name: str
    price: float
    category: Optional[str] = None
    reviews: List[Review] = []


# ================================================================
# Health Check Endpoint
# ================================================================

@app.get("/health")
async def health_check():
    """
    Basic health check endpoint to verify the API is running.
    Returns {"status": "ok"} when operational.
    """
    return {"status": "ok"}


# ================================================================
# Product CRUD Endpoints
# ================================================================

@app.get("/products", response_model=List[ProductOut])
async def list_products():
    """
    Retrieve all products from the MongoDB collection.
    Returns a list of ProductOut models.
    """
    return products.get_all_products()


@app.get("/products/{sku}", response_model=ProductOut)
async def get_product(sku: str):
    """
    Retrieve a single product document by its SKU.
    Raises 404 if the product does not exist.
    """
    return products.get_product(sku)


@app.post("/products", response_model=ProductOut, status_code=201)
async def create_product(body: ProductCreate):
    """
    Create a new product document in MongoDB.
    - Validates request body using ProductCreate model.
    - Returns the newly inserted product.
    - Raises 409 if SKU already exists.
    """
    return products.create_product(body.model_dump())


@app.patch("/products/{sku}", response_model=ProductOut)
async def update_product(sku: str, body: ProductUpdate):
    """
    Update an existing product document by SKU.
    - Accepts partial updates.
    - Raises 404 if the product does not exist.
    """
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    return products.update_product(sku, update_data)


@app.delete("/products/{sku}", status_code=204)
async def delete_product(sku: str):
    """
    Delete a product document by SKU.
    - Raises 404 if SKU not found.
    - Returns 204 No Content on success.
    """
    products.delete_product(sku)
    return


# ================================================================
# Future Enhancements (for teammates)
# ================================================================
# These routes can be extended later by other teammates to include:
# - add_review() and update_review() using MongoDB $push / $set
# - aggregation pipelines for average ratings
# - indexing and performance queries
#
# For now, CRUD endpoints provide the base functionality
# for product management in the catalog.
# ================================================================
