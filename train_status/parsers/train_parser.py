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

    # --------------------------------------------------------
    # Distance from source (KMs)
    #
    # Every halt except the source prints "Coach Position
    # <N> KMs"; the source prints "Coach Position SRC" instead
    # (i.e. 0 KMs). This is the only reliable, monotonically
    # increasing signal available for "is the train past this
    # station yet" -- scheduled/actual arrival & departure times
    # are NOT reliable for that (NTES fills in a projected time
    # for stations still ahead of the train too, not just ones
    # it has actually reached).
    # --------------------------------------------------------

    # Verified against a real NTES stop-train page: a halting station's row (div.stopRow,
    # what this function parses) never carries a KM-from-source figure anywhere in its text.
    # "Coach Position" is an unrelated modal button (physical coach layout on the platform,
    # opened via data-bs-toggle="modal") that happens to reuse similar wording -- it is not a
    # distance marker. A bare "<b>N</b> KMs" distance value does exist on the page, but only
    # on the separate non-stopping/pass-through rows (div.nonStopRow) this parser does not
    # collect. So there is no reliable per-stop distance signal available here; leave it null
    # except for the source, which is unambiguously 0.
    distance_km = 0 if is_source else None

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
        "distance_km": distance_km,

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

# Station names on NTES are always short (a handful of words) -- bounding every "station name"
# capture group to this many characters means a regex that fails to find its expected terminator
# nearby can never backtrack across the rest of the scraped page and swallow unrelated content
# into current_station (see _sanitize_current_station for the second line of defense).
MAX_STATION_NAME_CHARS = 60


def _sanitize_current_station(name):
    """
    Rejects a captured "current station" value that is clearly not a station name -- either
    because it's implausibly long, or because it contains markers (KMs, Coach Position,
    Non-Stopping, ...) that only ever appear when a regex has swallowed unrelated page content.
    This is a safety net independent of which pattern matched, since NTES's exact phrasing has
    already been observed to drift (see the "on DD-Mon-YYYY HH:MM" vs "at HH:MM DD-Mon" cases
    below) and may drift again.
    """

    if not name:
        return None

    cleaned = clean_current_station_name(name)

    if not cleaned:
        return None

    if len(cleaned) > MAX_STATION_NAME_CHARS:
        return None

    if re.search(
        r"\bKMs\b|Coach Position|Non-Stopping|Upcoming Station",
        cleaned,
        re.IGNORECASE
    ):
        return None

    return cleaned


def _match_movement_banner(text):
    """
    Matches NTES's simple movement-banner phrasing:

        Departed from BHAWANI MANDI(BWM) at 11:46 14-Aug (Delay: 00:06)
        Arrived at BHAWANI MANDI(BWM) at 11:46 14-Aug (Delay: 00:06)

    This is the exact phrasing used inside the page's single, purpose-built
    <h6 class="text-primary"> status element (see CASE 0 below), and is tried first there
    against just that short string. It is also tried again further down against the wider
    scoped page text, as a fallback for when that element isn't found.
    """

    patterns = [
        (
            "Departed",
            re.compile(
                r"Departed\s+from\s+"
                r"(.{1,%d}?)" % MAX_STATION_NAME_CHARS +
                r"\s+at\s+"
                r"(\d{1,2}:\d{2})\s+"
                r"(\d{1,2}-[A-Za-z]{3})"
                r"\s*"
                r"\(Delay:\s*([^)]+)\)",
                re.IGNORECASE
            )
        ),
        (
            "Departed",
            re.compile(
                r"Departed\s+from\s+"
                r"(.{1,%d}?)" % MAX_STATION_NAME_CHARS +
                r"\s+at\s+"
                r"(\d{1,2}:\d{2})\s+"
                r"(\d{1,2}-[A-Za-z]{3})"
                r".{0,30}?"
                r"Delay:\s*([0-9:]+)",
                re.IGNORECASE
            )
        ),
        (
            "Arrived",
            re.compile(
                r"Arrived\s+at\s+"
                r"(.{1,%d}?)" % MAX_STATION_NAME_CHARS +
                r"\s+at\s+"
                r"(\d{1,2}:\d{2})\s+"
                r"(\d{1,2}-[A-Za-z]{3})"
                r"\s*"
                r"\(Delay:\s*([^)]+)\)",
                re.IGNORECASE
            )
        ),
        (
            "Arrived",
            re.compile(
                r"Arrived\s+at\s+"
                r"(.{1,%d}?)" % MAX_STATION_NAME_CHARS +
                r"\s+at\s+"
                r"(\d{1,2}:\d{2})\s+"
                r"(\d{1,2}-[A-Za-z]{3})"
                r".{0,30}?"
                r"Delay:\s*([0-9:]+)",
                re.IGNORECASE
            )
        )
    ]

    for movement_type, pattern in patterns:

        match = pattern.search(text)

        if not match:
            continue

        # Reject and keep trying the next pattern/case rather than returning: a match whose
        # captured group isn't a plausible station name means the "at HH:MM DD-Mon" terminator
        # this pattern expects wasn't actually nearby, and .+? backtracked across unrelated
        # page content instead (see _sanitize_current_station).
        sanitized = _sanitize_current_station(
            match.group(1)
        )

        if not sanitized:
            continue

        return {
            "type": movement_type,
            "current_station": sanitized,
            "delay": clean_text(match.group(4)),
            "movement_time": match.group(2),
            "movement_date": match.group(3),
            "distance_km": None
        }

    return None


