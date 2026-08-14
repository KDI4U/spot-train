from playwright.sync_api import sync_playwright


PNR = "6206202109"

URL = (
    "https://www.indianrail.gov.in/"
    "enquiry/PNR/PnrEnquiry.html?locale=en"
)


def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        context = browser.new_context(
            viewport={
                "width": 1366,
                "height": 900
            }
        )

        page = context.new_page()

        # ------------------------------------------------
        # Capture all important requests/responses
        # ------------------------------------------------

        def request_handler(request):

            if (
                "CommonCaptcha" in request.url
                or "Captcha" in request.url
            ):
                print("\n========== REQUEST ==========")
                print(request.method)
                print(request.url)

                if request.post_data:
                    print("POST DATA:")
                    print(request.post_data)

        def response_handler(response):

            if (
                "CommonCaptcha" in response.url
                or "Captcha" in response.url
            ):
                print("\n========== RESPONSE ==========")
                print(response.status)
                print(response.url)

                try:
                    print(response.text())
                except Exception:
                    pass

        page.on(
            "request",
            request_handler
        )

        page.on(
            "response",
            response_handler
        )

        # ------------------------------------------------
        # Open PNR page
        # ------------------------------------------------

        print("Opening Indian Railways PNR page...")

        page.goto(
            URL,
            wait_until="networkidle",
            timeout=60000
        )

        print(
            "Page loaded:",
            page.title()
        )

        # ------------------------------------------------
        # Fill PNR
        # ------------------------------------------------

        print("\nEntering PNR...")

        pnr_input = page.locator(
            "#inputPnrNo"
        )

        pnr_input.fill(PNR)

        # ------------------------------------------------
        # Wait for CAPTCHA
        # ------------------------------------------------

        print("\nWaiting for CAPTCHA...")

        captcha_image = page.locator(
            "#CaptchaImgID"
        )

        captcha_image.wait_for(
            state="visible",
            timeout=30000
        )

        print(
            "CAPTCHA element found."
        )

        # Give browser time to render image
        page.wait_for_timeout(2000)

        # ------------------------------------------------
        # Save screenshot
        # ------------------------------------------------

        page.screenshot(
            path="pnr_page.png",
            full_page=True
        )

        print(
            "\nScreenshot saved:"
            " pnr_page.png"
        )

        # ------------------------------------------------
        # Ask user for CAPTCHA
        # ------------------------------------------------

        captcha = input(
            "\nEnter CAPTCHA shown in browser: "
        ).strip()

        if not captcha:

            print(
                "CAPTCHA cannot be empty."
            )

            browser.close()
            return

        # ------------------------------------------------
        # Fill CAPTCHA
        # ------------------------------------------------

        page.locator(
            "#inputCaptcha"
        ).fill(captcha)

        # ------------------------------------------------
        # Submit
        # ------------------------------------------------

        print(
            "\nSubmitting PNR..."
        )

        page.locator(
            "#submitPnrNo"
        ).click()

        # ------------------------------------------------
        # Wait for response
        # ------------------------------------------------

        page.wait_for_timeout(5000)

        print(
            "\nCurrent URL:"
        )

        print(
            page.url
        )

        # ------------------------------------------------
        # Print page text
        # ------------------------------------------------

        print(
            "\n========== PAGE TEXT ==========\n"
        )

        print(
            page.locator("body").inner_text()
        )

        print(
            "\n=============================="
        )

        input(
            "\nPress ENTER to close browser..."
        )

        browser.close()


if __name__ == "__main__":
    main()