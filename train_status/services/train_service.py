from datetime import date

from train_status.services.ntes_service import NTESService
from train_status.parsers.train_parser import parse_train_response


class TrainService:

    def __init__(self):
        self.ntes_service = NTESService()

    def spot_train(
        self,
        train_no: str,
        journey_date: date
    ):

        # Python date -> NTES format
        # Example: 2026-08-15 -> 15-Aug-2026
        ntes_date = journey_date.strftime("%d-%b-%Y")

        html = self.ntes_service.fetch_train_html(
            train_no=train_no,
            journey_date=ntes_date
        )

        with open(
            "live_response.html",
            "w",
            encoding="utf-8"
        ) as file:
            file.write(html)

        result = parse_train_response(
            file_name="live_response.html",
            requested_train_no=train_no
        )

        # Important: comma mat lagana
        return result