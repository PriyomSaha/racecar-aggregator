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
    # Create DataFrame from items (handle empty list)
    try:
        df = pd.DataFrame(items)
    except Exception:
        df = pd.DataFrame()

    # Use ExcelWriter to create multiple sheets (data + optional meta)
    with pd.ExcelWriter(file_path) as writer:
        # Write main data
        df.to_excel(writer, sheet_name="data", index=False)

        # If meta provided, write to separate sheet to avoid mixing types
        if meta:
            try:
                meta_df = pd.DataFrame([meta])
            except Exception:
                # fallback: coerce meta to a single-column DataFrame
                meta_df = pd.DataFrame({"meta": [str(meta)]})
            meta_df.to_excel(writer, sheet_name="meta", index=False)

    print(f"Excel file saved at: {file_path}")