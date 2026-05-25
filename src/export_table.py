import csv
import os
import sys
import io
import argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from db.connection import get_connection


def export_table(table_name: str, output_dir: str):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute(f"DESC {table_name}")
            cols = [r["Field"] for r in c.fetchall()]

            c.execute(f"SELECT * FROM {table_name}")
            rows = c.fetchall()

            path = os.path.join(output_dir, f"{table_name}.csv")
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=cols)
                writer.writeheader()
                writer.writerows(rows)

            print(f"  {table_name}: {len(rows)} rows -> {path}")
            return path
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="导出 MySQL 表为 CSV")
    parser.add_argument("tables", nargs="+", help="要导出的表名")
    parser.add_argument("--output-dir", default=None,
                        help="输出目录 (默认 src/output)")
    args = parser.parse_args()

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(os.path.dirname(__file__), "output")

    os.makedirs(output_dir, exist_ok=True)

    for table in args.tables:
        try:
            export_table(table, output_dir)
        except Exception as e:
            print(f"  [ERROR] {table}: {e}")


if __name__ == "__main__":
    main()
