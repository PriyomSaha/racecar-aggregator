import re
import time

from Utilities.actions_async import safe_click, safe_text
from Utilities.waits_async import wait_dom, wait_network
from Utilities.scroll_async import scroll_into_view
from Utilities.state_async import is_visible


class RallyCarsForSale:
    def __init__(self, page):
        self.page = page

    # ---------------- OPEN ---------------- #

    async def open(self):
        await self.page.goto(
            "https://rallycarsforsale.net/?s=&sa=search&scat=0"
        )
        await wait_dom(self.page)
        await wait_network(self.page)
        await self.accept_cookies_if_present()

    # ---------------- COOKIES ---------------- #

    async def accept_cookies_if_present(self):
        try:
            btn = self.page.get_by_role("button", name="Accept All").first
            if await btn.is_visible(timeout=3000):
                await btn.click()
                await self.page.wait_for_timeout(500)
        except Exception:
            pass

    # ---------------- PAGE INDICATOR ---------------- #

    async def wait_for_page_number(self, expected_page: int, timeout: int = 7000) -> bool:
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

    # ---------------- PAGINATION ---------------- #

    async def move_to_next_page(self, current_page: int) -> bool:
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

    # ---------------- COLLECT ---------------- #

    async def collect(self):
        items = []

        # get last page number safely
        last_page_locator = self.page.locator(
            "(//a[contains(@class,'page-numbers')][not(contains(@class,'next'))])[last()]"
        )
        pages_count = int(await last_page_locator.text_content())

        current_page = 1

        while current_page <= pages_count:
            await self.accept_cookies_if_present()

            ad_blocks = self.page.locator("//div[contains(@class,'post-block')]")
            count = await ad_blocks.count()

            print(f"Collecting page {current_page} with {count} ads")

            # -------- SCRAPE ADS HERE -------- #
            # for i in range(count):
            #     block = ad_blocks.nth(i)
            #     ...
            # -------------------------------- #

            if current_page == pages_count:
                break

            moved = await self.move_to_next_page(current_page)
            if not moved:
                print(f"⚠️ Failed to move from page {current_page}")
                break

            current_page += 1

        return items
