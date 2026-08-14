from bs4 import BeautifulSoup
import json
import re


# ============================================================
# Utility
# ============================================================

def clean_text(value):

    if not value:
        return ""

    return " ".join(value.split())


# ============================================================
# Parse One Station Row
# ============================================================

def parse_station(row):

    # --------------------------------------------------------
    # Find station-name font
    # --------------------------------------------------------

    station_font = None

    for font in row.find_all(
        "font",
        attrs={"size": "1"}
    ):

        inner_container = font.find(
            "div",
            class_="w3-container"
        )

        if inner_container:

            station_font = font
            break

    if not station_font:

        return None

    # --------------------------------------------------------
    # Station name
    # --------------------------------------------------------

    station_b = station_font.find("b")

    if not station_b:

        return None

    station = clean_text(
        station_b.get_text(
            " ",
            strip=True
        )
    )

    if not station:

        return None

    # --------------------------------------------------------
    # Ignore invalid blocks
    # --------------------------------------------------------

    if station in [
        "SRC",
        "DSTN"
    ]:

        return None

    if "Non-Stopping" in station:

        return None

    # --------------------------------------------------------
    # Station code + platform
    # --------------------------------------------------------

    code = None
    platform = None

    inner_container = station_font.find(
        "div",
        class_="w3-container"
    )

    if inner_container:

        code_b = inner_container.find("b")

        if code_b:

            direct_parts = []

            for child in code_b.children:

                if getattr(
                    child,
                    "name",
                    None
                ) == "span":

                    continue

                text_value = str(child).strip()

                if text_value:

                    direct_parts.append(
                        text_value
                    )

            code = clean_text(
                " ".join(direct_parts)
            )

            pf_span = code_b.find("span")

            if pf_span:

                pf_text = clean_text(
                    pf_span.get_text(
                        " ",
                        strip=True
                    )
                )

                pf_match = re.search(
                    r"PF\s*([A-Za-z0-9-]+)",
                    pf_text,
                    re.IGNORECASE
                )

                if pf_match:

                    platform = (
                        pf_match.group(1)
                    )

    # --------------------------------------------------------
    # Full station row text
    # --------------------------------------------------------

    row_text = clean_text(
        row.get_text(
            " ",
            strip=True
        )
    )

    # --------------------------------------------------------
    # Extract ALL time/date values.
    #
    # Normal row:
    #   scheduled arrival + scheduled departure
    #
    # Live row:
    #   scheduled arrival
    #   actual arrival
    #   scheduled departure
    #   actual departure
    #
    # Example from screenshot:
    #
    # 10:48 14-Aug
    # 11:53 14-Aug
    # 10:50 14-Aug
    # 11:57 14-Aug
    # --------------------------------------------------------

    times = re.findall(
        r"\b\d{1,2}:\d{2}\s+"
        r"\d{1,2}-[A-Za-z]{3}\b",
        row_text
    )

    # --------------------------------------------------------
    # Defaults
    # --------------------------------------------------------

    scheduled_arrival = None
    actual_arrival = None

    scheduled_departure = None
    actual_departure = None

    arrival_delay = None
    departure_delay = None

    # --------------------------------------------------------
    # Helper
    # --------------------------------------------------------

    def extract_time(value):

        if not value:

            return None

        return value.split()[0]

    # --------------------------------------------------------
    # Source station
    # --------------------------------------------------------

    is_source = bool(
        re.search(
            r"\bSRC\b",
            row_text,
            re.IGNORECASE
        )
    )

    # --------------------------------------------------------
    # Destination station
    # --------------------------------------------------------

    is_destination = bool(
        re.search(
            r"\bDSTN\b",
            row_text,
            re.IGNORECASE
        )
    )

    # ========================================================
    # FOUR TIMES
    #
    # Live/current station row.
    #
    # Example:
    #
    # Arrival:
    #   10:48 scheduled
    #   11:53 actual
    #
    # Departure:
    #   10:50 scheduled
    #   11:57 actual
    # ========================================================

    if len(times) >= 4:

        scheduled_arrival = extract_time(
            times[0]
        )

        actual_arrival = extract_time(
            times[1]
        )

        scheduled_departure = extract_time(
            times[2]
        )

        actual_departure = extract_time(
            times[3]
        )

    # ========================================================
    # THREE TIMES
    #
    # Usually source/destination/live special layout.
    # Keep best possible interpretation.
    # ========================================================

    elif len(times) == 3:

        if is_source:

            scheduled_departure = (
                extract_time(times[0])
            )

            actual_departure = (
                extract_time(times[1])
            )

        elif is_destination:

            scheduled_arrival = (
                extract_time(times[0])
            )

            actual_arrival = (
                extract_time(times[1])
            )

        else:

            scheduled_arrival = (
                extract_time(times[0])
            )

            actual_arrival = (
                extract_time(times[1])
            )

            scheduled_departure = (
                extract_time(times[2])
            )

    # ========================================================
    # TWO TIMES
    #
    # Normal scheduled station row:
    #
    # arrival + departure
    # ========================================================

    elif len(times) == 2:

        if is_source:

            scheduled_departure = (
                extract_time(times[0])
            )

        elif is_destination:

            scheduled_arrival = (
                extract_time(times[0])
            )

        else:

            scheduled_arrival = (
                extract_time(times[0])
            )

            scheduled_departure = (
                extract_time(times[1])
            )

    # ========================================================
    # ONE TIME
    # ========================================================

    elif len(times) == 1:

        if is_destination:

            scheduled_arrival = (
                extract_time(times[0])
            )

        else:

            scheduled_departure = (
                extract_time(times[0])
            )

    # --------------------------------------------------------
    # Delay extraction
    # --------------------------------------------------------

    # Example:
    #
    # 01:05 Hr
    # 01:07 Hr
    #
    # or:
    #
    # 6 Min
    # 8 Min
    # --------------------------------------------------------

    hr_delays = re.findall(
        r"\b\d{1,2}:\d{2}\s+Hr\b",
        row_text,
        re.IGNORECASE
    )

    min_delays = re.findall(
        r"\b\d+\s+Min\b",
        row_text,
        re.IGNORECASE
    )

    # --------------------------------------------------------
    # If two hour delays are available:
    #
    # first = arrival delay
    # second = departure delay
    # --------------------------------------------------------

    if len(hr_delays) >= 2:

        arrival_delay = clean_text(
            hr_delays[0]
        )

        departure_delay = clean_text(
            hr_delays[1]
        )

    elif len(min_delays) >= 2:

        arrival_delay = clean_text(
            min_delays[0]
        )

        departure_delay = clean_text(
            min_delays[1]
        )

    elif len(hr_delays) == 1:

        if is_destination:

            arrival_delay = clean_text(
                hr_delays[0]
            )

        else:

            departure_delay = clean_text(
                hr_delays[0]
            )

    elif len(min_delays) == 1:

        if is_destination:

            arrival_delay = clean_text(
                min_delays[0]
            )

        else:

            departure_delay = clean_text(
                min_delays[0]
            )

    # --------------------------------------------------------
    # On Time
    # --------------------------------------------------------

    if re.search(
        r"\bOn\s+Time\b",
        row_text,
        re.IGNORECASE
    ):

        if is_destination:

            if not arrival_delay:

                arrival_delay = "On Time"

        elif is_source:

            if not departure_delay:

                departure_delay = "On Time"

        else:

            if not arrival_delay:

                arrival_delay = "On Time"

            if not departure_delay:

                departure_delay = "On Time"

    # --------------------------------------------------------
    # Backward-compatible fields
    #
    # arrival/departure now represent ACTUAL time when
    # actual time exists; otherwise scheduled time.
    # --------------------------------------------------------

    arrival = (
        actual_arrival
        or scheduled_arrival
    )

    departure = (
        actual_departure
        or scheduled_departure
    )

    # --------------------------------------------------------
    # Overall delay
    #
    # For compatibility:
    # - if departure delay exists, use it
    # - otherwise arrival delay
    # --------------------------------------------------------

    overall_delay = (
        departure_delay
        or arrival_delay
    )

    return {
        "station": station,
        "code": code,
        "platform": platform,

        # Existing fields
        "arrival": arrival,
        "departure": departure,
        "delay": overall_delay,

        # New detailed fields
        "scheduled_arrival": scheduled_arrival,
        "actual_arrival": actual_arrival,
        "arrival_delay": arrival_delay,

        "scheduled_departure":
            scheduled_departure,
        "actual_departure":
            actual_departure,
        "departure_delay":
            departure_delay
    }


