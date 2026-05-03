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

    BASE_DIR = os.getcwd()
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    file_path = os.path.join(OUTPUT_DIR, file_path)

    if not isinstance(items, list):
        print("Invalid items")
        return

    # Convert items to DataFrame
    new_df = pd.DataFrame([item for item in items if isinstance(item, dict)])

    # If file exists → append
    if os.path.exists(file_path):
        try:
            old_df = pd.read_excel(file_path, sheet_name="data")
            combined_df = pd.concat([old_df, new_df], ignore_index=True)
        except Exception:
            combined_df = new_df
    else:
        combined_df = new_df

    # Meta handling
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        meta = {"meta": str(meta)}

    meta["last_updated"] = datetime.now().isoformat()
    meta["total_rows"] = len(combined_df)

    # Write file (overwrite but keep appended data)
    with pd.ExcelWriter(file_path, engine="openpyxl", mode="w") as writer:
        combined_df.to_excel(writer, sheet_name="data", index=False)
        pd.DataFrame([meta]).to_excel(writer, sheet_name="meta", index=False)
def deleteoldfile(file_path: str):
    BASE_DIR = os.getcwd()
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")
    file_path = os.path.join(OUTPUT_DIR, file_path)

    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted old file: {file_path}")
    else:
        print(f"No existing file to delete at: {file_path}")