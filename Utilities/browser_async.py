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
    pw = await async_playwright().start()

    browser = await pw.chromium.launch(
        headless=headless,
        args=["--start-maximized"] if not headless else []
    )

    context = await browser.new_context(
        viewport=None,   # ✅ THIS is the key
        user_agent=user_agent
    )

    page = await context.new_page()
    return pw, browser, context, page
