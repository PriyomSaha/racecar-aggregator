async def infinite_scroll(page, steps=10, pause=800):
    """Perform repeated page scrolls to load additional content.

    Use case: simulate user scrolling to trigger lazy-loading or infinite
    pagination. `steps` controls the number of scroll iterations and
    `pause` (ms) waits between scrolls.
    """
    for _ in range(steps):
        await page.mouse.wheel(0, 4000)
        await page.wait_for_timeout(pause)


async def scroll_into_view(locator, wait: bool = True, timeout: int = 3000) -> bool:
    """Scroll the given locator into view if needed.

    Use case: call this before interacting with an element to ensure it
    is visible in the viewport. The function optionally waits for the
    element to be attached, performs a Playwright scroll-into-view,
    and returns True on success or False on error.

    Args:
        locator: Playwright locator or element handle.
        wait: whether to wait for element to be attached before scrolling.
        timeout: ms to wait for attachment when `wait` is True.
    Returns:
        bool: True if scrolled (or already visible); False on failure.
    """
    try:
        if wait:
            await locator.wait_for(state="attached", timeout=timeout)
        # Playwright API: ensure element is in viewport
        await locator.scroll_into_view_if_needed()
        return True
    except Exception:
        return False