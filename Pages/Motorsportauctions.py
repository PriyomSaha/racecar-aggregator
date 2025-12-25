"""Pages.Motorsportauctions

Helpers for scraping MotorsportAuctions site using Playwright page API.

This module provides `MotorsportAuctions` which encapsulates navigation
and data-collection logic for motorsportauctions.com. Methods are written
as async coroutines and rely on utility helpers in `Utilities`.
"""

from Utilities.actions_async import safe_click, safe_text
from Utilities.output import as_excel
from Utilities.scroll_async import scroll_into_view
from Utilities.waits_async import wait_dom, wait_network
from Utilities.state_async import is_visible
from typing import Optional
from playwright.async_api import Locator


class MotorsportAuctions:
    """Page object for motorsportauctions.com.

    Args:
        page: Playwright `page` object used to interact with the site.

    Use case:
        m = MotorsportAuctions(page)
        await m.open()            # open homepage
        items = await m.collect() # collect ads and save to Excel
    """

    def __init__(self, page):
        self.page = page
        # Debug: indicate the page object was received
        print(f"[MotorsportAuctions] Initialized with page={page}")

    homeLink = "https://www.motorsportauctions.com/"

    async def open(self):
        """Navigate to the homepage and wait for DOM/network settle.

        Use case: call this at the start before any interactions to ensure
        the page is loaded. `wait_network` is attempted but tolerant of
        failures (ads/analytics may keep network busy indefinitely).
        """

        # Debug: starting navigation to homeLink
        print(f"[MotorsportAuctions] open() -> navigating to {self.homeLink}")
        await self.page.goto(self.homeLink)
        # Wait until basic DOM is loaded before performing further actions
        await wait_dom(self.page)
        try:
            # Wait for network idle where possible; tolerate timeouts
            await wait_network(self.page)
        except Exception as e:
            # Some sites (ads, analytics) may never reach networkidle; log and continue
            print(f"Warning: wait_network failed or timed out: {e}")

    async def collapse_expand_Advertisements(self, adtype: str = "", action: str = "collapse"):
        """Collapse or expand a chosen ad panel.

        Args:
            adtype: one of "recent" or "featured" to select the panel.
            action: "collapse" to ensure the panel is closed, "expand" to
                    ensure it is open. Defaults to "collapse".

        The method toggles the panel header until the requested state
        (visible or not visible) is reached, with a retry limit.
        """

        # Debug: show requested panel and action
        print(f"[MotorsportAuctions] collapse_expand_Advertisements(adtype={adtype}, action={action})")
        typeHeading: Optional[Locator] = None
        inner: Optional[Locator] = None

        adtype = (adtype or "").lower()
        action = (action or "collapse").lower()

        if adtype == "recent":
            typeHeading = self.page.locator("//div[contains(@id,'option01')]//h2")
            inner = self.page.locator("div#option01 div.content-block-inner")
        elif adtype == "featured":
            typeHeading = self.page.locator("//div[contains(@id,'option02')]//h2")
            inner = self.page.locator("div#option02 div.content-block-inner")

        if typeHeading is None or inner is None:
            print(f"Warning: unknown adtype '{adtype}'")
            return

        max_attempts = 6
        attempts = 0

        # If action is collapse -> wait until inner is NOT visible
        if action == "collapse":
            while await is_visible(inner) and attempts < max_attempts:
                await safe_click(typeHeading)
                await self.page.wait_for_timeout(1000)
                attempts += 1

        # If action is expand -> wait until inner IS visible
        elif action == "expand":
            while not await is_visible(inner) and attempts < max_attempts:
                await safe_click(typeHeading)
                await self.page.wait_for_timeout(1000)
                attempts += 1

        heading_text = await safe_text(typeHeading)
        visible_now = await is_visible(inner)
        if action == "collapse" and not visible_now:
            print(f"{heading_text} collapsed")
        elif action == "expand" and visible_now:
            print(f"{heading_text} expanded")
        else:
            print(f"Warning: {heading_text} did not reach requested state '{action}' after {attempts} attempts")

        await self.page.wait_for_timeout(1000)

    async def extract_ad_data(self, adsList, adCount, items):
        # Debug: starting ad extraction loop
        print(f"[MotorsportAuctions] extract_ad_data() - processing {adCount} ads")
        for i in range(adCount):
            ad = adsList.nth(i)
            ad_data = {}
            # Ensure ad is in viewport before extracting data
            await scroll_into_view(ad)
            # Debug: processing one ad index
            print(f"[MotorsportAuctions] extract_ad_data - processing ad {i+1}/{adCount}")
            
            # Title: try common title attribute first, otherwise fallback to visible text
            title = ad.locator("span").first
            val = await title.get_attribute("title")
            if not val:
                title = ad.locator("span.ad-title").first
                val = await safe_text(title)
            ad_data["title"] = val

            # Price: extract using safe_text (handles empty/missing nodes)
            price = ad.locator("div.advert-price").first
            val = await safe_text(price)
            ad_data["price"] = val

            # Date: human readable posted/auction date
            date = ad.locator("span.advert-date").first
            val = await safe_text(date)
            ad_data["date"] = val

            # Image URL: prefer lazy-loaded attributes then fallback to src
            img = ad.locator("img").first
            try:
                val = await img.get_attribute("nitro-lazy-src")
            except Exception:
                val = None
            if not val:
                val = await img.get_attribute("data-src") or await img.get_attribute("src") or ""
            ad_data["imageURL"] = val

            # Link: direct ad link
            link = ad.locator("a").first
            val = await link.get_attribute("href")
            ad_data["linkURL"] = val

            items.append(ad_data)
        return items

    async def load_all_ads(self, ad_type: str):
        """Click 'Load More' buttons until all ads are loaded.

        Use case: repeatedly click 'Load More' buttons on the page
        until no more are present, waiting for network idle after
        each click to ensure new content is loaded.
        """

        # Debug: begin loading 'Load More' buttons loop for ad_type
        print(f"[MotorsportAuctions] load_all_ads(ad_type={ad_type})")
        loadMore = "(//button[contains(., 'Load More')])"
        c=0
        while True:
        # while c < 2:  # limit to 3 clicks to avoid infinite loops
            c+=1
            loadMoreCount = await self.page.locator(loadMore).count()
            print(f"[MotorsportAuctions] Found {loadMoreCount} 'Load More' buttons")
            if loadMoreCount > 1:
                if ad_type == "recent":
                    await safe_click(self.page.locator(loadMore).first)
                    print("Clicking first 'Load More' (more than 1 present)")
                    
                elif ad_type == "featured":
                    await safe_click(self.page.locator(loadMore).nth(1))
                    print("Clicking second 'Load More' (more than 1 present)")
                try:
                    await wait_network(self.page)
                except Exception:
                    # tolerant: continue even if network idle isn't reached
                    pass
                # small pause to allow UI update before re-checking
                await self.page.wait_for_timeout(500)
                continue
            break

    async def collect(self):
        """Collect advertisement listings from the current page.

        Workflow / Use case:
            1. Optionally collapse or expand ad sections to reduce noise.
            2. Locate all ad containers and extract title, price, date,
               image URL and link for each listing.
            3. Save results to an Excel file with basic metadata.

        Returns:
            List[Dict]: list of ad metadata dictionaries.
        """

        # Debug: collect started
        print("[MotorsportAuctions] collect() - start")
        # Small initial pause to ensure any last rendering completes
        await self.page.wait_for_timeout(1000)

        # Collapse the featured advertisement section header (if present) to get stable layout
        await self.collapse_expand_Advertisements("featured")

        items = []

        # Ensure all ads are loaded by clicking 'Load More' buttons
        await self.load_all_ads("recent")
        
        # All Recent adverts containers match id pattern 'advert_id_'
        adsList = self.page.locator("//div[contains(@id,'advert_id_')]")
        adCount = await adsList.count()
        print(f"[MotorsportAuctions] Found {adCount} ads")

        items = await self.extract_ad_data(adsList, adCount, items)
        
        print(f"[MotorsportAuctions] Collected Recent Adverts {len(items)} ads")
        
        # Collapse the recent advertisement section header (if present) to get stable layout
        await self.collapse_expand_Advertisements("recent")

        # Expand the featured advertisement section header (if present) to get stable layout
        await self.collapse_expand_Advertisements("featured", action="expand")
        
        # Ensure all ads are loaded by clicking 'Load More' buttons
        await self.load_all_ads("featured")
        
        # All Featured adverts containers match id pattern 'featured_id_'
        adsList = self.page.locator("//div[contains(@id,'featured_id_')]")
        adCount = await adsList.count()
        print(f"[MotorsportAuctions] Found {adCount} featured ads")

        items.extend(await self.extract_ad_data(adsList, adCount, items))
        print(f"[MotorsportAuctions] Collected Featured Adverts, total {len(items)} ads")
        
        # Small initial pause to ensure any last rendering completes
        await self.page.wait_for_timeout(10000)
        
        # Metadata describing the collection
        meta = {"source": self.homeLink, "records": len(items)}

        # Persist results to Excel; `as_excel` will create a metadata sheet
        print(f"[MotorsportAuctions] Saving {len(items)} records to motorsport_auctions.xlsx")
        as_excel(items, meta=meta, file_path="motorsport_auctions.xlsx")

        return items
