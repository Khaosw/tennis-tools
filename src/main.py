import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from db.connection import get_read_only_connection


def query_court_table_info():
    conn = get_read_only_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DESCRIBE court")
            columns = cursor.fetchall()
            print("=== court table structure ===")
            print(f"{'Field':<30} {'Type':<25} {'Null':<6} {'Key':<6} {'Default':<15} {'Extra':<20}")
            print("-" * 110)
            for col in columns:
                print(
                    f"{col['Field']:<30} {col['Type']:<25} {col['Null']:<6} "
                    f"{col['Key']:<6} {str(col.get('Default', '')):<15} {col.get('Extra', ''):<20}"
                )
    finally:
        conn.close()


def query_court_sample():
    conn = get_read_only_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM court LIMIT 5")
            rows = cursor.fetchall()
            if not rows:
                print("court 表为空")
                return
            print("\n=== court table first 5 rows ===")
            fields = rows[0].keys()
            print(" | ".join(fields))
            print("-" * 80)
            for row in rows:
                print(" | ".join(str(v) for v in row.values()))
    finally:
        conn.close()


if __name__ == "__main__":
    query_court_table_info()
    query_court_sample()