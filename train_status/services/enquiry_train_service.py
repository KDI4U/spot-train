from datetime import datetime
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

from train_status.parsers.enquiry_train_parser import (
    parse_enquiry_train_schedule,
)


BASE_URL = "https://enquiry.indianrail.gov.in/mntes/"


# ============================================================
# DATE VALIDATION
# ============================================================

def format_ntes_date(journey_date: str) -> str:
    """
    Convert:

        15-08-2026

    into:

        15-Aug-2026
    """

    try:

        date_obj = datetime.strptime(
            journey_date,
            "%d-%m-%Y"
        )

    except ValueError:

        raise ValueError(
            "journey_date must be in DD-MM-YYYY format"
        )

    return date_obj.strftime(
        "%d-%b-%Y"
    )


# ============================================================
# SELENIUM DRIVER
# ============================================================

def create_driver():

    options = Options()

    # Browser UI नहीं दिखेगा
    options.add_argument(
        "--headless=new"
    )

    options.add_argument(
        "--window-size=1920,1080"
    )

    options.add_argument(
        "--disable-gpu"
    )

    options.add_argument(
        "--no-sandbox"
    )

    options.add_argument(
        "--disable-dev-shm-usage"
    )

    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )

    driver = webdriver.Chrome(
        options=options
    )

    return driver


# ============================================================
# GET TRAIN SCHEDULE
# ============================================================

def get_enquiry_train_schedule(
    train_no: str,
    journey_date: str,
) -> dict:

    """
    Get Indian Railways NTES train schedule.

    Input:

        train_no = "12221"
        journey_date = "15-08-2026"
    """

    # ========================================================
    # VALIDATE INPUT
    # ========================================================

    train_no = str(
        train_no
    ).strip()

    journey_date = str(
        journey_date
    ).strip()

    if not train_no:

        raise ValueError(
            "train_no is required"
        )

    if not train_no.isdigit():

        raise ValueError(
            "train_no must contain only numbers"
        )

    # Validate date
    ntes_date = format_ntes_date(
        journey_date
    )

    driver = None

    try:

        # ====================================================
        # 1. START SELENIUM
        # ====================================================

        driver = create_driver()

        wait = WebDriverWait(
            driver,
            20
        )

        # ====================================================
        # 2. OPEN NTES
        # ====================================================

        driver.get(
            BASE_URL
        )

        # ====================================================
        # 3. FIND TRAIN INPUT
        # ====================================================

        train_input = wait.until(
            EC.presence_of_element_located(
                (
                    By.ID,
                    "trainNo"
                )
            )
        )

        # ====================================================
        # 4. ENTER TRAIN NUMBER
        # ====================================================

        train_input.clear()

        train_input.send_keys(
            train_no
        )

        # ====================================================
        # 5. CALL onTrainInput()
        # ====================================================

        driver.execute_script(
            """
            if (
                typeof window.onTrainInput ===
                'function'
            ) {
                window.onTrainInput();
            }
            """
        )

        # ====================================================
        # WAIT FOR TRAIN DATA
        # ====================================================

        wait.until(
            lambda d:
            train_no in d.page_source
        )

        time.sleep(3)

        # ====================================================
        # 6. VERIFY TRAIN DATA
        # ====================================================

        page_html = driver.page_source

        if train_no not in page_html:

            return {
                "success": False,
                "message": "Train number not found",
                "train_no": train_no,
                "journey_date": journey_date,
                "total_stations": 0,
                "schedule": [],
            }

        # ====================================================
        # 7. CHECK SCHEDULE FUNCTION
        # ====================================================

        js_functions = driver.execute_script(
            """
            return {
                showTrainSchedule:
                    typeof window.showTrainSchedule,

                showTrainServiceSchedule:
                    typeof window.showTrainServiceSchedule
            };
            """
        )

        # ====================================================
        # 8. OPEN TRAIN SCHEDULE
        # ====================================================

        schedule_opened = False

        if (
            js_functions.get(
                "showTrainSchedule"
            )
            == "function"
        ):

            result = driver.execute_script(
                """
                if (
                    typeof window.showTrainSchedule ===
                    'function'
                ) {

                    window.showTrainSchedule('K');

                    return true;
                }

                return false;
                """
            )

            schedule_opened = bool(
                result
            )

        # ====================================================
        # 9. WAIT FOR SCHEDULE
        # ====================================================

        if not schedule_opened:

            return {
                "success": False,
                "message": "Unable to open train schedule",
                "train_no": train_no,
                "journey_date": journey_date,
                "total_stations": 0,
                "schedule": [],
            }

        time.sleep(5)

        # ====================================================
        # 10. FIND SCHEDULE HTML
        # ====================================================

        schedule_html = None

        for handle in driver.window_handles:

            driver.switch_to.window(
                handle
            )

            time.sleep(1)

            html = driver.page_source

            html_lower = html.lower()

            # ------------------------------------------------
            # Generic NTES schedule indicators
            # ------------------------------------------------

            schedule_indicators = [

                "train schedule",

                "days of run",

                "reserved class of travel",

                "dist. kms.",

                "station",

                "arr.",

                "dep.",
            ]

            found_indicators = sum(
                1
                for indicator
                in schedule_indicators
                if indicator in html_lower
            )

            # ------------------------------------------------
            # Find actual schedule rows
            # ------------------------------------------------

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            schedule_rows = 0

            for row in soup.find_all("tr"):

                cells = row.find_all("td")

                if len(cells) != 6:
                    continue

                values = [
                    cell.get_text(
                        " ",
                        strip=True
                    )
                    for cell in cells
                ]

                if not values:
                    continue

                # First column should be Sr No
                if not values[0].isdigit():
                    continue

                schedule_rows += 1

            # ------------------------------------------------
            # DEBUG
            # ------------------------------------------------

            print(
                "Schedule indicators:",
                found_indicators
            )

            print(
                "Schedule rows:",
                schedule_rows
            )

            # ------------------------------------------------
            # Generic schedule detection
            # ------------------------------------------------

            if (
                found_indicators >= 3
                and schedule_rows >= 1
            ):

                schedule_html = html

                print(
                    "✅ GENERIC NTES SCHEDULE FOUND"
                )

                break

        # ====================================================
        # 11. SCHEDULE NOT FOUND
        # ====================================================

        if not schedule_html:

            return {
                "success": False,
                "message": "Train schedule not found",
                "train_no": train_no,
                "journey_date": journey_date,
                "total_stations": 0,
                "schedule": [],
            }

        # ====================================================
        # 12. PARSE HTML
        # ====================================================

        schedule = (
            parse_enquiry_train_schedule(
                schedule_html
            )
        )

        # ====================================================
        # 13. RETURN RESULT
        # ====================================================

        return {

            "success":
                len(schedule) > 0,

            "train_no":
                train_no,

            "journey_date":
                journey_date,

            "ntes_date":
                ntes_date,

            "total_stations":
                len(schedule),

            "schedule":
                schedule,
        }

    except Exception as exc:

        return {

            "success": False,

            "message":
                str(exc),

            "train_no":
                train_no,

            "journey_date":
                journey_date,

            "total_stations":
                0,

            "schedule":
                [],
        }

    finally:

        # ====================================================
        # CLOSE SELENIUM
        # ====================================================

        if driver:

            try:

                driver.quit()

            except Exception:

                pass