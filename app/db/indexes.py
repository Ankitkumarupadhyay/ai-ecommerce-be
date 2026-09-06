import logging
from pymongo import IndexModel, ASCENDING
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

async def create_indexes():
    db = get_database()
    if db is None or type(db).__name__ == "MockDatabase":
        logger.info("Using in-memory database or uninitialized client. Skipping index creation.")
        return

    try:
        # Users indexes
        await db.users.create_index([("email", ASCENDING)], unique=True)
        await db.users.create_index([("google_id", ASCENDING)], unique=True)

        # Products indexes
        await db.products.create_index([("category", ASCENDING)])
        await db.products.create_index([("is_active", ASCENDING)])

        # Carts index
        await db.carts.create_index([("user_id", ASCENDING)], unique=True)

        # Orders indexes
        await db.orders.create_index([("user_id", ASCENDING)])
        await db.orders.create_index([("stripe_checkout_session_id", ASCENDING)], sparse=True)

        # Webhook / Payment events idempotency index
        await db.webhook_events.create_index([("event_id", ASCENDING)], unique=True)

        # AI Chat Logs indexes
        await db.ai_chat_logs.create_index([("session_id", ASCENDING)])
        await db.ai_chat_logs.create_index([("user_id", ASCENDING)], sparse=True)
        await db.ai_chat_logs.create_index([("created_at", ASCENDING)])

        logger.info("Successfully initialized MongoDB database indexes.")
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
