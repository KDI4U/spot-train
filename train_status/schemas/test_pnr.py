import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = "https://www.indianrail.gov.in"

PNR_PAGE = (
    f"{BASE_URL}/enquiry/PNR/PnrEnquiry.html?locale=en"
)

JS_URL = (
    f"{BASE_URL}/enquiry/js/pnrEnquiryJS.js?version=18"
)


session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
})


def print_context(text, keyword, before=1200, after=2500):

    lower = text.lower()
    pos = lower.find(keyword.lower())

    if pos == -1:
        return False

    start = max(0, pos - before)
    end = min(len(text), pos + after)

    print("\n" + "=" * 80)
    print(f"FOUND: {keyword}")
    print("=" * 80)

    print(text[start:end])

    print("=" * 80)

    return True


def main():

    # ------------------------------------------------
    # 1. Open PNR page
    # ------------------------------------------------

    print("Opening PNR page...")

    response = session.get(
        PNR_PAGE,
        timeout=30
    )

    print(
        "PNR page status:",
        response.status_code
    )

    if response.status_code != 200:
        return

    # ------------------------------------------------
    # 2. Get JavaScript
    # ------------------------------------------------

    print("\nDownloading pnrEnquiryJS.js...")

    js_response = session.get(
        JS_URL,
        headers={
            "Referer": PNR_PAGE
        },
        timeout=30
    )

    print(
        "JS status:",
        js_response.status_code
    )

    js = js_response.text

    # ------------------------------------------------
    # 3. Search CAPTCHA related functions
    # ------------------------------------------------

    keywords = [
        "CaptchaImgID",
        "CaptchaImage",
        "captchaImage",
        "refreshCaptcha",
        "generateCaptcha",
        "getCaptcha",
        "CaptchaQuestion",
        "inputCaptcha",
        "CommonCaptcha",
        "CaptchaConfig",
        "firstCaptcha",
        "secondCaptcha",
    ]

    print(
        "\nSearching CAPTCHA implementation..."
    )

    for keyword in keywords:

        print_context(
            js,
            keyword,
            before=1000,
            after=2500
        )

    # ------------------------------------------------
    # 4. Find AJAX URLs
    # ------------------------------------------------

    print(
        "\n\nSearching AJAX/request URLs..."
    )

    lines = js.splitlines()

    for i, line in enumerate(lines):

        line_lower = line.lower()

        if (
            "url :" in line_lower
            or
            "url:" in line_lower
            or
            "$.ajax" in line_lower
        ):

            block = "\n".join(
                lines[
                    max(0, i - 3):
                    min(len(lines), i + 8)
                ]
            )

            if (
                "captcha" in block.lower()
                or
                "pnr" in block.lower()
            ):

                print(
                    "\n--- AJAX BLOCK ---"
                )

                print(block)

    print(
        "\n\nDONE."
    )


if __name__ == "__main__":
    main()