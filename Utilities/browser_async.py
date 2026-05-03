# from playwright.async_api import async_playwright
# from screeninfo import get_monitors

# async def get_page(headless=True, user_agent=None):
#     """Start an async Playwright browser and return runtime objects.
    
#     Opens a Chromium browser in headful mode (maximized) if headless=False.
#     Dynamically sets viewport to full screen.
#     """
#     pw = await async_playwright().start()
#     browser = await pw.chromium.launch(headless=headless)

#     # Get primary monitor size
#     monitor = get_monitors()[0]
#     viewport = {"width": monitor.width, "height": monitor.height}

#     context_args = {"viewport": viewport if not headless else None}
#     if user_agent:
#         context_args["user_agent"] = user_agent

#     context = await browser.new_context(**context_args)
#     page = await context.new_page()

#     return pw, browser, context, page

from playwright.async_api import async_playwright

async def get_page(headless=True, user_agent=None):
    
    # pw = await async_playwright().start()
    
    # browser = await pw.chromium.launch(
    #     headless=headless,
    #     args=["--start-maximized"] if not headless else []
    # )

    # context = await browser.new_context(
    #     viewport=None,   # ✅ THIS is the key
    #     user_agent=user_agent,
    #     # locale="en-US",
    #     # extra_http_headers={
    #     #     "Accept-Language": "en-US,en;q=0.9"
    #     # },
    # )

    # page = await context.new_page()
    # return pw, browser, context, page
    
    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )

    pw = await async_playwright().start()

    browser = await pw.chromium.launch(
        headless=headless,
        args=[
            "--start-maximized",
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-infobars",
            "--disable-extensions",
            "--disable-gpu",
        ]
    )

    context = await browser.new_context(
        viewport=None,  # real window size
        user_agent=user_agent,
        locale="en-US",
        timezone_id="Asia/Kolkata",  # ✅ safe, not intrusive like geolocation
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    # 🔥 Patch browser fingerprints
    await context.add_init_script("""
        // Remove webdriver flag
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Fake Chrome runtime
        window.chrome = {
            runtime: {}
        };

        // Fake plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // Fake languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
    """)

    page = await context.new_page()
    return pw, browser, context, page