# ============================================================
# Clean Station Name
# ============================================================

def clean_current_station_name(value):

    if not value:

        return None

    value = clean_text(value)

    # --------------------------------------------------------
    # Example:
    #
    # BHAWANI MANDI(BWM)
    #
    # Convert to:
    #
    # BHAWANI MANDI
    # --------------------------------------------------------

    match = re.match(
        r"^(.+?)\s*\(([A-Z0-9]+)\)$",
        value
    )

    if match:

        return clean_text(
            match.group(1)
        )

    return value


# ============================================================
# Parse Current Running Information
# ============================================================

def parse_current_running_info(full_text):

    # --------------------------------------------------------
    # Normalize text for reliable matching
    # --------------------------------------------------------

    normalized_text = clean_text(full_text)

    current_station = None
    delay = None
    movement_time = None
    movement_date = None

    # ========================================================
    # CASE 1
    #
    # Departed from BHAWANI MANDI(BWM)
    # at 11:46 14-Aug
    # (Delay: 00:06)
    # ========================================================

    departed_patterns = [
        re.compile(
            r"Departed\s+from\s+"
            r"(.+?)"
            r"\s+at\s+"
            r"(\d{1,2}:\d{2})\s+"
            r"(\d{1,2}-[A-Za-z]{3})"
            r"\s*"
            r"\(Delay:\s*([^)]+)\)",
            re.IGNORECASE
        ),
        re.compile(
            r"Departed\s+from\s+"
            r"(.+?)"
            r"\s+at\s+"
            r"(\d{1,2}:\d{2})\s+"
            r"(\d{1,2}-[A-Za-z]{3})"
            r".{0,30}?"
            r"Delay:\s*([0-9:]+)",
            re.IGNORECASE
        )
    ]

    departed_match = None

    for pattern in departed_patterns:

        departed_match = pattern.search(
            normalized_text
        )

        if departed_match:
            break

    if departed_match:

        current_station = (
            departed_match.group(1)
        )

        movement_time = (
            departed_match.group(2)
        )

        movement_date = (
            departed_match.group(3)
        )

        delay = (
            departed_match.group(4)
        )

        return {
            "type": "Departed",
            "current_station":
                clean_current_station_name(
                    current_station
                ),
            "delay": clean_text(delay),
            "movement_time":
                movement_time,
            "movement_date":
                movement_date
        }

    # ========================================================
    # CASE 2
    #
    # Arrived at BHAWANI MANDI(BWM)
    # at 11:46 14-Aug
    # (Delay: 00:06)
    # ========================================================

    arrived_patterns = [
        re.compile(
            r"Arrived\s+at\s+"
            r"(.+?)"
            r"\s+at\s+"
            r"(\d{1,2}:\d{2})\s+"
            r"(\d{1,2}-[A-Za-z]{3})"
            r"\s*"
            r"\(Delay:\s*([^)]+)\)",
            re.IGNORECASE
        ),
        re.compile(
            r"Arrived\s+at\s+"
            r"(.+?)"
            r"\s+at\s+"
            r"(\d{1,2}:\d{2})\s+"
            r"(\d{1,2}-[A-Za-z]{3})"
            r".{0,30}?"
            r"Delay:\s*([0-9:]+)",
            re.IGNORECASE
        )
    ]

    arrived_match = None

    for pattern in arrived_patterns:

        arrived_match = pattern.search(
            normalized_text
        )

        if arrived_match:
            break

    if arrived_match:

        current_station = (
            arrived_match.group(1)
        )

        movement_time = (
            arrived_match.group(2)
        )

        movement_date = (
            arrived_match.group(3)
        )

        delay = (
            arrived_match.group(4)
        )

        return {
            "type": "Arrived",
            "current_station":
                clean_current_station_name(
                    current_station
                ),
            "delay": clean_text(delay),
            "movement_time":
                movement_time,
            "movement_date":
                movement_date
        }

    # ========================================================
    # FALLBACK
    #
    # Sometimes NTES may return the current station and
    # delay in a slightly different text layout.
    # ========================================================

    current_station_match = re.search(
        r"(?:Departed\s+from|Arrived\s+at)\s+"
        r"(.+?)(?:\s+at\s+\d{1,2}:\d{2})",
        normalized_text,
        re.IGNORECASE
    )

    delay_match = re.search(
        r"\(Delay:\s*([^)]+)\)",
        normalized_text,
        re.IGNORECASE
    )

    if current_station_match:

        current_station = clean_current_station_name(
            current_station_match.group(1)
        )

        if delay_match:

            delay = clean_text(
                delay_match.group(1)
            )

        return {
            "type": "Running",
            "current_station": current_station,
            "delay": delay,
            "movement_time": None,
            "movement_date": None
        }

    # ========================================================
    # DEBUG
    #
    # If this happens, the browser may show current status
    # dynamically while the direct NTES response does not
    # contain the same text.
    # ========================================================

    print()
    print("=" * 100)
    print("CURRENT TRAIN STATUS DEBUG")
    print("=" * 100)

    for keyword in [
        "Departed from",
        "Arrived at",
        "Reached Destination",
        "Last Updates On",
        "Delay:"
    ]:

        print(
            f"{keyword:<25} => "
            f"{keyword.lower() in normalized_text.lower()}"
        )

    print("-" * 100)

    # Print useful portions of the response instead of
    # printing the complete HTML/text.
    for keyword in [
        "Departed",
        "Arrived",
        "Reached",
        "Last Updates",
        "Delay"
    ]:

        match = re.search(
            rf".{{0,180}}{re.escape(keyword)}.{{0,250}}",
            normalized_text,
            re.IGNORECASE
        )

        if match:

            print(
                f"\n{keyword} context:\n"
                f"{match.group(0)}"
            )

    print("=" * 100)
    print()

    return {
        "type": None,
        "current_station": None,
        "delay": None,
        "movement_time": None,
        "movement_date": None
    }


