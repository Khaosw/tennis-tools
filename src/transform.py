import csv
import json
import random
import re
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from geocoding import geocode_address

# 北京区域预设映射
REGION_MAPPING = {
    "朝阳": {"province_id": 1, "city_id": 2, "district_id": 5},
    "海淀": {"province_id": 1, "city_id": 2, "district_id": 8},
    "东城": {"province_id": 1, "city_id": 2, "district_id": 2},
    "西城": {"province_id": 1, "city_id": 2, "district_id": 3},
    "丰台": {"province_id": 1, "city_id": 2, "district_id": 6},
    "石景山": {"province_id": 1, "city_id": 2, "district_id": 7},
    "通州": {"province_id": 1, "city_id": 2, "district_id": 12},
    "昌平": {"province_id": 1, "city_id": 2, "district_id": 14},
    "大兴": {"province_id": 1, "city_id": 2, "district_id": 18},
    "房山": {"province_id": 1, "city_id": 2, "district_id": 19},
    "顺义": {"province_id": 1, "city_id": 2, "district_id": 13},
    "门头沟": {"province_id": 1, "city_id": 2, "district_id": 9},
    "怀柔": {"province_id": 1, "city_id": 2, "district_id": 16},
    "平谷": {"province_id": 1, "city_id": 2, "district_id": 17},
    "密云": {"province_id": 1, "city_id": 2, "district_id": 15},
    "延庆": {"province_id": 1, "city_id": 2, "district_id": 20},
}

COVER_URL = "https://tennis.52emo.com/court/1768728941013gl3HCxVWEY.webp"

# 配套设施关键词映射
FACILITY_KEYWORDS = {
    "shower": ["淋浴", "有淋浴间"],
    "toilet": ["卫生间", "有卫生间"],
    "locker": ["储物柜", "有储物柜"],
    "rest_area": ["休息区", "有休息区"],
    "ac": ["空调", "空调开放"],
    "no_smoke": ["无烟环境"],
    "heating": ["暖气"],
    "locker_room": ["更衣室"],
    "parking": ["停车", "免费停车"],
}


def parse_opening_hours(text: str) -> str:
    """标准化营业时间格式"""
    if not text:
        return "08:00 - 18:00"

    text = text.strip()
    # 尝试提取时间格式 "HH:MM - HH:MM"
    pattern = r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})"
    match = re.search(pattern, text)
    if match:
        start_time = match.group(1)
        end_time = match.group(2)
        return f"{start_time} - {end_time}"

    return "08:00 - 18:00"


def parse_court_count(text: str) -> int:
    """从文本中提取场地数量"""
    if not text:
        return 0
    # 匹配数字
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else 0


def parse_facilities(text: str) -> dict:
    """将配套设施文本转换为 JSON 对象"""
    if not text:
        return {}

    facilities = {}
    text = text.replace("\n", " ").replace("\r", " ")

    for key, keywords in FACILITY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                facilities[key] = 1
                break

    return facilities


def extract_phone(text: str) -> str:
    """从文本中提取最长的一段连续数字作为电话"""
    if not text:
        return ""

    # 移除非数字字符，保留纯数字
    import re
    numbers = re.findall(r'\d+', str(text))
    if not numbers:
        return ""

    # 返回最长的数字串
    return max(numbers, key=len)


def process_row(row_data: dict, geocode_cache: dict) -> dict:
    """处理一行数据，转换为 court 表格式"""
    region = row_data.get("区域", "").strip()
    region_info = REGION_MAPPING.get(region, {"province_id": 1, "city_id": 2, "district_id": 0})

    # name: 换行符替换为空格
    name = row_data.get("名称", "").strip()
    name = name.replace("\n", " ").replace("\r", " ")

    # address: 换行符替换为空格，清理特殊字符
    address = row_data.get("位置", "").strip()
    address = address.replace("\n", " ").replace("\r", " ")
    address = re.sub(r'[<>]', '', address)

    # contact_number: 提取最长连续数字
    contact_number = extract_phone(row_data.get("电话", ""))

    # 经纬度处理
    lat, lng = 0.0, 0.0
    cache_key = address
    if cache_key not in geocode_cache:
        lat, lng = geocode_address(address)
        geocode_cache[cache_key] = (lat, lng)
    else:
        lat, lng = geocode_cache[cache_key]

    # 室内/室外数量
    indoor_text = row_data.get("室内", "")
    outdoor_text = row_data.get("室外", "")
    indoor_count = parse_court_count(indoor_text)
    outdoor_count = parse_court_count(outdoor_text)

    # 配套设施
    facilities_text = row_data.get("配套设施", "")
    facilities = parse_facilities(facilities_text)

    # court_types: 有室内场地=1，有室外场地=0
    court_types = 1
    if indoor_count == 0 and outdoor_count > 0:
        court_types = 0

    return {
        "name": name,
        "cover": COVER_URL,
        "province_id": region_info["province_id"],
        "city_id": region_info["city_id"],
        "district_id": region_info["district_id"],
        "address": address,
        "latitude": lat,
        "longitude": lng,
        "contact_number": contact_number,
        "opening_hours": parse_opening_hours(row_data.get("营业时间", "")),
        "court_types": court_types,
        "is_indoor": 1,
        "facilities": json.dumps(facilities, ensure_ascii=False),
        "base_price": random.randint(100, 200),
        "description": "这里不错",
        "rating": 0.0,
        "enrolling_count": 0,
        "status": 0,
    }


def read_input_csv(filepath: str) -> list:
    """读取并合并 CSV 多行记录"""
    records = []
    current_record = {}

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)

        for row in reader:
            if not row or len(row) < 2:
                continue

            seq = row[0].strip() if row[0] else ""

            # 如果有序号，说明是新记录
            if seq and seq.isdigit():
                # 保存上一条记录
                if current_record:
                    records.append(current_record)

                # 构建新记录
                current_record = {}
                for i, col in enumerate(row):
                    if i < len(header):
                        current_record[header[i]] = col
            else:
                # 合并到当前记录
                for i, col in enumerate(row):
                    if i < len(header):
                        key = header[i]
                        if key in current_record and current_record[key]:
                            current_record[key] += "\n" + col
                        else:
                            current_record[key] = col

        # 保存最后一条记录
        if current_record:
            records.append(current_record)

    return records


def write_output_csv(records: list, output_path: str):
    """写入 normalized CSV"""
    fieldnames = [
        "name", "cover", "province_id", "city_id", "district_id",
        "address", "latitude", "longitude", "contact_number",
        "opening_hours", "court_types", "is_indoor", "facilities",
        "base_price", "description", "rating", "enrolling_count", "status"
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def main():
    input_path = os.path.join(os.path.dirname(__file__), "..", "data", "input.csv")
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    output_path = os.path.join(output_dir, "court_normalized.csv")

    os.makedirs(output_dir, exist_ok=True)

    print("Reading input CSV...")
    raw_records = read_input_csv(input_path)
    print(f"Raw records: {len(raw_records)}")

    print("Processing records...")
    geocode_cache = {}
    normalized_records = []

    for i, raw in enumerate(raw_records):
        try:
            record = process_row(raw, geocode_cache)
            normalized_records.append(record)
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(raw_records)}")
        except Exception as e:
            print(f"Error processing row {i}: {e}")

    print(f"Writing {len(normalized_records)} records to {output_path}")
    write_output_csv(normalized_records, output_path)
    print("Done!")


if __name__ == "__main__":
    main()