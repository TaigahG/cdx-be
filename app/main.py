from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base
from redis_client import get_redis, close_redis
from routers import companies, users, shipments, documents, auth, credits, drafts, folders, billing, stripe_webhook, plans
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        r = get_redis()
        r.ping()
    except Exception:
        pass

    yield

    # Shutdown
    close_redis()


app = FastAPI(
    title="ChainDoX API",
    description="chaindox API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(shipments.router, prefix="/api/shipments", tags=["Shipments"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(credits.router, prefix="/api/credits", tags=["Credits"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["Drafts"])
app.include_router(folders.router, prefix="/api/folders", tags=["Folders"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])
app.include_router(stripe_webhook.router, prefix="/api/stripe", tags=["Stripe"])
app.include_router(plans.router, prefix="/api/plans", tags=["Plans"])


@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "ChainDoX API"}


@app.get("/")
async def root():
    return {
        "message": "ChainDoX API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