# ============================================================
# Determine Train Status
# ============================================================

def determine_train_status(
    full_text,
    current_info
):

    # --------------------------------------------------------
    # Live movement always gets highest priority
    # --------------------------------------------------------

    if current_info["type"] in [
        "Departed",
        "Arrived",
        "Running"
    ]:

        return "Running"

    # --------------------------------------------------------
    # Cancelled
    # --------------------------------------------------------

    if re.search(
        r"\bCancelled\b",
        full_text,
        re.IGNORECASE
    ):

        return "Cancelled"

    # --------------------------------------------------------
    # Not Started
    # --------------------------------------------------------

    if re.search(
        r"Not Started",
        full_text,
        re.IGNORECASE
    ):

        return "Not Started"

    # --------------------------------------------------------
    # Reached Destination
    # --------------------------------------------------------

    if re.search(
        r"Reached Destination",
        full_text,
        re.IGNORECASE
    ):

        return "Reached Destination"

    # --------------------------------------------------------
    # Running fallback
    # --------------------------------------------------------

    if re.search(
        r"\bRunning\b",
        full_text,
        re.IGNORECASE
    ):

        return "Running"

    return None


# ============================================================
# Parse Route Header
# ============================================================

def parse_route_header(soup):

    source = None
    destination = None

    route_header = soup.find("h5")

    if not route_header:

        return source, destination

    route_text = clean_text(
        route_header.get_text(
            " ",
            strip=True
        )
    )

    # --------------------------------------------------------
    # Example:
    #
    # AMRITSAR - BANDRA TERMINUS
    #
    # --------------------------------------------------------

    route_match = re.search(
        r"(.+?)"
        r"\s+-\s+"
        r"(.+?)"
        r"(?:\s+Average Delay|$)",
        route_text,
        re.IGNORECASE
    )

    if route_match:

        source = clean_text(
            route_match.group(1)
        )

        destination = clean_text(
            route_match.group(2)
        )

    return source, destination


