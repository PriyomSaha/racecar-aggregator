async def paginate_by_click(page, button_locator, max_pages=10):
    """Paginate by repeatedly clicking a "load more" button.

    Use case: click a pagination or "load more" button until it is no
    longer visible or until `max_pages` iterations are reached. Waits for
    network idle after each click to allow content to load.
    """
    for _ in range(max_pages):
        if not await button_locator.is_visible():
            break
        await button_locator.click()
        await page.wait_for_load_state("networkidle")