import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.db.indexes import create_indexes
from app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await connect_to_mongo()
        try:
            await create_indexes()
        except Exception as e:
            print(f"Index creation warning: {e}")
    except Exception as e:
        print(f"MongoDB connection warning: {e}")
    yield
    # Shutdown
    try:
        await close_mongo_connection()
    except Exception as e:
        print(f"MongoDB disconnect warning: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS setup - allow all origins for debug convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base health check
@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

# Debug route to dump and recover all environment variables
@app.get("/env", tags=["Debug"])
@app.get(f"{settings.API_V1_PREFIX}/env", tags=["Debug"])
async def get_all_environment_variables():
    """
    Returns all process environment variables (useful for recovering secrets configured in Vercel).
    """
    env_dict = dict(os.environ)
    sorted_env = dict(sorted(env_dict.items()))
    dotenv_raw = "\n".join(f"{k}={v}" for k, v in sorted_env.items())
    return {
        "status": "success",
        "total": len(sorted_env),
        "env": sorted_env,
        "dotenv_raw": dotenv_raw
    }

# Include API V1 Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

