import re
import requests

from train_status.utils.constants import (
    NTES_BASE_URL,
    NTES_USER_AGENT
)


class NTESService:

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": NTES_USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Referer": NTES_BASE_URL
        })

    def initialize_session(self):

        response = self.session.get(
            NTES_BASE_URL,
            timeout=30
        )

        response.raise_for_status()

        return response

    def get_csrf_token(self):

        csrf_url = (
            NTES_BASE_URL +
            "GetCSRFToken?t=1234567890"
        )

        response = self.session.get(
            csrf_url,
            timeout=30
        )

        response.raise_for_status()

        csrf_match = re.search(
            r"name=['\"]([^'\"]+)['\"]\s+"
            r"value=['\"]([^'\"]+)['\"]",
            response.text
        )

        if not csrf_match:
            raise Exception(
                "NTES CSRF token not found"
            )

        return (
            csrf_match.group(1),
            csrf_match.group(2)
        )

    def create_session(self):

        self.initialize_session()

        csrf_name, csrf_value = (
            self.get_csrf_token()
        )

        return (
            self.session,
            csrf_name,
            csrf_value
        )

    def fetch_train_html(
        self,
        train_no: str,
        journey_date: str
    ):

        session, csrf_name, csrf_value = (
            self.create_session()
        )

        url = (
            NTES_BASE_URL +
            "tr?opt=TrainRunning&"
            "subOpt=FindRunningInstance"
        )

        payload = {
            "lan": "en",
            "jDate": journey_date,
            "trainNo": train_no,
            csrf_name: csrf_value
        }

        response = session.post(
            url,
            data=payload,
            timeout=60
        )

        response.raise_for_status()

        if not response.text.strip():
            raise Exception(
                "NTES returned empty response"
            )

        return response.text