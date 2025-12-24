async def wait_dom(page, timeout=10000):
    """Asynchronously wait until the DOM is fully loaded.

    Use case: ensure document.readyState becomes 'complete' before accessing
    elements that depend on initial page load in async flows.
    """
    await page.wait_for_function(
        "document.readyState === 'complete'",
        timeout=timeout
    )

async def wait_network(page, timeout=10000):
    """Asynchronously wait for network idle state.

    Use case: wait until network activity settles after navigation or async
    actions before proceeding.
    """
    await page.wait_for_load_state("networkidle", timeout=timeout)

async def wait_visible(locator, timeout=8000):
    """Wait until the locator is visible (async).

    Use case: ensure element is visible before interacting in async flows.
    """
    await locator.wait_for(state="visible", timeout=timeout)

async def wait_hidden(locator, timeout=8000):
    """Wait until the locator is hidden (async).

    Use case: wait for overlays/loaders to disappear in async scripts.
    """
    await locator.wait_for(state="hidden", timeout=timeout)

async def wait_attached(locator, timeout=8000):
    """Wait until the locator is attached to the DOM (async).

    Use case: confirm element exists in DOM before further async ops.
    """
    await locator.wait_for(state="attached", timeout=timeout)
    