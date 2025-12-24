import asyncio
from screeninfo import get_monitors

from Utilities.browser_async import get_page
from Pages.Motorsportauctions import MotorsportAuctions
from Pages.Rallycarsforsale import RallyCarsForSale



SITES = {
    "motorsport": MotorsportAuctions,
    "rally": RallyCarsForSale,
}


async def run(site_key):
    pw, browser, context, page = await get_page(
        headless=False,
    )

    try:
        site = SITES[site_key](page)

        await site.open()
        data = await site.collect()
        

        # print(f"\nCollected {len(data)} items from {site_key}")
        # for d in data[:3]:
        #     print(d)

    finally:
        await context.close()
        await browser.close()
        await pw.stop()


async def main():
    # Run ONE site
    # await run("motorsport")
    await run("rally")


if __name__ == "__main__":
    asyncio.run(main())
