import logging
import asyncio
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

class MockCollection:
    def __init__(self, name: str):
        self.name = name
        self.docs: List[Dict[str, Any]] = []

    async def create_index(self, keys, **kwargs):
        pass

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for doc in self.docs:
            match = True
            for k, v in query.items():
                if k == "$or" and isinstance(v, list):
                    or_match = any(
                        all(doc.get(sub_k) == sub_v for sub_k, sub_v in sub_q.items())
                        for sub_q in v
                    )
                    if not or_match:
                        match = False
                        break
                elif str(doc.get(k)) != str(v) and doc.get(k) != v:
                    match = False
                    break
            if match:
                res = doc.copy()
                return res
        return None

    def find(self, query: Dict[str, Any] = None):
        matching = []
        query = query or {}
        search_kw = None

        if "$or" in query:
            for sub_q in query["$or"]:
                for sub_k, sub_v in sub_q.items():
                    if isinstance(sub_v, dict) and "$regex" in sub_v:
                        search_kw = sub_v["$regex"].lower()

        for doc in self.docs:
            if "is_active" in query and doc.get("is_active") != query["is_active"]:
                continue
            if "category" in query and isinstance(query["category"], dict) and "$regex" in query["category"]:
                cat_pat = query["category"]["$regex"].lower().replace("^", "").replace("$", "")
                if doc.get("category", "").lower() != cat_pat:
                    continue
            if "user_id" in query and str(doc.get("user_id")) != str(query["user_id"]):
                continue
            if search_kw:
                combined = f"{doc.get('name', '')} {doc.get('description', '')} {doc.get('category', '')}".lower()
                if search_kw not in combined:
                    continue
            matching.append(doc.copy())

        class AsyncCursor:
            def __init__(self, items):
                self.items = items
            def sort(self, key, direction):
                return self
            def __aiter__(self):
                self.index = 0
                return self
            async def __anext__(self):
                if self.index < len(self.items):
                    item = self.items[self.index]
                    self.index += 1
                    return item
                raise StopAsyncIteration

        return AsyncCursor(matching)

    async def insert_one(self, doc: Dict[str, Any]):
        from bson import ObjectId
        doc_copy = doc.copy()
        if "_id" not in doc_copy:
            doc_copy["_id"] = ObjectId()
        self.docs.append(doc_copy)

        class InsertResult:
            inserted_id = doc_copy["_id"]
        return InsertResult()

    async def insert_many(self, docs: List[Dict[str, Any]]):
        from bson import ObjectId
        inserted_ids = []
        for d in docs:
            d_copy = d.copy()
            if "_id" not in d_copy:
                d_copy["_id"] = ObjectId()
            self.docs.append(d_copy)
            inserted_ids.append(d_copy["_id"])

        class InsertManyResult:
            def __init__(self, ids):
                self.inserted_ids = ids
        return InsertManyResult(inserted_ids)

    async def update_one(self, filter_q: Dict[str, Any], update_q: Dict[str, Any]):
        doc = await self.find_one(filter_q)
        if doc:
            idx = self.docs.index(doc)
            target = self.docs[idx]
            if "$set" in update_q:
                target.update(update_q["$set"])
            if "$inc" in update_q:
                for k, v in update_q["$inc"].items():
                    target[k] = target.get(k, 0) + v

    async def find_one_and_update(self, filter_q: Dict[str, Any], update_q: Dict[str, Any], return_document=True):
        doc = await self.find_one(filter_q)
        if doc:
            idx = self.docs.index(doc)
            target = self.docs[idx]
            if "$set" in update_q:
                target.update(update_q["$set"])
            if "$inc" in update_q:
                for k, v in update_q["$inc"].items():
                    target[k] = target.get(k, 0) + v
            return target.copy()
        return None

    async def delete_one(self, filter_q: Dict[str, Any]):
        doc = await self.find_one(filter_q)
        if doc:
            self.docs.remove(doc)
            class DeleteResult:
                deleted_count = 1
            return DeleteResult()
        class DeleteResult:
            deleted_count = 0
        return DeleteResult()

    async def delete_many(self, filter_q: Dict[str, Any]):
        count = len(self.docs)
        self.docs.clear()
        class DeleteResult:
            deleted_count = count
        return DeleteResult()

class MockDatabase:
    def __init__(self):
        self.users = MockCollection("users")
        self.products = MockCollection("products")
        self.carts = MockCollection("carts")
        self.orders = MockCollection("orders")
        self.webhook_events = MockCollection("webhook_events")
        self.ai_chat_logs = MockCollection("ai_chat_logs")

mock_db = MockDatabase()

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Any = None
    is_mock: bool = False

db = Database()

async def connect_to_mongo():
    logger.info("Attempting MongoDB connection...")
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=10000)
        # Test connection ping with timeout
        await asyncio.wait_for(client.admin.command('ping'), timeout=5.0)
        db.client = client
        try:
            db.db = client.get_default_database()
        except Exception:
            db.db = client[settings.MONGODB_DATABASE]
        db.is_mock = False
        logger.info(f"Connected to MongoDB database: {db.db.name}")
    except Exception as e:
        logger.warning(f"MongoDB connection unavailable ({e}). Using in-memory database store for full functionality.")
        db.client = None
        db.db = mock_db
        db.is_mock = True
        # Seed mock database with default products
        await seed_mock_database()

async def seed_mock_database():
    if not mock_db.products.docs:
        from scripts.seed_products import SAMPLE_PRODUCTS
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        for p in SAMPLE_PRODUCTS:
            p_copy = p.copy()
            p_copy["created_at"] = now
            p_copy["updated_at"] = now
            await mock_db.products.insert_one(p_copy)

async def close_mongo_connection():
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    return db.db if db.db is not None else mock_db
