from pydantic import BaseModel, Field


# ============================================================
# PNR REQUEST
# ============================================================

class PNRRequest(BaseModel):

    pnr_number: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r"^\d{10}$",
        description="10 digit PNR number"
    )


# ============================================================
# PASSENGER STATUS
# ============================================================

class PassengerStatus(BaseModel):

    passenger_number: int | None = None

    booking_status: str | None = None
    current_status: str | None = None

    booking_berth_no: str | None = None
    current_berth_no: str | None = None

    berth: int | None = None


# ============================================================
# PNR RESPONSE
# ============================================================

class PNRStatusResponse(BaseModel):

    success: bool = True

    pnr_number: str | None = None

    train_number: str | None = None
    train_name: str | None = None

    source_station: str | None = None
    source_station_name: str | None = None

    destination_station: str | None = None
    destination_station_name: str | None = None

    boarding_point: str | None = None
    boarding_point_name: str | None = None

    reservation_upto: str | None = None
    reservation_upto_name: str | None = None

    journey_date: str | None = None
    arrival_date: str | None = None

    journey_class: str | None = None
    journey_class_name: str | None = None

    current_status: str | None = None

    chart_prepared: bool | None = None
    chart_expected_time: str | None = None

    booking_fare: float | None = None
    ticket_fare: float | None = None

    quota: str | None = None

    passenger_count: int = 0

    passenger_list: list[PassengerStatus] = Field(
        default_factory=list
    )

    last_updated: str | None = None