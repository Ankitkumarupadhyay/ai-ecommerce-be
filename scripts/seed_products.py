import asyncio
import os
import sys
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings

SAMPLE_PRODUCTS = [
    {
        "name": "Wireless Noise-Canceling Headphones",
        "description": "Premium over-ear wireless headphones with active noise cancellation, 30-hour battery life, and spatial audio.",
        "price": 249.99,
        "currency": "usd",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500",
        "stock": 25,
        "category": "Electronics",
        "is_active": True
    },
    {
        "name": "Minimalist Mechanical Keyboard",
        "description": "Custom compact RGB mechanical keyboard with tactile switches and durable PBT keycaps.",
        "price": 129.50,
        "currency": "usd",
        "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500",
        "stock": 18,
        "category": "Electronics",
        "is_active": True
    },
    {
        "name": "Ergonomic Aluminium Laptop Stand",
        "description": "Elevate your workspace with this premium anodized aluminum laptop stand engineered for optimal cooling.",
        "price": 49.99,
        "currency": "usd",
        "image_url": "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500",
        "stock": 40,
        "category": "Electronics",
        "is_active": True
    },
    {
        "name": "Organic Heavyweight Cotton Hoodie",
        "description": "Ultra-soft 450gsm organic cotton hoodie with a cozy relaxed fit and reinforced double stitching.",
        "price": 85.00,
        "currency": "usd",
        "image_url": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=500",
        "stock": 30,
        "category": "Clothing",
        "is_active": True
    },
    {
        "name": "Water-Resistant Commuter Backpack",
        "description": "Sleek 22L urban backpack featuring a padded 16-inch laptop compartment and anti-theft hidden pockets.",
        "price": 110.00,
        "currency": "usd",
        "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500",
        "stock": 15,
        "category": "Accessories",
        "is_active": True
    },
    {
        "name": "Stainless Steel Insulated Tumbler",
        "description": "Double-wall vacuum insulated 32oz tumbler keeps drinks ice cold for 24 hours or piping hot for 12 hours.",
        "price": 34.99,
        "currency": "usd",
        "image_url": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=500",
        "stock": 50,
        "category": "Home",
        "is_active": True
    },
    {
        "name": "Smart Fitness Watch & Tracker",
        "description": "Track your heart rate, sleep metrics, and workouts with an vivid AMOLED display and 7-day battery life.",
        "price": 179.99,
        "currency": "usd",
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500",
        "stock": 20,
        "category": "Electronics",
        "is_active": True
    },
    {
        "name": "Ceramic Pour-Over Coffee Set",
        "description": "Handcrafted matte ceramic dripper and glass carafe set for brewing barista-grade specialty coffee at home.",
        "price": 58.00,
        "currency": "usd",
        "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500",
        "stock": 12,
        "category": "Home",
        "is_active": True
    },
    {
        "name": "Polarized Classic Aviator Sunglasses",
        "description": "Lightweight titanium frame sunglasses featuring UV400 anti-glare polarized lenses.",
        "price": 95.00,
        "currency": "usd",
        "image_url": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=500",
        "stock": 22,
        "category": "Accessories",
        "is_active": True
    },
    {
        "name": "4K Ultra HD Streaming Webcam",
        "description": "Crisp 4K 60fps webcam with dual noise-canceling microphones and automatic low-light correction.",
        "price": 139.99,
        "currency": "usd",
        "image_url": "https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=500",
        "stock": 10,
        "category": "Electronics",
        "is_active": True
    }
]

async def seed_products():
    print("Connecting to MongoDB Atlas...")
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    try:
        db = client.get_default_database()
    except Exception:
        db = client[settings.MONGODB_DATABASE]

    now = datetime.now(timezone.utc)
    print("Clearing existing products...")
    await db.products.delete_many({})

    print(f"Seeding {len(SAMPLE_PRODUCTS)} sample products...")
    for p in SAMPLE_PRODUCTS:
        p["created_at"] = now
        p["updated_at"] = now

    result = await db.products.insert_many(SAMPLE_PRODUCTS)
    print(f"Successfully seeded {len(result.inserted_ids)} products into collection 'products'.")

    client.close()

if __name__ == "__main__":
    asyncio.run(seed_products())
