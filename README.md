# racecar-aggregator
A backend data aggregator that collects competition car listings from selected motorsport websites and exposes them through a unified API and stores data in an Excel file.

## Install dependencies

Run these commands from the project root:

```bash
pip install playwright pandas screeninfo openpyxl
playwright install
```

## Notes

- `playwright` is used for browser automation.
- `pandas` is used to generate Excel output.
- `screeninfo` is used to detect monitor size when launching the browser.
- `openpyxl` is needed for `pandas` to write `.xlsx` files.
