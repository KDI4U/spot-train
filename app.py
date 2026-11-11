import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from train_status.routes.train_routes import (
    router as train_router
)

from train_status.routes.pnr_routes import (
    router as pnr_router
)

from train_status.routes.enquiry_train_routes import (
    router as enquiry_train_router,
)


app = FastAPI(
    title="Spot Train API",
    description="Production API for Indian Railways Train Running Status, PNR Enquiry & Train Schedule",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root():
    return {
        "success": True,
        "message": "Spot Train API is running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Spot Train API"
    }


app.include_router(
    train_router,
    prefix="/api/railway/train",
    tags=["Train"]
)

app.include_router(
    pnr_router,
    prefix="/api/railway/pnr",
    tags=["PNR"]
)

app.include_router(
    enquiry_train_router
)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("app:app", host=host, port=port, reload=True)
