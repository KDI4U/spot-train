import requests

from fastapi import APIRouter, HTTPException

from train_status.schemas.pnr_schema import (
    PNRRequest,
    PNRStatusResponse
)

from train_status.services.pnr_service import (
    PNRService
)


router = APIRouter()

pnr_service = PNRService()


# ============================================================
# TEST
# ============================================================

@router.get("/test")
def pnr_test():

    return {

        "success": True,

        "message":
            "PNR API working"
    }


# ============================================================
# PNR STATUS
# ============================================================

@router.post(
    "/status",
    response_model=PNRStatusResponse
)
def pnr_status(
    request: PNRRequest
):

    try:

        result = pnr_service.get_pnr_status(

            pnr_number=request.pnr_number
        )

        return result


    except requests.HTTPError as e:

        status_code = (
            e.response.status_code
            if e.response is not None
            else 502
        )

        raise HTTPException(

            status_code=status_code,

            detail=(
                "MakeMyTrip PNR API request failed: "
                f"{str(e)}"
            )
        )


    except requests.RequestException as e:

        raise HTTPException(

            status_code=502,

            detail=(
                "MakeMyTrip connection failed: "
                f"{str(e)}"
            )
        )


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"PNR processing failed: {str(e)}"
        )