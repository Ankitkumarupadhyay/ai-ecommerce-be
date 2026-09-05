from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.db.mongodb import get_database
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

class ProductService:
    @staticmethod
    async def get_products(
        search: Optional[str] = None,
        category: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[ProductResponse]:
        db = get_database()
        query: Dict[str, Any] = {}
        
        if not include_inactive:
            query["is_active"] = True
            
        if category:
            query["category"] = {"$regex": f"^{category}$", "$options": "i"}
            
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"category": {"$regex": search, "$options": "i"}}
            ]
            
        cursor = db.products.find(query).sort("created_at", -1)
        products = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            products.append(ProductResponse(**doc))
        return products

    @staticmethod
    async def get_product_by_id(product_id: str, include_inactive: bool = False) -> Optional[ProductResponse]:
        if not ObjectId.is_valid(product_id):
            return None
        db = get_database()
        query: Dict[str, Any] = {"_id": ObjectId(product_id)}
        if not include_inactive:
            query["is_active"] = True
            
        doc = await db.products.find_one(query)
        if not doc:
            return None
        doc["id"] = str(doc["_id"])
        return ProductResponse(**doc)

    @staticmethod
    async def create_product(product_in: ProductCreate) -> ProductResponse:
        db = get_database()
        now = datetime.now(timezone.utc)
        product_dict = product_in.model_dump()
        product_dict["created_at"] = now
        product_dict["updated_at"] = now
        
        result = await db.products.insert_one(product_dict)
        product_dict["id"] = str(result.inserted_id)
        return ProductResponse(**product_dict)

    @staticmethod
    async def update_product(product_id: str, product_in: ProductUpdate) -> Optional[ProductResponse]:
        if not ObjectId.is_valid(product_id):
            return None
        db = get_database()
        
        update_data = {k: v for k, v in product_in.model_dump().items() if v is not None}
        if not update_data:
            return await ProductService.get_product_by_id(product_id, include_inactive=True)
            
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        result = await db.products.find_one_and_update(
            {"_id": ObjectId(product_id)},
            {"$set": update_data},
            return_document=True
        )
        if not result:
            return None
        result["id"] = str(result["_id"])
        return ProductResponse(**result)

    @staticmethod
    async def delete_product(product_id: str) -> bool:
        if not ObjectId.is_valid(product_id):
            return False
        db = get_database()
        result = await db.products.delete_one({"_id": ObjectId(product_id)})
        return result.deleted_count > 0

product_service = ProductService()
