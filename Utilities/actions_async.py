async def safe_click(locator, timeout=5000):
    """Asynchronously click a locator safely.

    Use case: scroll the element into view, wait until it's visible
    (with optional timeout), then click. For use with Playwright's async API.
    """
    await locator.scroll_into_view_if_needed()
    await locator.wait_for(state="visible", timeout=timeout)
    await locator.click()

async def safe_fill(locator, value, clear=True):
    """Asynchronously fill an input safely.

    Use case: ensure the element is visible, optionally clear it, then
    fill it with the provided value. Useful for async flows.
    """
    await locator.scroll_into_view_if_needed()
    await locator.wait_for(state="visible")
    if clear:
        await locator.fill("")
    await locator.fill(value)

async def safe_text(locator):
    """Asynchronously return the trimmed inner text of a locator.

    Use case: wait for attachment and then return the element text with
    whitespace trimmed. Intended for Playwright async locators.
    """
    await locator.wait_for(state="attached")
    return (await locator.inner_text()).strip()