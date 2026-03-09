from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import companies, users, shipments, documents

app = FastAPI(
    title="ChainDoX API",
    description="chaindox API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(shipments.router, prefix="/api/shipments", tags=["Shipments"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ChainDoX API"}

@app.get("/")
async def root():
    return {
        "message": "ChainDoX API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)