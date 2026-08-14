# ============================================================
# MakeMyTrip PNR Parser
# ============================================================


def parse_pnr_response(data: dict):

    if not isinstance(data, dict):

        raise ValueError(
            "Invalid PNR response"
        )


    # ========================================================
    # TRAIN DETAILS
    # ========================================================

    train_details = data.get(
        "TrainDetails",
        {}
    )

    train = train_details.get(
        "Train",
        {}
    )

    departure_details = train_details.get(
        "DepartureDetails",
        {}
    )


    # ========================================================
    # CITY DETAILS
    # ========================================================

    city_details = data.get(
        "CityDetails",
        {}
    )

    source_city = city_details.get(
        "SourceCity",
        {}
    )

    destination_city = city_details.get(
        "DestinationCity",
        {}
    )


    # ========================================================
    # STATION DETAILS
    # ========================================================

    station_details = data.get(
        "StationDetails",
        {}
    )

    boarding_point = station_details.get(
        "BoardingPoint",
        {}
    )

    reservation_upto = station_details.get(
        "ReservationUpto",
        {}
    )


    # ========================================================
    # PNR DETAILS
    # ========================================================

    pnr_details = data.get(
        "PnrDetails",
        {}
    )

    fare_details = pnr_details.get(
        "FareDetails",
        {}
    )


    # ========================================================
    # PASSENGERS
    # ========================================================

    passenger_details = data.get(
        "PassengerDetails",
        {}
    )

    passengers = passenger_details.get(
        "PassengerStatus",
        []
    )


    parsed_passengers = []

    for passenger in passengers:

        parsed_passengers.append({

            "passenger_number":
                passenger.get("Number"),

            "booking_status":
                passenger.get("BookingStatusNew"),

            "current_status":
                passenger.get("CurrentStatusNew"),

            "booking_berth_no":
                passenger.get("BookingBerthNo"),

            "current_berth_no":
                passenger.get("CurrentBerthNo"),

            "berth":
                passenger.get("Berth")
        })


    # ========================================================
    # RETURN CLEAN RESPONSE
    # ========================================================

    return {

        "success": True,

        "pnr_number":
            pnr_details.get("Pnr"),

        "train_number":
            train.get("Number"),

        "train_name":
            train.get("Name"),

        "source_station":
            source_city.get("Code"),

        "source_station_name":
            source_city.get("Name"),

        "destination_station":
            destination_city.get("Code"),

        "destination_station_name":
            destination_city.get("Name"),

        "boarding_point":
            boarding_point.get("code"),

        "boarding_point_name":
            boarding_point.get("name"),

        "reservation_upto":
            reservation_upto.get("code"),

        "reservation_upto_name":
            reservation_upto.get("name"),

        "journey_date":
            train_details.get(
                "TrainStartingDate"
            ),

        "arrival_date":
            pnr_details.get(
                "DestinationDoj",
                {}
            ).get("FormattedDate"),

        "journey_class":
            pnr_details.get("Class"),

        "journey_class_name":
            pnr_details.get("Text"),

        "current_status":
            pnr_details.get(
                "PnrCurrentStatus"
            ),

        "chart_prepared":
            train_details.get(
                "ChartPrepared"
            ),

        "chart_expected_time":
            train_details.get(
                "ExpectedChartPreparedTime"
            ),

        "booking_fare":
            float(
                fare_details.get(
                    "bookingFare",
                    0
                ) or 0
            ),

        "ticket_fare":
            float(
                fare_details.get(
                    "ticketFare",
                    0
                ) or 0
            ),

        "quota":
            pnr_details.get("Quota"),

        "passenger_count":
            passenger_details.get(
                "Count",
                len(parsed_passengers)
            ),

        "passenger_list":
            parsed_passengers,

        "last_updated":
            data.get("LastUpdated")
    }