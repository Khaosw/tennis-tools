import csv
import json
import sys
import io
from decimal import Decimal

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from db.connection import get_connection


# court 表字段定义（用于类型校验）
COURT_FIELDS = {
    "name": {"type": str, "required": True, "default": ""},
    "cover": {"type": str, "required": True, "default": ""},
    "province_id": {"type": int, "required": True, "default": 1},
    "city_id": {"type": int, "required": True, "default": 2},
    "district_id": {"type": int, "required": True, "default": 0},
    "address": {"type": str, "required": True, "default": ""},
    "latitude": {"type": float, "required": True, "default": 0.0},
    "longitude": {"type": float, "required": True, "default": 0.0},
    "geo_point": {"type": str, "required": True, "default": None},
    "contact_number": {"type": str, "required": True, "default": ""},
    "opening_hours": {"type": str, "required": True, "default": "08:00 - 22:00"},
    "court_types": {"type": int, "required": True, "default": 1},
    "is_indoor": {"type": int, "required": True, "default": 1},
    "facilities": {"type": str, "required": True, "default": "{}"},
    "base_price": {"type": int, "required": True, "default": 120},
    "description": {"type": str, "required": False, "default": ""},
    "rating": {"type": float, "required": True, "default": 0.0},
    "enrolling_count": {"type": int, "required": True, "default": 0},
    "status": {"type": int, "required": True, "default": 0},
}


def cast_value(field_name: str, value: str):
    """强制类型转换"""
    field_def = COURT_FIELDS.get(field_name)
    if not field_def:
        return value

    expected_type = field_def["type"]
    default_value = field_def["default"]

    # geo_point 特殊处理
    if field_name == "geo_point":
        return value  # 不在这里处理，由后面逻辑单独处理

    if value is None or value == "":
        return default_value

    try:
        if expected_type == int:
            return int(float(value))
        elif expected_type == float:
            return float(value)
        elif expected_type == str:
            return str(value)
        else:
            return value
    except (ValueError, TypeError):
        print(f"  [WARN] {field_name}: '{value}' cast failed, use default {default_value}")
        return default_value


def validate_row(row: dict) -> tuple:
    """校验行数据，返回 (是否有效, 错误信息)"""
    errors = []

    for field_name, field_def in COURT_FIELDS.items():
        value = row.get(field_name, "")

        # 检查必填字段
        if field_def["required"] and (value is None or str(value).strip() == ""):
            # name 和 address 绝对不能为空
            if field_name in ["name", "address"]:
                errors.append(f"{field_name} 不能为空")
            continue

        # 类型校验
        try:
            cast_value(field_name, str(value))
        except Exception as e:
            errors.append(f"{field_name} 类型错误: {e}")

    # 额外校验
    rating = cast_value("rating", row.get("rating", "0"))
    if not (0 <= rating <= 5):
        errors.append(f"rating 超出范围 [0-5]: {rating}")

    base_price = cast_value("base_price", row.get("base_price", "0"))
    if base_price < 0:
        errors.append(f"base_price 不能为负数: {base_price}")

    return (len(errors) == 0, "; ".join(errors))


def read_csv(filepath: str) -> list:
    """读取 CSV 文件，自动检测编码"""
    encodings = ["utf-8-sig", "gbk", "gb2312", "gb18030"]

    for enc in encodings:
        try:
            records = []
            with open(filepath, "r", encoding=enc) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(row)
            print(f"  [INFO] 使用编码: {enc}")
            return records
        except UnicodeDecodeError:
            continue

    raise ValueError(f"无法读取 CSV 文件，尝试了编码: {encodings}")


def import_to_mysql(records: list, dry_run: bool = True):
    """导入数据到 MySQL"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            valid_count = 0
            error_count = 0
            skipped_count = 0

            for i, row in enumerate(records):
                # 类型转换
                converted_row = {}
                for field_name in COURT_FIELDS.keys():
                    value = row.get(field_name, "")
                    converted_row[field_name] = cast_value(field_name, value)

                # 生成 geo_point (MySQL POINT format: POINT(lng lat))
                lng = converted_row.get("longitude", 0)
                lat = converted_row.get("latitude", 0)
                if lng and lat:
                    converted_row["geo_point"] = f"POINT({lng} {lat})"
                else:
                    converted_row["geo_point"] = "POINT(0 0)"

                # 校验
                is_valid, error_msg = validate_row(converted_row)
                if not is_valid:
                    print(f"  [SKIP] Row {i+1} validation failed: {error_msg}")
                    skipped_count += 1
                    continue

                # 构建 SQL - geo_point 需要使用 ST_GeomFromText 函数
                field_list = list(COURT_FIELDS.keys())
                sql_fields = []
                sql_values = []
                sql_set_parts = []

                for f in field_list:
                    sql_fields.append(f)
                    if f == "geo_point":
                        geo = converted_row.get("geo_point")
                        if geo:
                            sql_set_parts.append(f"ST_GeomFromText('{geo}')")
                        else:
                            sql_set_parts.append("NULL")
                    else:
                        sql_set_parts.append("%s")
                        sql_values.append(converted_row[f])

                sql = f"INSERT INTO court ({', '.join(sql_fields)}) VALUES ({', '.join(sql_set_parts)})"

                if dry_run:
                    print(f"  [DRY RUN] Row {i+1}: {converted_row['name'][:30]}...")
                    valid_count += 1
                else:
                    cursor.execute(sql, sql_values)
                    valid_count += 1

                if (i + 1) % 20 == 0:
                    print(f"  Processed {i+1}/{len(records)} records")

            conn.commit()
            print(f"\nDone: valid={valid_count}, skipped={skipped_count}, error={error_count}")

            return {"valid": valid_count, "skipped": skipped_count, "error": error_count}
    finally:
        conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="将 normalized CSV 导入 MySQL")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="仅预览不实际导入 (默认)")
    parser.add_argument("--execute", action="store_true", default=False,
                        help="实际执行导入 (需要此参数)")
    parser.add_argument("--yes", action="store_true", default=False,
                        help="直接确认，无需交互输入")
    parser.add_argument("--file", default="output/court_normalized.csv",
                        help="CSV 文件路径 (相对于 src 目录)")

    args = parser.parse_args()

    import os
    csv_path = os.path.join(os.path.dirname(__file__), args.file)

    print(f"Reading CSV: {csv_path}")
    records = read_csv(csv_path)
    print(f"Total {len(records)} records\n")

    if args.execute:
        print("[EXECUTE MODE] About to import data to MySQL...")
        if not args.yes:
            confirm = input("Confirm import? (yes/no): ")
            if confirm.lower() != "yes":
                print("Cancelled")
                return
        else:
            print("[AUTO CONFIRM] --yes flag specified")
        import_to_mysql(records, dry_run=False)
    else:
        print("[DRY RUN MODE] Only preview, no actual import")
        print("Use --execute flag to actually import\n")
        import_to_mysql(records, dry_run=True)


if __name__ == "__main__":
    main()