async def get_contexts(page, include_iframes=False):
    """Return page contexts (page and optionally frames).

    Use case: when you want to operate on either the main page only or
    include iframe contexts. If include_iframes is False, returns a list
    with the main page; otherwise returns the page's frames collection.
    """
    if not include_iframes:
        return [page]
    return page.frames