def parse_current_running_info(full_text, scope=None):

    # --------------------------------------------------------
    # Normalize text for reliable matching
    # --------------------------------------------------------

    normalized_text = clean_text(full_text)

    # ========================================================
    # CASE 0
    #
    # NTES renders the current-running status in a single, purpose-built element:
    # <h6 class="text-primary"><b>Arrived at BIHTA(BTA) at 12:12 14-Aug (Delay: 01:09)</b></h6>
    # This is the least ambiguous signal on the page -- try it first, scoped to just that
    # element's own short text, before falling back to scanning the wider page below (which
    # can contain similar-looking phrases elsewhere, e.g. other days' history).
    # ========================================================

    if scope is not None:

        banner = scope.select_one("h6.text-primary")

        if banner:

            banner_info = _match_movement_banner(
                clean_text(banner.get_text(" ", strip=True))
            )

            if banner_info:
                return banner_info

    # ========================================================
    # CASE 1 / CASE 2
    #
    # Same phrasing as CASE 0, but the dedicated element wasn't found -- fall back to
    # searching for it within the wider (but still date-scoped) page text.
    # ========================================================

    banner_info = _match_movement_banner(normalized_text)

    if banner_info:
        return banner_info

    # ========================================================
    # CASE 3
    #
    # NTES's per-station table row uses a different phrasing
    # than the summary banner above (CASE 1/2): instead of
    # "at HH:MM DD-Mon" it reads e.g.
    #
    #   RAJBANDH - RBH 151 KMs Departed from RAJBANDH (RBH)
    #     on 14-Aug-2026 18:28
    #   RANI KAMALAPATI - RKMP 1674 KMs Departed from
    #     RANI KAMALAPATI (RKMP) on 14-Aug-2026 20:31
    #
    # The "STATION - CODE <N> KMs" prefix right before
    # "Departed from/Arrived at/Reported from" is the only
    # reliable distance-from-source signal available anywhere
    # in the page for the live position itself (see distance_km
    # on parse_station) -- captured here when present so the
    # frontend can place the live marker between the correct
    # two halts instead of guessing from arrival/departure data
    # (which NTES also fills in as a projection for stations the
    # train hasn't reached yet, so it can't be used for that).
    # No "(Delay: ...)" is attached directly here -- delay for
    # this case comes from the same page-wide fallback search
    # used below.
    # ========================================================

    on_date_pattern = re.compile(
        r"(?:[A-Z][A-Z0-9 .'\-]{0,%d}?\s*-\s*[A-Z0-9]+\s+(\d+)\s*KMs\s+" % MAX_STATION_NAME_CHARS +
        r")?"
        r"(?:Departed\s+from|Arrived\s+at|Reported\s+from)\s+"
        r"(.{1,%d}?)" % MAX_STATION_NAME_CHARS +
        r"\s+on\s+"
        r"\d{1,2}-[A-Za-z]{3}-\d{4}\s+"
        r"\d{1,2}:\d{2}",
        re.IGNORECASE
    )

    on_date_match = on_date_pattern.search(
        normalized_text
    )

    if on_date_match:

        sanitized = _sanitize_current_station(
            on_date_match.group(2)
        )

        if sanitized:

            delay_match = re.search(
                r"\(Delay:\s*([^)]+)\)",
                normalized_text,
                re.IGNORECASE
            )

            return {
                "type": "Running",
                "current_station": sanitized,
                "delay": clean_text(delay_match.group(1)) if delay_match else None,
                "movement_time": None,
                "movement_date": None,
                "distance_km": int(on_date_match.group(1)) if on_date_match.group(1) else None
            }

    # ========================================================
    # FALLBACK
    #
    # Sometimes NTES may return the current station and
    # delay in a slightly different text layout. Still bounded
    # and sanitized -- an unmatched terminator here must not
    # fall through to garbage the way the unbounded version of
    # this pattern used to.
    # ========================================================

    current_station_match = re.search(
        r"(?:Departed\s+from|Arrived\s+at)\s+"
        r"(.{1,%d}?)" % MAX_STATION_NAME_CHARS +
        r"(?:\s+at\s+\d{1,2}:\d{2})",
        normalized_text,
        re.IGNORECASE
    )

    delay_match = re.search(
        r"\(Delay:\s*([^)]+)\)",
        normalized_text,
        re.IGNORECASE
    )

    if current_station_match:

        sanitized = _sanitize_current_station(
            current_station_match.group(1)
        )

        if sanitized:

            return {
                "type": "Running",
                "current_station": sanitized,
                "delay": clean_text(delay_match.group(1)) if delay_match else None,
                "movement_time": None,
                "movement_date": None,
                "distance_km": None
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
        "movement_date": None,
        "distance_km": None
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
# Resolve Active Date Scope
# ============================================================

def get_active_date_scope(soup):
    """
    NTES's spot-train page bundles several days into a single document: one
    <div class="tab-pane ... active" id="trainDD-mon-yyyy"> block for the requested/current
    date, plus one more such block per recent day the same train number ran (each with its
    own already-completed "Reached Destination" banner and its own div.stopRow station
    list) -- only the block carrying the "active" class is the date actually asked for.
    Everything that reads the current-running banner or the station table must be scoped to
    just this element; reading from the whole page mixes in unrelated days' banners and
    station data (verified against a real captured NTES response).

    Falls back to the whole soup if this structure isn't found, so a page that doesn't use
    the multi-day-tabs layout (or a future markup change) degrades to the old behavior
    instead of returning nothing.
    """

    active_scope = soup.select_one(
        'div.tab-pane.active[id^="train"]'
    )

    return active_scope if active_scope else soup


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
    html=None,
    file_name=None,
    requested_train_no=None,
    html_content=None
):

    # --------------------------------------------------------
    # Read HTML (From memory or file)
    # --------------------------------------------------------

    if html is None:
        html = html_content

    if html is None and file_name:
        with open(
            file_name,
            "r",
            encoding="utf-8"
        ) as f:
            html = f.read()

    if html is None:
        raise ValueError("html content or file_name must be provided")
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
        "current_distance_km": None,
        "delay": None,
        "last_updated": None,
        "stations": []
    }

    # ========================================================
    # Active Date Scope
    #
    # See get_active_date_scope() -- the page bundles several days into one
    # document, and everything below except train_no/train_name (which sit
    # outside/above the per-date blocks) must be read from just today's block.
    # ========================================================

    active_scope = get_active_date_scope(soup)

    full_text = clean_text(
        active_scope.get_text(
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
        parse_route_header(active_scope)
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
            full_text,
            scope=active_scope
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

    result["current_distance_km"] = (
        current_info.get("distance_km")
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

    stop_rows = active_scope.select(
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