# ============================================================
# Merge Duplicate Stations
# ============================================================

def merge_duplicate_stations(stations):

    merged = []

    index_by_key = {}

    for station in stations:

        key = station.get("code")

        if not key:

            key = station.get(
                "station"
            )

        if not key:

            continue

        key = key.upper().strip()

        # ----------------------------------------------------
        # First occurrence
        # ----------------------------------------------------

        if key not in index_by_key:

            index_by_key[key] = len(
                merged
            )

            merged.append(
                station.copy()
            )

            continue

        # ----------------------------------------------------
        # Duplicate occurrence
        # ----------------------------------------------------

        existing_index = (
            index_by_key[key]
        )

        existing = merged[
            existing_index
        ]

        # ----------------------------------------------------
        # New detailed fields
        # ----------------------------------------------------

        fields = [
            "scheduled_arrival",
            "actual_arrival",
            "arrival_delay",
            "scheduled_departure",
            "actual_departure",
            "departure_delay"
        ]

        for field in fields:

            new_value = station.get(
                field
            )

            if not new_value:

                continue

            # Actual/live value should win.
            if (
                field.startswith("actual_")
                or field.endswith("_delay")
            ):

                if (
                    new_value != "On Time"
                    or not existing.get(field)
                ):

                    existing[field] = (
                        new_value
                    )

            elif not existing.get(field):

                existing[field] = (
                    new_value
                )

        # ----------------------------------------------------
        # Platform
        # ----------------------------------------------------

        if station.get("platform"):

            existing["platform"] = (
                station["platform"]
            )

        # ----------------------------------------------------
        # Backward-compatible arrival/departure
        # ----------------------------------------------------

        existing["arrival"] = (
            existing.get("actual_arrival")
            or existing.get(
                "scheduled_arrival"
            )
        )

        existing["departure"] = (
            existing.get("actual_departure")
            or existing.get(
                "scheduled_departure"
            )
        )

        existing["delay"] = (
            existing.get("departure_delay")
            or existing.get("arrival_delay")
        )

    return merged


