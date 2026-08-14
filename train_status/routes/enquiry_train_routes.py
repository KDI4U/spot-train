from fastapi import APIRouter, HTTPException

from train_status.schemas.enquiry_train_schema import (
    EnquiryTrainScheduleRequest,
    EnquiryTrainScheduleResponse,
)

from train_status.services.enquiry_train_service import (
    get_enquiry_train_schedule,
)


router = APIRouter(
    prefix="/api/railway/enquiry/train",
    tags=["Enquiry Train"]
)


@router.post(
    "/schedule",
    response_model=EnquiryTrainScheduleResponse
)
def get_train_schedule(
    request: EnquiryTrainScheduleRequest
):

    try:

        result = get_enquiry_train_schedule(
            train_no=request.train_no,
            journey_date=request.journey_date,
        )

        # Service failed
        if not result.get("success"):

            raise HTTPException(
                status_code=404,
                detail=result.get(
                    "message",
                    "Train schedule not found"
                )
            )

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )