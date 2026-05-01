import asyncio
from screeninfo import get_monitors
from Utilities import db_utils

from Pages.Racecarsforyou import RaceCarsForYou
from Utilities.browser_async import get_page
from Pages.Motorsportauctions import MotorsportAuctions
from Pages.Rallycarsforsale import RallyCarsForSale



SITES = {
    "motorsport": MotorsportAuctions,
    "rally": RallyCarsForSale,
    "racecars": RaceCarsForYou,
}


async def run(site_key):
    pw, browser, context, page = await get_page(
        headless=False,
    )

    try:
        site = SITES[site_key](page)

        await site.open()
        data = await site.collect_test()
        # data = await site.collect()
        
        
        for item in data:
            db_utils.upsert_product(item)
        

        # print(f"\nCollected {len(data)} items from {site_key}")
        # for d in data[:3]:
        #     print(d)

    finally:
        await context.close()
        await browser.close()
        await pw.stop()


async def main():
    db_utils.create_table()
    # Run ONE site
    await run("motorsport")
    # await run("rally")
    # await run("racecars")


if __name__ == "__main__":
    asyncio.run(main())