# ============================================================
# Parse Complete Train Response
# ============================================================

def parse_train_response(
    html,
    requested_train_no=None
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # --------------------------------------------------------
    # Result structure
    # --------------------------------------------------------

    result = {
        "success": True,
        "train_no": None,
        "train_name": None,
        "source": None,
        "destination": None,
        "status": None,
        "current_station": None,
        "delay": None,
        "last_updated": None,
        "stations": []
    }

    # ========================================================
    # Full Page Text
    # ========================================================

    full_text = clean_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    # ========================================================
    # TRAIN NUMBER + TRAIN NAME
    # ========================================================

    train_no = (
        str(requested_train_no)
        if requested_train_no
        else None
    )

    # --------------------------------------------------------
    # First: requested train number
    # --------------------------------------------------------

    for h3 in soup.find_all("h3"):

        text = clean_text(
            h3.get_text(
                " ",
                strip=True
            )
        )

        if (
            train_no
            and text.startswith(
                train_no + " "
            )
        ):

            result["train_no"] = train_no

            result["train_name"] = text[
                len(train_no):
            ].strip()

            break

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if not result["train_no"]:

        for h3 in soup.find_all("h3"):

            text = clean_text(
                h3.get_text(
                    " ",
                    strip=True
                )
            )

            match = re.match(
                r"^(\d{4,5})\s+(.+)$",
                text
            )

            if match:

                result["train_no"] = (
                    match.group(1)
                )

                result["train_name"] = (
                    match.group(2).strip()
                )

                break

    # ========================================================
    # ROUTE HEADER
    # ========================================================

    route_source, route_destination = (
        parse_route_header(soup)
    )

    result["source"] = route_source
    result["destination"] = (
        route_destination
    )

    # ========================================================
    # CURRENT RUNNING INFORMATION
    # ========================================================

    current_info = (
        parse_current_running_info(
            full_text
        )
    )

    print(
        "Parsed current train info:",
        current_info
    )

    result["current_station"] = (
        current_info[
            "current_station"
        ]
    )

    result["delay"] = (
        current_info["delay"]
    )

    # ========================================================
    # STATUS
    # ========================================================

    result["status"] = (
        determine_train_status(
            full_text,
            current_info
        )
    )

    # ========================================================
    # LAST UPDATED
    # ========================================================

    updated_match = re.search(
        r"Last Updates On\s+"
        r"(\d{1,2}-[A-Za-z]{3}-\d{4})\s+"
        r"(\d{2}:\d{2})",
        full_text,
        re.IGNORECASE
    )

    if updated_match:

        result["last_updated"] = (
            f"{updated_match.group(1)} "
            f"{updated_match.group(2)}"
        )

    # ========================================================
    # STATIONS
    # ========================================================

    stop_rows = soup.select(
        "div.stopRow"
    )

    print(
        f"Found stop rows: {len(stop_rows)}"
    )

    raw_stations = []

    for row in stop_rows:

        station = parse_station(
            row
        )

        if station:

            raw_stations.append(
                station
            )

    # ========================================================
    # MERGE DUPLICATES
    # ========================================================

    result["stations"] = (
        merge_duplicate_stations(
            raw_stations
        )
    )

    # ========================================================
    # SOURCE / DESTINATION
    #
    # Station list is more reliable than route
    # header because it contains actual station data.
    # ========================================================

    if result["stations"]:

        result["source"] = (
            result["stations"][0][
                "station"
            ]
        )

        result["destination"] = (
            result["stations"][-1][
                "station"
            ]
        )

    # ========================================================
    # Fallback to Route Header
    # ========================================================

    if not result["source"]:

        result["source"] = (
            route_source
        )

    if not result["destination"]:

        result["destination"] = (
            route_destination
        )

    # ========================================================
    # RETURN
    # ========================================================

    return result


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    with open("response.html", "r", encoding="utf-8") as f:
        sample_html = f.read()

    result = parse_train_response(
        html=sample_html,
        requested_train_no="12904"
    )

    print()
    print("=" * 80)
    print("FINAL JSON")
    print("=" * 80)

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )