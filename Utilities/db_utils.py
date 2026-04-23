import json

import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",   # IMPORTANT (explained below)
        database="docker",
        user="docker",
        password="docker",
        port=5432
    )

# 🧱 CREATE TABLE
def create_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            unique_id TEXT PRIMARY KEY,

            title TEXT,
            price TEXT,
            date TEXT,
            image_urls TEXT[],

            link_url TEXT,
            detailed_description TEXT,
            location TEXT,
            contact_info TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            is_synced BOOLEAN DEFAULT FALSE
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


# 🚀 INSERT / UPDATE (SMART UPSERT)
def upsert_product(data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO products (
            unique_id, title, price, date, image_urls,
            link_url, detailed_description, location, contact_info,
            created_at, is_synced
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), FALSE)

        ON CONFLICT (unique_id) DO UPDATE
        SET
            title = EXCLUDED.title,
            price = EXCLUDED.price,
            date = EXCLUDED.date,
            image_urls = EXCLUDED.image_urls,
            link_url = EXCLUDED.link_url,
            detailed_description = EXCLUDED.detailed_description,
            location = EXCLUDED.location,
            contact_info = EXCLUDED.contact_info,
            updated_at = NOW(),
            is_synced = FALSE

        WHERE
            products.title IS DISTINCT FROM EXCLUDED.title OR
            products.price IS DISTINCT FROM EXCLUDED.price OR
            products.date IS DISTINCT FROM EXCLUDED.date OR
            products.image_urls IS DISTINCT FROM EXCLUDED.image_urls OR
            products.link_url IS DISTINCT FROM EXCLUDED.link_url OR
            products.detailed_description IS DISTINCT FROM EXCLUDED.detailed_description OR
            products.location IS DISTINCT FROM EXCLUDED.location OR
            products.contact_info IS DISTINCT FROM EXCLUDED.contact_info;
    """, (
        data["id"],
        data["title"],
        data["price"],
        data["date"],
        data["imageURLs"],
        data["linkURL"],
        data["detailedDescription"],
        data["location"],
        data["contactInfo"]
    ))

    conn.commit()
    cur.close()
    conn.close()

# 🔍 FETCH UNSYNCED ROWS
def get_unsynced_rows(conn):
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM products
        WHERE is_synced = FALSE;
    """)

    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()

    return [dict(zip(columns, row)) for row in rows]


# 📦 BUILD JSON PAYLOAD
def build_payload(rows):
    return json.dumps({
        "records": rows
    }, default=str)


# 🌐 SEND TO API
def send_to_api(payload):
    try:
        response = requests.post(
            "https://api.base44.com/endpoint",  # replace later
            headers={"Content-Type": "application/json"},
            data=payload,
            timeout=10
        )

        print("API Status:", response.status_code)
        return response.status_code == 200

    except Exception as e:
        print("❌ API Error:", e)
        return False


# ✅ MARK AS SYNCED
def mark_as_synced(conn, ids):
    cur = conn.cursor()

    cur.execute("""
        UPDATE products
        SET is_synced = TRUE
        WHERE unique_id = ANY(%s);
    """, (ids,))

    conn.commit()


# 🔁 FULL SYNC PIPELINE
def sync_pipeline():
    conn = get_connection()

    rows = get_unsynced_rows(conn)

    if not rows:
        print("✅ Nothing to sync")
        return

    payload = build_payload(rows)

    success = send_to_api(payload)

    if success:
        ids = [row["unique_id"] for row in rows]
        mark_as_synced(conn, ids)
        print(f"✅ Synced {len(ids)} records")
    else:
        print("❌ Sync failed, will retry next run")

    conn.close()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO products (title, price) VALUES (%s, %s)",
        ("Test Car", "10000")
    )

    conn.commit()
    cur.close()
    conn.close()