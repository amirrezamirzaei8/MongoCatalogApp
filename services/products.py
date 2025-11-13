# services/products.py
from fastapi import HTTPException, status
from db import get_products_collection
from pymongo.errors import PyMongoError
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# helper to get collection
def _coll():
    return get_products_collection()

# helper for not found SKU
def _not_found(sku: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product with SKU '{sku}' not found"
    )


# --- CRUD operations ---

def create_product(product_data: dict):
    """
    Inserts a new product document.
    """
    coll = _coll()

    # check if SKU already exists
    if coll.find_one({"sku": product_data["sku"]}):
        raise HTTPException(status_code=409, detail="SKU already exists")

    result = coll.insert_one(product_data)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to insert product")

    # return the inserted document (excluding _id)
    return coll.find_one({"sku": product_data["sku"]}, {"_id": 0})


def get_product(sku: str):
    """
    Retrieves a product by SKU.
    """
    coll = _coll()
    doc = coll.find_one({"sku": sku}, {"_id": 0})
    if not doc:
        _not_found(sku)
    return doc


def get_all_products():
    """
    Returns all products.
    """
    coll = _coll()
    products = list(coll.find({}, {"_id": 0}))
    return products


def update_product(sku: str, update_data: dict):
    """
    Updates an existing product.
    """
    coll = _coll()
    res = coll.update_one({"sku": sku}, {"$set": update_data})
    if res.matched_count == 0:
        _not_found(sku)
    return coll.find_one({"sku": sku}, {"_id": 0})


def delete_product(sku: str):
    """
    Deletes a product by SKU.
    """
    coll = _coll()
    res = coll.delete_one({"sku": sku})
    if res.deleted_count == 0:
        _not_found(sku)
    return {"message": f"Product '{sku}' deleted successfully"}

def add_review(sku: str, review_data: dict):
    """
    Adds a review to a product.
    """
    coll = _coll()
    res = coll.update_one({"sku": sku}, {"$push": {"reviews": review_data}})
    if res.matched_count == 0:
        _not_found(sku)
    return coll.find_one({"sku": sku}, {"_id": 0})

def update_review_positional(sku: str, review_id: str, update_data: dict):
    """
    Updates a single review in a product using MongoDB's positional operator ($).
    """
    coll = _coll()

    update_fields = {f"reviews.$.{k}": v for k, v in update_data.items()}
    res = coll.update_one(
        {"sku": sku, "reviews.review_id": review_id},
        {"$set": update_fields}
    )

    if res.matched_count == 0:
        _not_found(sku)

    return coll.find_one({"sku": sku}, {"_id": 0})


def update_review_array_filters(sku: str, filter_criteria: dict, new_data: dict):
    coll = _coll()

    # Build $[rev] placeholder
    update_fields = {f"reviews.$[rev].{k}": v for k, v in new_data.items()}
    array_filters = [{f"rev.{k}": v for k, v in filter_criteria.items()}]

    logger.debug("SKU: %s", sku)
    logger.debug("Filter criteria: %s", filter_criteria)
    logger.debug("New data: %s", new_data)
    logger.debug("Update fields: %s", update_fields)
    logger.debug("Array filters: %s", array_filters)

    res = coll.update_one(
        {"sku": sku},
        {"$set": update_fields},
        array_filters=array_filters  # ← pass list directly
    )

    logger.debug("MongoDB result: %s", res.raw_result)

    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku}' not found")
    if res.modified_count == 0:
        # Improve error message
        raise HTTPException(
            status_code=404,
            detail=f"No review matched filter {filter_criteria} or data unchanged. "
                   f"Array filters used: {array_filters}"
        )

    return coll.find_one({"sku": sku}, {"_id": 0})

