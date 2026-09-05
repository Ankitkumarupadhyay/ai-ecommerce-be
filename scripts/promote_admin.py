import asyncio
import os
import sys
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core.config import settings

async def promote_user(email: str):
    print("Connecting to MongoDB Atlas...")
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    try:
        db = client.get_default_database()
    except Exception:
        db = client[settings.MONGODB_DATABASE]

    result = await db.users.find_one_and_update(
        {"email": email},
        {"$set": {"role": "admin", "updated_at": datetime.now(timezone.utc)}},
        return_document=True
    )

    if result:
        print(f"Successfully promoted user '{email}' (ID: {result['_id']}) to ADMIN role.")
    else:
        print(f"User with email '{email}' not found in database.")

    client.close()

if __name__ == "__main__":
    target_email = sys.argv[1] if len(sys.argv) > 1 else "admin@example.com"
    asyncio.run(promote_user(target_email))
