# racecar-aggregator

A web scraper and data aggregator that collects competition car listings from motorsport websites and stores them in a PostgreSQL database.

## Features

- **Multi-site scraping**: Collects listings from three motorsport websites:
  - Motorsport Auctions (motorsportauctions.com)
  - Rally Cars For Sale (rallycarsforsale.com)
  - Race Cars For You (racecarsforyou.com)
- **Async operations**: Built with async/await for efficient concurrent scraping
- **Database storage**: Stores collected data in PostgreSQL with schema management
- **Docker support**: Includes Docker and Docker Compose setup for PostgreSQL and pgAdmin
- **Excel export**: Can export data to Excel files using pandas

## Prerequisites

- Python 3.13+
- PostgreSQL (or Docker for containerized setup)
- Playwright browsers (automatically installed)

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd racecar-aggregator
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install
```

## Setup

### Database Setup

Option 1: Using Docker (Recommended)
```bash
docker-compose up -d
```
This starts PostgreSQL on `localhost:5432` and pgAdmin on `localhost:5050`.

Option 2: Manual PostgreSQL Setup
Ensure PostgreSQL is running on `localhost:5432` with:
- Username: `docker`
- Password: `docker`
- Database: `docker`

## Usage

### Running the scraper

```bash
python Run.py
```

Or use the shell scripts:
- **macOS/Linux**: `./Run.sh`
- **Windows**: `Run.bat`

The script will:
1. Create the database schema if it doesn't exist
2. Scrape listings from specified sites
3. Store data in PostgreSQL
4. Handle upserts to avoid duplicates

### Project Structure

```
├── Pages/                  # Site-specific scrapers
│   ├── Motorsportauctions.py
│   ├── Racecarsforyou.py
│   └── Rallycarsforsale.py
├── Utilities/              # Helper modules
│   ├── db_utils.py        # Database operations
│   ├── browser_async.py   # Browser automation helpers
│   ├── actions_async.py   # DOM interaction helpers
│   ├── pagination_async.py
│   ├── scroll_async.py
│   ├── waits_async.py
│   └── ...
├── output/                # Generated Excel files
├── docker-compose.yaml    # Docker services configuration
├── Dockerfile             # Container image definition
└── Run.py                 # Main entry point
```

## Dependencies

- **playwright**: Browser automation for scraping
- **psycopg2-binary**: PostgreSQL database driver
- **pandas**: Data manipulation and Excel export
- **openpyxl**: Excel file handling
- **screeninfo**: Monitor detection for browser sizing

## Configuration

Database connection settings are configured in `Utilities/db_utils.py`:
```python
host="localhost"
database="docker"
user="docker"
password="docker"
port=5432
```

## Development Notes

- All page scrapers are built as Page Objects using Playwright
- Async/await pattern is used throughout for performance
- Database schema includes fields for: title, price, date, images, links, descriptions, and location
- Each product has a unique ID to prevent duplicate entries
