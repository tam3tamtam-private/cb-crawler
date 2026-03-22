from typing import Dict, List, Sequence
import json
import psycopg2
from psycopg2.extras import execute_values
from crawler import config


def get_connection():
    if config.DATABASE_URL:
        return psycopg2.connect(config.DATABASE_URL)
    return psycopg2.connect(
        host=config.PGHOST,
        port=config.PGPORT,
        dbname=config.PGDATABASE,
        user=config.PGUSER,
        password=config.PGPASSWORD,
    )


def fetch_categories(conn) -> List[Dict[str, str]]:
    sql = """
        SELECT category_id, webpage_id, category_url
        FROM cb_m_category
        WHERE category_url IS NOT NULL
        ORDER BY category_id
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return [
        {"category_id": r[0], "webpage_id": r[1], "category_url": r[2]}
        for r in rows
    ]


def bulk_insert_campaigns(
    conn,
    rows: Sequence[Dict[str, object]],
    batch_size: int,
) -> int:
    if not rows:
        return 0

    sql = """
        INSERT INTO cb_fr_campaigns (
            raw_campaign_url,
            webpage_id,
            category_id,
            raw_campaign_name,
            raw_cb_value,
            raw_json,
            crawl_id
        ) VALUES %s
    """

    total = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            values = [
                (
                    r.get("raw_campaign_url"),
                    r.get("webpage_id"),
                    r.get("category_id"),
                    r.get("raw_campaign_name"),
                    r.get("raw_cb_value"),
                    json.dumps(r.get("raw_json") or {}),
                    r.get("crawl_id"),
                )
                for r in batch
            ]
            execute_values(cur, sql, values)
            total += len(values)
        conn.commit()
    return total
