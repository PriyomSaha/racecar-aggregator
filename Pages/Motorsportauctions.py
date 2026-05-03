"""Pages.Motorsportauctions

Helpers for scraping MotorsportAuctions site using Playwright page API.

This module provides `MotorsportAuctions` which encapsulates navigation
and data-collection logic for motorsportauctions.com. Methods are written
as async coroutines and rely on utility helpers in `Utilities`.
"""

from os import link

from Utilities import db_utils
from Utilities.actions_async import safe_click, safe_text
from Utilities.output import as_excel,deleteoldfile
from Utilities.scroll_async import scroll_into_view
from Utilities.waits_async import wait_dom, wait_network, wait_for
from Utilities.state_async import is_visible
from Utilities.id_utils import generate_id
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

    homeLink = "https://www.motorsportauctions.com/"
    OUTPUT_FILE_NAME = "motorsport_auctions.xlsx"

    async def open(self):
        """Navigate to the homepage and wait for DOM/network settle.

        Use case: call this at the start before any interactions to ensure
        the page is loaded. `wait_network` is attempted but tolerant of
        failures (ads/analytics may keep network busy indefinitely).
        """

        # Debug: starting navigation to homeLink
        await self.page.goto(self.homeLink, timeout=120000, wait_until="domcontentloaded")
        # Wait until basic DOM is loaded before performing further actions
        await wait_dom(self.page,999999)
        try:
            # Wait for network idle where possible; tolerate timeouts
            await wait_network(self.page)
        except Exception as e:
            # Some sites (ads, analytics) may never reach networkidle; log and continue
            print(f"Warning: network idle not reached during open(): {e}")

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
            pass
        elif action == "expand" and visible_now:
            pass
        else:
            print(f"Warning: {heading_text} did not reach requested state '{action}' after {attempts} attempts")

        await self.page.wait_for_timeout(1000)

    async def extract_ad_data(self, adsList, adCount, items, category=None):
        for i in range(adCount):
            ad = adsList.nth(i)
            ad_data = {}
            # Ensure ad is in viewport before extracting data
            await scroll_into_view(ad)
            
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
            imgs = ad.locator("img")
            count = await imgs.count()
    
            ad_data["imageURLs"] = await self.get_all_image_urls(imgs, count)
            
            # Link: direct ad link
            link = ad.locator("a").first
            val = await link.get_attribute("href")
            ad_data["linkURL"] = val
            
            # Create unique ID for the ad based on its link
            ad_data["id"] = generate_id("MSA_", val)
            
            # Add category if provided
            if category:
                ad_data["category"] = [category] if category else []
            
            items.append(ad_data)
        return items

    async def get_all_image_urls(self, imgs , count):
        image_urls = []

        for i in range(count):
            img = imgs.nth(i)

            val = await img.get_attribute("nitro-lazy-src")
            if not val:
                val = await img.get_attribute("data-src")
            if not val:
                val = await img.get_attribute("src")

            if val:
                image_urls.append(val)
                
        
        return sorted(list(set(image_urls)))

    async def load_all_ads(self, ad_type: str):
        """Click 'Load More' buttons until all ads are loaded.

        Use case: repeatedly click 'Load More' buttons on the page
        until no more are present, waiting for network idle after
        each click to ensure new content is loaded.
        """

        loadMore = "(//button[contains(., 'Load More')])"
        c=0
        while True:
        # while c < 2:  # limit to 3 clicks to avoid infinite loops
            c+=1
            loadMoreCount = await self.page.locator(loadMore).count()
            if loadMoreCount > 1:
                if ad_type == "recent":
                    await safe_click(self.page.locator(loadMore).first)
                    
                elif ad_type == "featured":
                    await safe_click(self.page.locator(loadMore).nth(1))
                try:
                    await wait_network(self.page)
                except Exception:
                    # tolerant: continue even if network idle isn't reached
                    pass
                # small pause to allow UI update before re-checking
                await self.page.wait_for_timeout(500)
                continue
            break

    async def gather_detailed_data(self, items):
        """Gather detailed data for each advertisement in the list.

        Use case: for each ad in the list, navigate to its detail page and
        extract additional information (e.g., description, seller info).
        """
        for idx, item in enumerate(items, start=1):
            link = item.get("linkURL")
            if not link:
                continue
            
            # await wait_for(2000)  # small pause before navigation
            await self.page.goto(link, timeout=120000, wait_until="domcontentloaded")
            await wait_dom(self.page,100000)
            
            # Check for the error message indicating the ad page is not found; if present, skip detailed extraction
            if await self.page.locator("text=Oops! That page can’t be found.").count() > 0:
                item["detailedDescription"] = None
                item["location"] = None
                item["contactInfo"] = None
                item["imageURLs"] = []
                continue

            # extract description
            description_locator = self.page.locator("div.adverts-content")

            # Extract full visible text in DOM order
            description = await description_locator.inner_text()

            # Normalize Windows line endings
            description = description.replace("\r\n", "\n")

            # Remove excessive trailing spaces but KEEP blank lines
            description = "\n".join(line.rstrip() for line in description.split("\n"))

            description = description.strip()

            item["detailedDescription"] = description

            location_locator = self.page.locator(
                "(//span[contains(text(),'Location')]//following::div)[1]"
            )

            if await location_locator.count() > 0:
                location = await safe_text(location_locator)
                item["location"] = location
            else:
                item["location"] = None

            try:
                # Contact Info Locator
                contact_locator = self.page.locator("(//span[contains(text(),'Phone')]//following::div)[1]")
                contact_info = await safe_text(contact_locator)
                item["contactInfo"] = contact_info
            except Exception:
                item["contactInfo"] = None
            
            # Extract additional image URLs if available
            try:
                images_locators = self.page.locator(
                "//li[contains(@class,'wpadverts')]"
            )              
                imgs = images_locators.locator("img")
                count = await imgs.count()      
                if count > 0:
                    item["imageURLs"] = await self.get_all_image_urls(imgs, count)
            except Exception as e:
                print(f"Error extracting image URLs for item #{idx}: {e}")
            
            # Ensure imageURLs is always a list
            if "imageURLs" not in item:
                item["imageURLs"] = []

    async def collect_categorized_data(self, category):
        items =[]
        
         # Nested helper function to build category-based links
        def build_category_link(category):
            """Build a link based on the category value.
            
            Args:
                category: The category value (e.g., 'recent', 'featured', 'esports')
                
            Returns:
                str: The constructed link or None if category is unknown
            """
            
            if category == "esports":
                return self.homeLink + "category/20/esports.html"
            elif category == "race-cars":
                return self.homeLink + "/category/61/race-cars.html"
            elif category == "rally-cars":
                return self.homeLink + "/category/66/rally-cars.html" 
            elif category == "sports-cars":
                return self.homeLink + "category/75/sports-cars.html"           
            elif category == "performance-road-cars":
                return self.homeLink + "category/60/performance-road-cars.html"
            elif category == "touring-cars":
                return self.homeLink + "category/79/touring-cars.html"
            elif category == "historic-road-cars":
                return self.homeLink + "category/23/historic-road-cars.html"
            elif category == "transporters-and-support-vehicles":
                return self.homeLink + "category/87/transporters-and-support-vehicles.html"
            elif category == "other-items":
                return self.homeLink + "category/24/other-items.html"            
            else:
                return None
        
        category_link = build_category_link(category)
        if not category_link:
            print(f"Unknown category '{category}'. Skipping.")
            return items
        
        await self.page.goto(category_link, timeout=120000, wait_until="domcontentloaded")
        await wait_dom(self.page)
        
        adsList = self.page.locator("//div[contains(@class,'middle-content')]//div[contains(@class,'advert-item-col')]")
        
        # Check if ads exist on this page
        try:
            adCount = await adsList.count()
            if adCount == 0:
                print(f"No ads found for category '{category}'")
                return items
            
            # Check if first ad is visible (strict mode issue with multiple elements)
            if await is_visible(adsList.first):              
                # Page 1 (already loaded)
                await self.extract_ad_data(adsList, adCount, items, category=category)
                # Pagination loop (2, 3, 4...)
                page = 2
                while True:
                    next_page = self.page.locator(f"//a[@class='page-numbers' and text()='{page}']")

                    if await next_page.count() == 0:
                        break

                    await next_page.click()
                    await wait_dom(self.page)
                    await wait_network(self.page)

                    # re-evaluate ads after page change
                    adCount = await adsList.count()

                    await self.extract_ad_data(adsList, adCount, items, category=category)
                    page += 1
                
                await self.gather_detailed_data(items)

            else:
                print(f"Ads found for category '{category}' but not visible")
        except Exception as e:
            print(f"Error processing category '{category}': {e}")
        
        return items
           
    async def collect_test(self):
        items = []
        
        # await self.collapse_expand_Advertisements("featured")
        
        # adsList = self.page.locator("//div[contains(@id,'advert_id_')]")
        # adCount = await adsList.count()

        # items = await self.extract_ad_data(adsList, adCount, items, category="recent")

        # await self.gather_detailed_data(items)
        
        # items.extend(await self.collect_categorized_data([], category="esports"))
        
        # items.extend(await self.collect_categorized_data([], category="race-cars"))
        
        # items.extend(await self.collect_categorized_data([], category="rally-cars"))
        
        # items.extend(await self.collect_categorized_data([], category="sports-cars"))
        
        # items.extend(await self.collect_categorized_data([], category="touring-cars"))
        # items.extend(await self.collect_categorized_data([], category="performance-road-cars"))
        # items.extend(await self.collect_categorized_data([], category="historic-road-cars"))
        items.extend(await self.collect_categorized_data(category="transporters-and-support-vehicles"))
        # items.extend(await self.collect_categorized_data([], category="other-items"))
        
        
        
        
        
        # Metadata describing the collection
        meta = {"source": self.homeLink, "records": len(items)}

        # Persist results to Excel; `as_excel` will create a metadata sheet
        as_excel(items, meta=meta, file_path="motorsport_auctions.xlsx")

        return items
    
    async def collect_featured_and_recent_ads(self):
        
        """Collect advertisement listings from the current page.

        Workflow / Use case:
            1. Optionally collapse or expand ad sections to reduce noise.
            2. Locate all ad containers and extract title, price, date,
               image URL and link for each listing.
            3. Save results to an Excel file with basic metadata.

        Returns:
            List[Dict]: list of ad metadata dictionaries.
        """

        homeAnchor = self.page.locator("//a[normalize-space()='Home']")
        await safe_click(homeAnchor)
        
        items = []
        # Small initial pause to ensure any last rendering completes
        await self.page.wait_for_timeout(1000)

        # Collapse the featured advertisement section header (if present) to get stable layout
        await self.collapse_expand_Advertisements("featured")


        # Ensure all ads are loaded by clicking 'Load More' buttons
        await self.load_all_ads("recent")
        
        # All Recent adverts containers match id pattern 'advert_id_'
        adsList = self.page.locator("//div[contains(@id,'advert_id_')]")
        adCount = await adsList.count()

        items = await self.extract_ad_data(adsList, adCount, items, category="recent")
        
        # Collapse the recent advertisement section header (if present) to get stable layout
        await self.collapse_expand_Advertisements("recent")

        # Expand the featured advertisement section header (if present) to get stable layout
        await self.collapse_expand_Advertisements("featured", action="expand")
        
        # Ensure all ads are loaded by clicking 'Load More' buttons
        await self.load_all_ads("featured")
        
        # All Featured adverts containers match id pattern 'featured_id_'
        adsList = self.page.locator("//div[contains(@id,'featured_id_')]")
        adCount = await adsList.count()

        items.extend(await self.extract_ad_data(adsList, adCount, [], category="featured"))
        
        # Small initial pause to ensure any last rendering completes
        await self.page.wait_for_timeout(10000)
        
        await self.gather_detailed_data(items)
        
        # Metadata describing the collection
        meta = {"source": self.homeLink, "records": len(items)}

        # Persist results to Excel; `as_excel` will create a metadata sheet
        as_excel(items, meta=meta, file_path="motorsport_auctions.xlsx")

        return items

    async def store_in_db_excel(self, items,category):
        for item in items:
            db_utils.upsert_product(item)
            
        # Metadata describing the collection
        meta = {"source": self.homeLink,"category": category, "records": len(items)}
        # Persist results to Excel; `as_excel` will create a metadata sheet
        as_excel(items, meta=meta, file_path=self.OUTPUT_FILE_NAME)
    
    async def collect(self):
        """Main method to collect advertisement listings from the current page.

        This is the primary method to call for data collection. It orchestrates
        the entire workflow of collapsing/expanding sections, loading all ads,
        extracting data, and saving results.

        Returns:
            List[Dict]: list of ad metadata dictionaries.
        """
        # categories = ["esports","sports-cars", "race-cars", "rally-cars",  "touring-cars", "historic-road-cars", "performance-road-cars", "transporters-and-support-vehicles", "other-items"]
        
        # deleteoldfile(self.OUTPUT_FILE_NAME)
        
        categories = ["historic-road-cars", "performance-road-cars", "transporters-and-support-vehicles", "other-items"]
        
        for cat in categories:
            items = []
            items.extend(await self.collect_categorized_data(cat))
            await self.store_in_db_excel(items,cat)
        
        # items.extend(await self.collect_featured_and_recent_ads())
        