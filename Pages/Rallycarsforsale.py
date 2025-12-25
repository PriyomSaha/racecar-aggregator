from datetime import datetime, timedelta
import re
import time

from Utilities.actions_async import safe_click, safe_text
from Utilities.output import as_excel
from Utilities.waits_async import wait_dom, wait_network
from Utilities.scroll_async import scroll_into_view
from Utilities.state_async import is_visible


class RallyCarsForSale:
    def __init__(self, page):
        self.page = page
        # Debug: indicate instance creation
        print(f"[RallyCarsForSale] Initialized with page={page}")
    homeLink = "https://rallycarsforsale.net/"

    # ---------------- OPEN ---------------- #

    async def open(self):
        # Debug: opening listing page
        print(f"[RallyCarsForSale] open() -> navigating to {self.homeLink}")
        await self.page.goto(
            f"{self.homeLink}?s=&sa=search&scat=0"
        )
        await wait_dom(self.page)
        await wait_network(self.page)
        await self.accept_cookies_if_present()

    # ---------------- COOKIES ---------------- #

    async def accept_cookies_if_present(self):
        # Try to accept cookie banner if present to avoid obstructions
        print("[RallyCarsForSale] accept_cookies_if_present()")
        try:
            btn = self.page.get_by_role("button", name="Accept All").first
            if await btn.is_visible(timeout=3000):
                await btn.click()
                await self.page.wait_for_timeout(500)
        except Exception:
            # ignore if not present or other errors
            pass

    # ---------------- PAGE INDICATOR ---------------- #

    async def wait_for_page_number(self, expected_page: int, timeout: int = 7000) -> bool:
        # Wait until the page indicator shows the expected page number
        print(f"[RallyCarsForSale] wait_for_page_number(expected_page={expected_page})")
        indicator = self.page.locator("//span[@class='total']")
        end_time = time.time() + timeout / 1000

        while time.time() < end_time:
            try:
                txt = (await indicator.text_content()) or ""
                if re.search(rf"Page\s*{expected_page}\b", txt):
                    return True
            except Exception:
                pass

            await self.page.wait_for_timeout(250)

        return False

    async def parse_relative_date(self, text: str) -> str:
        """Convert relative time strings (e.g. '14 uur ago' or 'December 20 , 2025')

        Returns a formatted date like '22 December 2025' when possible, otherwise
        returns the original text.
        """
        # Debug: show raw input to the parser
        print(f"[RallyCarsForSale] parse_relative_date input: {text}")
        if not text:
            return ""

        s = text.strip()
        # normalize spacing and remove extra commas and 'ago'
        s_clean = re.sub(r"\s+", " ", s.replace(',', '')).strip().lower()
        s_proc = s_clean.replace('ago', '').strip()

        now = datetime.now()

        # relative: hours
        m = re.match(r"^(\d+)\s*(uur|u|hours?|hrs?|h)\b", s_proc)
        if m:
            dt = now - timedelta(hours=int(m.group(1)))
            return dt.strftime("%d %B %Y")

        # minutes
        m = re.match(r"^(\d+)\s*(min|mins|minuten|minutes?)\b", s_proc)
        if m:
            dt = now - timedelta(minutes=int(m.group(1)))
            return dt.strftime("%d %B %Y")

        # days
        m = re.match(r"^(\d+)\s*(dag|dagen|d|day|days)\b", s_proc)
        if m:
            dt = now - timedelta(days=int(m.group(1)))
            return dt.strftime("%d %B %Y")

        # weeks
        m = re.match(r"^(\d+)\s*(week|weeks|w)\b", s_proc)
        if m:
            dt = now - timedelta(weeks=int(m.group(1)))
            return dt.strftime("%d %B %Y")

        # months / years (approximate)
        m = re.match(r"^(\d+)\s*(month|months|maand|maanden)\b", s_proc)
        if m:
            dt = now - timedelta(days=30 * int(m.group(1)))
            return dt.strftime("%d %B %Y")

        m = re.match(r"^(\d+)\s*(year|years|jaar)\b", s_proc)
        if m:
            dt = now - timedelta(days=365 * int(m.group(1)))
            return dt.strftime("%d %B %Y")

        # Try parsing common explicit date formats after removing commas
        s_try = re.sub(r",", "", s).strip()
        formats = [
            "%B %d %Y",
            "%b %d %Y",
            "%d %B %Y",
            "%d %b %Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(s_try, fmt)
                return dt.strftime("%d %B %Y")
            except Exception:
                pass

        # fallback
        return text


    # ---------------- PAGINATION ---------------- #

    async def move_to_next_page(self, current_page: int) -> bool:
        print(f"[RallyCarsForSale] move_to_next_page(current_page={current_page})")
        next_button = (
            self.page.locator(
                "//a[contains(@class,'page-numbers') and not(contains(@class,'current'))]"
            )
            .filter(has_text=str(current_page + 1))
            .first
        )

        if not await is_visible(next_button):
            return False

        await scroll_into_view(next_button)
        await self.page.wait_for_timeout(500)
        await safe_click(next_button)

        return await self.wait_for_page_number(current_page + 1)

    # ---------------- EXTRACT DATA ---------------- #
    
    async def extract_ad_data(self, adsList, adCount, items):
        print(f"[RallyCarsForSale] extract_ad_data() - processing {adCount} ads")
        for i in range(adCount):
            ad = adsList.nth(i)
            ad_data = {}
            # Ensure ad is in viewport before extracting data
            await scroll_into_view(ad)
            print(f"[RallyCarsForSale] extract_ad_data - processing ad {i+1}/{adCount}")
            
            # Title
            title = ad.locator("xpath=.//h3//a").first
            val = await safe_text(title)
            ad_data["title"] = val
            
            # Price: extract using safe_text (handles empty/missing nodes)
            # Use XPath relative selector to avoid CSS vs XPath ambiguity
            price_locator = ad.locator("xpath=.//p[contains(@class,'post-price')]")
            val = "sold"
            try:
                count = await price_locator.count()
                if count > 0:
                    # prefer using safe_text on the locator so it handles
                    # missing/empty nodes consistently; normalize empty -> 'sold'
                    text = await safe_text(price_locator.first)
                    if text and isinstance(text, str) and text.strip():
                        val = text.strip()
                    else:
                        val = "sold"
                else:
                    val = "sold"
            except Exception:
                # any unexpected error -> mark as sold to keep behavior safe
                val = "sold"
            ad_data["price"] = val

            # Date: human readable posted/auction date
            date = ad.locator("xpath=.//span[@class ='dashicons-before clock']//span").first
            val = await self.parse_relative_date(await safe_text(date))
            ad_data["date"] = val

            # Image URL: prefer lazy-loaded attributes then fallback to src
            img = ad.locator("img").first
            val = await img.get_attribute("src") or ""
            ad_data["imageURL"] = val

            # Link: direct ad link
            link = ad.locator("a").first
            val = await link.get_attribute("href")
            ad_data["linkURL"] = val

            items.append(ad_data)
        return items
    
    # ---------------- COLLECT ---------------- #

    async def collect(self):
        print("[RallyCarsForSale] collect() - start")
        items = []

        # get last page number safely
        last_page_locator = self.page.locator(
            "(//a[contains(@class,'page-numbers')][not(contains(@class,'next'))])[last()]"
        )
        pages_count = int(await last_page_locator.text_content())

        current_page = 1
        
        items = []

        while current_page <= pages_count:
            await self.accept_cookies_if_present()

            ad_blocks = self.page.locator("//div[contains(@class,'post-block-out')]")
            count = await ad_blocks.count()

            print(f"[RallyCarsForSale] Collecting page {current_page} with {count} ads")

            await self.extract_ad_data(ad_blocks, count, items)

            if current_page == pages_count:
                break

            moved = await self.move_to_next_page(current_page)
            if not moved:
                print(f"⚠️ Failed to move from page {current_page}")
                break

            current_page += 1

        print(f"[RallyCarsForSale] Collected Featured Adverts, total {len(items)} ads")
        
        # Small initial pause to ensure any last rendering completes
        await self.page.wait_for_timeout(10000)
        
        # Metadata describing the collection
        meta = {"source": self.homeLink, "records": len(items)}

        # Persist results to Excel; `as_excel` will create a metadata sheet
        print(f"[RallyCarsForSale] Saving {len(items)} records to rallycars.xlsx")
        as_excel(items, meta=meta, file_path="rallycars.xlsx")
        return items
