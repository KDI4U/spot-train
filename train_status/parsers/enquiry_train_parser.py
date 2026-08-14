from bs4 import BeautifulSoup
import re


def parse_enquiry_train_schedule(html: str) -> list[dict]:
    """
    Parse NTES train schedule HTML into a list of station dictionaries.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    schedule = []

    rows = soup.find_all("tr")

    for row in rows:

        cells = row.find_all("td")

        # NTES schedule row has 6 columns
        if len(cells) != 6:
            continue

        values = [
            cell.get_text(
                " ",
                strip=True
            )
            for cell in cells
        ]

        # First column must be Sr No
        if not re.fullmatch(
            r"\d+",
            values[0]
        ):
            continue

        # ====================================================
        # STATION NAME + CODE
        # ====================================================

        fonts = cells[1].find_all("font")

        font_values = [
            font.get_text(
                strip=True
            )
            for font in fonts
        ]

        if len(font_values) >= 2:

            station_name = font_values[0]
            station_code = font_values[1]

        else:

            station_name = values[1]
            station_code = ""

        # ====================================================
        # DAY
        # ====================================================

        day = values[2]

        # ====================================================
        # ARRIVAL / DEPARTURE
        # ====================================================

        time_fonts = cells[3].find_all("font")

        times = [
            font.get_text(
                strip=True
            )
            for font in time_fonts
        ]

        arrival = None
        departure = None

        if len(times) >= 1:
            arrival = times[0]

        if len(times) >= 2:
            departure = times[1]

        # ====================================================
        # HALT
        # ====================================================

        halt = values[4] or None

        # ====================================================
        # DISTANCE
        # ====================================================

        distance_km = values[5]

        try:
            distance_km = int(distance_km)
        except (ValueError, TypeError):
            distance_km = None

        # ====================================================
        # FIRST / LAST STATION NORMALIZATION
        # ====================================================

        # SRC = Source marker, not an arrival time
        if arrival == "SRC":
            arrival = None

        # DSTN = Destination marker, not a departure time
        if departure == "DSTN":
            departure = None

        # ====================================================
        # ADD STATION
        # ====================================================

        schedule.append(
            {
                "sr": int(values[0]),
                "station_name": station_name,
                "station_code": station_code,
                "day": day,
                "arrival": arrival,
                "departure": departure,
                "halt": halt,
                "distance_km": distance_km,
            }
        )

    return schedule