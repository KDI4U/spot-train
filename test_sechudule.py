from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

import json
import time
import re
from datetime import datetime


TRAIN_NO = "12221"
JOURNEY_DATE = "15-08-2026"

BASE_URL = "https://enquiry.indianrail.gov.in/mntes/"


# ============================================================
# DATE FORMAT
# ============================================================

def format_date(date_value):
    """
    User date:
        15-08-2026

    NTES date:
        15-Aug-2026
    """

    dt = datetime.strptime(
        date_value,
        "%d-%m-%Y"
    )

    return dt.strftime(
        "%d-%b-%Y"
    )


# ============================================================
# PARSE SCHEDULE
# ============================================================

def parse_schedule(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    schedule = []

    rows = soup.find_all("tr")

    print(
        "TR found:",
        len(rows)
    )

    for row in rows:

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

        # Sr No
        if not re.fullmatch(
            r"\d+",
            values[0]
        ):
            continue

        # ----------------------------------------------------
        # Station
        # ----------------------------------------------------

        fonts = cells[1].find_all("font")

        font_values = [
            f.get_text(
                strip=True
            )
            for f in fonts
        ]

        if len(font_values) >= 2:

            station_name = font_values[0]
            station_code = font_values[1]

        else:

            station_name = values[1]
            station_code = ""

        # ----------------------------------------------------
        # Day
        # ----------------------------------------------------

        day = values[2]

        # ----------------------------------------------------
        # Arrival / Departure
        # ----------------------------------------------------

        time_fonts = cells[3].find_all("font")

        times = [
            f.get_text(
                strip=True
            )
            for f in time_fonts
        ]

        arrival = None
        departure = None

        if len(times) >= 1:
            arrival = times[0]

        if len(times) >= 2:
            departure = times[1]

        # ----------------------------------------------------
        # Halt
        # ----------------------------------------------------

        halt = values[4] or None

        # ----------------------------------------------------
        # Distance
        # ----------------------------------------------------

        distance = values[5]

        try:
            distance = int(distance)
        except ValueError:
            pass

        schedule.append({

            "sr": int(values[0]),

            "station_name":
                station_name,

            "station_code":
                station_code,

            "day":
                day,

            "arrival":
                arrival,

            "departure":
                departure,

            "halt":
                halt,

            "distance_km":
                distance
        })

    return schedule


# ============================================================
# MAIN
# ============================================================

def get_train_schedule(
    train_no,
    journey_date
):

    print("=" * 70)
    print("TRAIN SCHEDULE REQUEST")
    print("=" * 70)

    print(
        "Train No :",
        train_no
    )

    print(
        "Date     :",
        journey_date
    )

    # Convert date
    ntes_date = format_date(
        journey_date
    )

    print(
        "NTES Date:",
        ntes_date
    )

    # ========================================================
    # CHROME OPTIONS
    # ========================================================

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

    wait = WebDriverWait(
        driver,
        20
    )

    try:

        # ====================================================
        # 1. OPEN NTES
        # ====================================================

        print("\n" + "=" * 70)
        print("1. OPEN NTES")
        print("=" * 70)

        driver.get(
            BASE_URL
        )

        print(
            "URL:",
            driver.current_url
        )

        # ====================================================
        # 2. FIND TRAIN INPUT
        # ====================================================

        print("\n2. FIND TRAIN INPUT")

        train_input = wait.until(
            EC.presence_of_element_located(
                (
                    By.ID,
                    "trainNo"
                )
            )
        )

        print(
            "Train input found"
        )

        # ====================================================
        # 3. ENTER TRAIN NUMBER
        # ====================================================

        print("\n3. ENTER TRAIN NUMBER")

        train_input.clear()

        train_input.send_keys(
            train_no
        )

        print(
            "Entered:",
            train_no
        )

        # ====================================================
        # 4. LET NTES LOAD TRAIN
        # ====================================================

        time.sleep(3)

        # ====================================================
        # 5. CALL NTES JS
        # ====================================================

        print(
            "\n4. CALL NTES JS"
        )

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

        time.sleep(4)

        # ====================================================
        # 6. CHECK TRAIN DATA
        # ====================================================

        print(
            "\n5. CHECK TRAIN DATA"
        )

        page_html = driver.page_source

        for text in [
            train_no,
            "HOWRAH",
            "DURONTO"
        ]:

            print(
                f"{text:<25} => "
                f"{text.lower() in page_html.lower()}"
            )

        # ====================================================
        # 7. CHECK JAVASCRIPT FUNCTIONS
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

        print(
            "\nJS functions:",
            js_functions
        )

        # ====================================================
        # 8. SAVE CURRENT WINDOWS
        # ====================================================

        old_windows = set(
            driver.window_handles
        )

        # ====================================================
        # 9. CALL SHOW TRAIN SCHEDULE
        # ====================================================

        print(
            "\n6. OPEN TRAIN SCHEDULE"
        )

        driver.execute_script(
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

        time.sleep(5)

        # ====================================================
        # 10. CHECK WINDOWS
        # ====================================================

        current_windows = set(
            driver.window_handles
        )

        print(
            "Windows:",
            len(current_windows)
        )

        new_windows = (
            current_windows -
            old_windows
        )

        print(
            "New windows:",
            len(new_windows)
        )

        # ====================================================
        # 11. FIND SCHEDULE HTML
        # ====================================================

        schedule_html = None

        for handle in current_windows:

            driver.switch_to.window(
                handle
            )

            time.sleep(1)

            current_html = (
                driver.page_source
            )

            current_url = (
                driver.current_url
            )

            print("\n--------------------------------")
            print("WINDOW")
            print("--------------------------------")

            print(
                "URL:",
                current_url
            )

            print(
                "HTML length:",
                len(current_html)
            )

            # ------------------------------------------------
            # Schedule keywords
            # ------------------------------------------------

            keywords = [
                "PUNE JN",
                "DAUND CHORD LINE",
                "BILASPUR",
                "TATANAGAR",
                "HOWRAH JN"
            ]

            found = 0

            for keyword in keywords:

                if (
                    keyword.lower()
                    in current_html.lower()
                ):

                    found += 1

            print(
                "Schedule keywords:",
                found,
                "/",
                len(keywords)
            )

            if found >= 2:

                schedule_html = (
                    current_html
                )

                print(
                    "✅ Schedule found"
                )

                break

        # ====================================================
        # 12. SCHEDULE NOT FOUND
        # ====================================================

        if schedule_html is None:

            print(
                "\n❌ Schedule not found"
            )

            with open(
                "selenium_debug.html",
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    driver.page_source
                )

            print(
                "Saved: selenium_debug.html"
            )

            return {
                "success": False,
                "train_no": train_no,
                "journey_date": journey_date,
                "total_stations": 0,
                "schedule": []
            }

        # ====================================================
        # 13. SAVE RAW HTML
        # ====================================================

        html_file = (
            f"schedule_{train_no}_"
            f"{journey_date.replace('-', '')}.html"
        )

        with open(
            html_file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                schedule_html
            )

        print(
            "\nHTML saved:",
            html_file
        )

        # ====================================================
        # 14. PARSE
        # ====================================================

        print(
            "\n7. PARSE SCHEDULE"
        )

        schedule = parse_schedule(
            schedule_html
        )

        print(
            "\nTotal Stations:",
            len(schedule)
        )

        # ====================================================
        # 15. PRINT LIST
        # ====================================================

        print(
            "\n" + "=" * 70
        )

        print(
            "SCHEDULE"
        )

        print(
            "=" * 70
        )

        for item in schedule:

            print(
                item
            )

        # ====================================================
        # 16. FINAL JSON
        # ====================================================

        result = {

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
                schedule
        }

        # ====================================================
        # 17. SAVE JSON
        # ====================================================

        json_file = (
            f"train_schedule_"
            f"{train_no}_"
            f"{journey_date.replace('-', '')}.json"
        )

        with open(
            json_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                result,
                f,
                indent=4,
                ensure_ascii=False
            )

        print(
            "\nJSON saved:",
            json_file
        )

        print(
            "\n" + "=" * 70
        )

        print(
            "DONE"
        )

        print(
            "=" * 70
        )

        return result

    finally:

        driver.quit()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    get_train_schedule(
        train_no=TRAIN_NO,
        journey_date=JOURNEY_DATE
    )