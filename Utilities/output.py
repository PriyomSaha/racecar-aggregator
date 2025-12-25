import os
import sys
import subprocess
from datetime import datetime

import pandas as pd

def as_json(items: list, meta: dict | None = None):
    """Format items and optional metadata as a JSON-serializable dict.

    Use case: standardize output for list endpoints or helpers, returning
    a dict with `count`, `results`, and `meta` keys.
    """
    return {
        "count": len(items),
        "results": items,
        "meta": meta or {}
    }


def as_excel(items: list, meta: dict | None = None, file_path: str = "output.xlsx",
             sheet_name_items: str = "Items", sheet_name_meta: str = "Metadata"):

    """Write items to an Excel file with an optional meta sheet.

    This writes the main data to a sheet named 'data' and, if `meta` is
    provided, writes metadata to a separate sheet named 'meta'. This
    preserves structure and prints cleanly in Excel viewers.
    """
    # Attempt to close any open Excel application to avoid file locks.
    # This uses platform-specific commands but will silently continue
    # if the operation fails or the platform is unsupported.
    try:
        if sys.platform == "darwin":
            # macOS: politely ask Microsoft Excel to quit via AppleScript
            subprocess.run(["osascript", "-e", "tell application \"Microsoft Excel\" to quit"], check=False)
            # fallback: try pkill for any lingering process
            subprocess.run(["pkill", "-f", "Microsoft Excel"], check=False)
        elif sys.platform.startswith("win"):
            # Windows: use taskkill to terminate Excel processes
            subprocess.run(["taskkill", "/f", "/im", "EXCEL.EXE"], check=False, shell=True)
        else:
            # Linux/other: try pkill
            subprocess.run(["pkill", "-f", "excel"], check=False)
    except Exception:
        # Ignore any errors from attempting to kill/quit Excel
        pass

    # If the file exists, remove it so we always start fresh
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        # ignore removal errors and proceed to overwrite via ExcelWriter
        pass

    # Ensure meta is a dict and add/update last_updated timestamp
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        meta = {"meta": str(meta)}
    meta["last_updated"] = datetime.now().isoformat()

    # Create DataFrame from items (handle empty list)
    try:
        df = pd.DataFrame(items)
    except Exception:
        df = pd.DataFrame()

    # Use ExcelWriter to create multiple sheets (data + optional meta)
    with pd.ExcelWriter(file_path) as writer:
        # Write main data
        df.to_excel(writer, sheet_name="data", index=False)

        # Write meta to separate sheet
        try:
            meta_df = pd.DataFrame([meta])
        except Exception:
            meta_df = pd.DataFrame({"meta": [str(meta)]})
        meta_df.to_excel(writer, sheet_name="meta", index=False)

    print(f"Excel file saved at: {file_path}")