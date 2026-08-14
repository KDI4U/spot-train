from fastapi import FastAPI
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
    version="1.0.0"
)


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


@app.get("/")
def root():

    return {
        "success": True,
        "message": "Spot Train API is running"
    }

app.include_router(
    enquiry_train_router
)