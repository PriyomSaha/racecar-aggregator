import asyncio
async def is_visible(locator, count=0) -> bool:
    try:
        if await locator.is_visible():
            if count >= 3:
                return True
            await asyncio.sleep(0.1)
            return await is_visible(locator, count + 1)
        return False
    except Exception:
        return False

async def is_expanded(locator) -> bool:
    """Asynchronously determine if an element is expanded (visibility-based).

    Use case: convenience async wrapper for checking expandable elements.
    Returns False on errors.
    """
    try:
        return await locator.is_visible()
    except:
        return False

async def exists(locator) -> bool:
    """Asynchronously check whether a locator exists in the DOM.

    Use case: safe existence check for async tests/scripts; returns False
    if an exception occurs while querying.
    """
    try:
        return await locator.count() > 0
    except:
        return False


from typing import Optional


async def get_attr_async(locator, name: str, wait: bool = True, timeout: int = 3000) -> Optional[str]:
    """Safely get an attribute value from a locator (async).

    Returns the attribute string or None if not present or on error.
    If wait is True, waits up to `timeout` ms for the element to be attached.
    """
    try:
        if wait:
            await locator.wait_for(state="attached", timeout=timeout)
        return await locator.get_attribute(name)
    except Exception:
        return None


async def has_class_async(locator, class_name: str, wait: bool = True, timeout: int = 3000) -> bool:
    """Return True if the locator has the specified CSS class (async).

    Handles multiple classes and returns False on errors.
    """
    try:
        if wait:
            await locator.wait_for(state="attached", timeout=timeout)
        cls = await locator.get_attribute("class") or ""
        return class_name in cls.split()
    except Exception:
        return False