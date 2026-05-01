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
def bulk_insert(payload):
    
    import requests

    headers = {"api_key": "cf2344429a6641e5acf63001a74d24e4", "Content-Type": "application/json"}
    response = requests.post("https://priyom.base44.app/api/entities/CarListing/bulk", headers=headers, 
                             json=[{"title":"Example title","price":0,"images":[]}])
    data = response.json()
        
    try:
        response = requests.post(
            "https://app.base44.com/api/apps/{{app_id}}/entities/CarListing",
            headers={"Content-Type": "application/json"},
            data=payload,
            timeout=10
        )

        print("API Status:", response.status_code)
        return response.status_code == 200

    except Exception as e:
        print("❌ API Error:", e)
        return False

