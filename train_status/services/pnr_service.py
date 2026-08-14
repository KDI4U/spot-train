import os
import uuid
import requests

from train_status.parsers.pnr_parser import (
    parse_pnr_response
)


MMT_PNR_URL = (
    "https://mapi.makemytrip.com/"
    "api/rails/pnr/currentstatus/v1"
)


class PNRService:

    def __init__(self):

        self.authorization = os.getenv(
            "MMT_AUTHORIZATION"
        )

        if not self.authorization:

            raise RuntimeError(
                "MMT_AUTHORIZATION is not configured"
            )


    # ========================================================
    # GET PNR STATUS
    # ========================================================

    def get_pnr_status(
        self,
        pnr_number: str
    ):

        # ----------------------------------------------------
        # Generate application device ID
        # ----------------------------------------------------

        device_id = str(
            uuid.uuid4()
        )


        # ----------------------------------------------------
        # Query parameters
        # ----------------------------------------------------

        params = {

            "region": "IN",

            "language": "eng",

            "currency": "inr",

            "user-currency": "INR"
        }


        # ----------------------------------------------------
        # Request payload
        # ----------------------------------------------------

        payload = {

            "pnrID": pnr_number,

            "trackingParams": {

                "affiliateCode": "MMT001",

                "channelCode": "WEB"
            }
        }


        # ----------------------------------------------------
        # Headers
        # ----------------------------------------------------

        headers = {

            "Accept":
                "application/json",

            "Content-Type":
                "application/json",

            "Authorization":
                self.authorization,

            "currency":
                "inr",

            "deviceid":
                device_id,

            "entity-name":
                "india",

            "language":
                "eng",

            "mcid":
                device_id,

            "origin":
                "https://www.makemytrip.com",

            "os":
                "WEB",

            "region":
                "in",

            "user-country":
                "IN",

            "user-currency":
                "INR",

            "usr-mcid":
                device_id,

            "vid":
                device_id,

            "visitor-id":
                device_id,

            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            )
        }


        # ----------------------------------------------------
        # API Request
        # ----------------------------------------------------

        response = requests.post(

            MMT_PNR_URL,

            params=params,

            json=payload,

            headers=headers,

            timeout=60
        )


        # ----------------------------------------------------
        # HTTP error
        # ----------------------------------------------------

        response.raise_for_status()


        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        try:

            data = response.json()

        except ValueError:

            raise Exception(
                "MakeMyTrip returned non-JSON response"
            )


        # ----------------------------------------------------
        # Parse
        # ----------------------------------------------------

        return parse_pnr_response(
            data
        )