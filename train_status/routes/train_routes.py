import requests

from datetime import datetime, date

from fastapi import APIRouter, HTTPException, Query

from train_status.services.train_service import TrainService


router = APIRouter()

train_service = TrainService()


@router.get("/test")
def train_test():

    return {
        "success": True,
        "message": "Train API working"
    }


@router.get("/spot/{train_no}")
def spot_train(
    train_no: str,
    journey_date: str = Query(
        default_factory=lambda: date.today().strftime("%d-%m-%Y"),
        description="Journey date in DD-MM-YYYY format"
    )
):

    # --------------------------------------------------
    # Train number validation
    # --------------------------------------------------

    if not train_no.isdigit():

        raise HTTPException(
            status_code=400,
            detail="Train number must contain digits only"
        )

    # --------------------------------------------------
    # Date validation
    # --------------------------------------------------

    try:

        parsed_date = datetime.strptime(
            journey_date,
            "%d-%m-%Y"
        ).date()

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid journey_date. Use DD-MM-YYYY format"
        )

    # --------------------------------------------------
    # Call service
    # --------------------------------------------------

    try:

        return train_service.spot_train(
            train_no=train_no,
            journey_date=parsed_date
        )

    except requests.RequestException as e:

        raise HTTPException(
            status_code=502,
            detail=f"NTES request failed: {str(e)}"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Train processing failed: {str(e)}"
        )