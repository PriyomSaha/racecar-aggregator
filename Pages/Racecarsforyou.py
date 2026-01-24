from datetime import datetime, timedelta
import re
import time

from Utilities.actions_async import safe_click, safe_text
from Utilities.output import as_excel
from Utilities.waits_async import wait_dom, wait_network
from Utilities.scroll_async import scroll_into_view
from Utilities.state_async import get_attr_async, is_visible


class RaceCarsForYou:
    def __init__(self, page):
        self.page = page
        # Debug: indicate instance creation
        print(f"[RaceCarsForYou] Initialized with page={page}")
    
    homeLink = "https://racecarsforyou.com/"
    
    # ---------------- OPEN ---------------- #

    async def open(self):
        # Debug: opening listing page
        print(f"[RaceCarsForYou] open() -> navigating to {self.homeLink}")
        await self.page.goto(
            f"{self.homeLink}/search-for-race-cars/?_listing_type=race-car%2Crace-car-parts%2Crace-car-pit-equipment-tools%2Crace-trailers%2Ctransporters-trucks-toters&_sorter=date&_currency=undefined&_per_page=50"
        )
        await wait_dom(self.page)

    # ---------------- PAGINATION ---------------- #

    async def move_to_next_page(self, current_page: int, count: int) -> bool:
        print(f"[RaceCarsForYou] move_to_next_page(current_page={current_page})")
        next_button = self.page.locator(
            "(//a[contains(@class,'facetwp-page next')])[1]"
        )

        if not await is_visible(next_button):
            return False

        await scroll_into_view(next_button)
        await self.page.wait_for_timeout(500)
        await safe_click(next_button)

        return await self.wait_for_page_number(current_page + 1)


    # ---------------- PAGE INDICATOR ---------------- #

    async def wait_for_page_number(self, expected_page: int, timeout: int = 30000) -> bool:
        # Wait until the page indicator shows the expected page number
        print(f"[RaceCarsForYou] wait_for_page_number(expected_page={expected_page})")
        # Locator for the pagination link/button that corresponds to the expected page
        page_link = self.page.locator(f"//a[contains(@class,'facetwp-page') and text()='{expected_page}']")
        end_time = time.time() + timeout / 1000
        loader = self.page.locator("//div[@class='loading-icon loading']")
 
        while time.time() < end_time or await is_visible(loader):
            try:
                # New check: pagination control has become active (class or aria-current)
                if await page_link.count() > 0:
                    cls = await get_attr_async(page_link.first, 'class') or ""
                    dataPage = await get_attr_async(page_link.first, 'data-page') or ""
                    if 'active' in cls.split() and dataPage == str(expected_page):
                        return True
            except Exception as e:
                # ignore per-iteration errors and retry until timeout
                print(f"[RaceCarsForYou] wait_for_page_number - error: {e}")                
                pass
            
            await self.page.wait_for_timeout(5000)
            await wait_dom(self.page)

        return False

    # ---------------- EXTRACT DATA ---------------- #
    
    async def extract_ad_data(self, adsList, adCount, items):
        print(f"[RaceCarsForYou] extract_ad_data() - processing {adCount} ads")
        for i in range(adCount):
            ad = adsList.nth(i)
            ad_data = {}
            # Ensure ad is in viewport before extracting data
            await scroll_into_view(ad)
            print(f"[RaceCarsForYou] extract_ad_data - processing ad {i+1}/{adCount}")
            
            # Title
            title = ad.locator("xpath=.//h2[contains(@class,'entry-title')]//a").first
            val = await safe_text(title)
            ad_data["title"] = val
            
            # Price: handle 'sold' case
            price_container = ad.locator("xpath=.//div[contains(@class,'grid_listing_price')]")
            val = "sold"

            try:
                if await price_container.count() > 0:
                    container = price_container.first

                    # Try to get non-striked (sale) price
                    sale_price = container.locator(".//span[contains(@class,'sale_price')]")

                    if await sale_price.count() > 0:
                        val = (await sale_price.first.inner_text()).strip()
                    else:
                        # Fallback: single price case
                        text = (await container.inner_text()).strip()
                        if text:
                            val = text

            except Exception:
                val = "sold"

            ad_data["price"] = val

            # Image URL: prefer lazy-loaded attributes then fallback to src
            img = ad.locator("img").first
            val = await img.get_attribute("src") or ""
            ad_data["imageURL"] = val

            # Link: direct ad link
            link = ad.locator("xpath=.//h2[contains(@class,'entry-title')]//a").first
            val = await link.get_attribute("href")
            ad_data["linkURL"] = val

            items.append(ad_data)
        return items
    
    # ---------------- COLLECT ---------------- #

    async def collect(self):
        items = []

        # get last page number safely
        last_page_locator = self.page.locator(
            "//a[contains(@class,'facetwp-page last')]"
        ).first
        pages_count = int(await last_page_locator.text_content())

        current_page = 1
        
        items = []

        while current_page <= pages_count:
            
            ad_blocks = self.page.locator("//div[contains(@class,'grid_listing listing-')]")
            count = await ad_blocks.count()

            print(f"[RaceCarsForYou] Collecting page {current_page} with {count} ads")

            await self.extract_ad_data(ad_blocks, count, items)

            if current_page == pages_count:
                break

            moved = await self.move_to_next_page(current_page,count)
            if not moved:
                print(f"⚠️ Failed to move from page {current_page}")
                break

            current_page += 1

        # print(f"[RaceCarsForYou] Collected Featured Adverts, total {len(items)} ads")
        
        # Small initial pause to ensure any last rendering completes
        await self.page.wait_for_timeout(1000)
        
        # Metadata describing the collection
        meta = {"source": self.homeLink, "records": len(items)}

        # Persist results to Excel; `as_excel` will create a metadata sheet
        print(f"[Racecars] Saving {len(items)} records to rallycars.xlsx")
        as_excel(items, meta=meta, file_path="racecars.xlsx")
        return items


# 