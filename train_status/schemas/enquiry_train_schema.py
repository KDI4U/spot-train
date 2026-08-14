from pydantic import BaseModel, Field
from typing import Optional, List


class EnquiryTrainScheduleRequest(BaseModel):
    train_no: str = Field(
        ...,
        min_length=1,
        description="Indian Railways train number"
    )

    journey_date: str = Field(
        ...,
        description="Journey date in DD-MM-YYYY format"
    )


class EnquiryTrainStation(BaseModel):
    sr: int
    station_name: str
    station_code: str
    day: str
    arrival: Optional[str] = None
    departure: Optional[str] = None
    halt: Optional[str] = None
    distance_km: Optional[int] = None


class EnquiryTrainScheduleResponse(BaseModel):
    success: bool
    train_no: str
    journey_date: str
    total_stations: int
    schedule: List[EnquiryTrainStation]