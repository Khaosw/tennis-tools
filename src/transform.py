import csv
import json
import random
import re
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from geocoding import geocode_address

# 区域预设映射 (来源: 民政部 2024 行政区划代码, 拆分为两位)
REGION_MAPPING = {
    # 北京 (province=11, city=01)
    "东城":   {"province_id": 11, "city_id": 1, "district_id": 1},
    "西城":   {"province_id": 11, "city_id": 1, "district_id": 2},
    "朝阳":   {"province_id": 11, "city_id": 1, "district_id": 5},
    "丰台":   {"province_id": 11, "city_id": 1, "district_id": 6},
    "石景山": {"province_id": 11, "city_id": 1, "district_id": 7},
    "海淀":   {"province_id": 11, "city_id": 1, "district_id": 8},
    "门头沟": {"province_id": 11, "city_id": 1, "district_id": 9},
    "房山":   {"province_id": 11, "city_id": 1, "district_id": 11},
    "通州":   {"province_id": 11, "city_id": 1, "district_id": 12},
    "顺义":   {"province_id": 11, "city_id": 1, "district_id": 13},
    "昌平":   {"province_id": 11, "city_id": 1, "district_id": 14},
    "大兴":   {"province_id": 11, "city_id": 1, "district_id": 15},
    "怀柔":   {"province_id": 11, "city_id": 1, "district_id": 16},
    "平谷":   {"province_id": 11, "city_id": 1, "district_id": 17},
    "密云":   {"province_id": 11, "city_id": 1, "district_id": 18},
    "延庆":   {"province_id": 11, "city_id": 1, "district_id": 19},
    # 上海 (province=31, city=01)
    "黄浦":   {"province_id": 31, "city_id": 1, "district_id": 1},
    "徐汇":   {"province_id": 31, "city_id": 1, "district_id": 4},
    "长宁":   {"province_id": 31, "city_id": 1, "district_id": 5},
    "静安":   {"province_id": 31, "city_id": 1, "district_id": 6},
    "普陀":   {"province_id": 31, "city_id": 1, "district_id": 7},
    "虹口":   {"province_id": 31, "city_id": 1, "district_id": 9},
    "杨浦":   {"province_id": 31, "city_id": 1, "district_id": 10},
    "闵行":   {"province_id": 31, "city_id": 1, "district_id": 12},
    "宝山":   {"province_id": 31, "city_id": 1, "district_id": 13},
    "嘉定":   {"province_id": 31, "city_id": 1, "district_id": 14},
    "浦东":   {"province_id": 31, "city_id": 1, "district_id": 15},
    "金山":   {"province_id": 31, "city_id": 1, "district_id": 16},
    "松江":   {"province_id": 31, "city_id": 1, "district_id": 17},
    "青浦":   {"province_id": 31, "city_id": 1, "district_id": 18},
    "奉贤":   {"province_id": 31, "city_id": 1, "district_id": 20},
    "崇明":   {"province_id": 31, "city_id": 1, "district_id": 51},
    "浦东新": {"province_id": 31, "city_id": 1, "district_id": 15},
}

COVER_URL = "https://tennis.52emo.com/court/1768728941013gl3HCxVWEY.webp"

# 配套设施关键词 → config_name 映射
FACILITY_KEYWORDS = {
    "store": ["有储物柜", "寄存柜", "储物柜"],
    "no_smoking": ["无烟环境"],
    "lounge": ["有休息区", "休息区", "休息长椅"],
    "ac": ["空调开放"],
    "restroom": ["有卫生间", "卫生间", "公共卫生间"],
    "change": ["更衣室"],
    "heating": ["暖气"],
    "rent": ["训练服", "球拍", "器材租赁"],
    "shower": ["有淋浴间", "淋浴"],
    "free_food": ["免费点心", "免费茶水"],
    "parking": ["免费停车"],
    "shop": ["饮品售卖", "饮品区"],
}

FACILITY_ICONS = {
    "shower": "https://static.poptennis.com.cn/court/icon/shower.webp",
    "parking": "https://static.poptennis.com.cn/court/icon/parking.webp",
    "rent": "https://static.poptennis.com.cn/court/icon/rent.webp",
    "change": "https://static.poptennis.com.cn/court/icon/change.webp",
    "ac": "https://static.poptennis.com.cn/court/icon/ac.webp",
    "store": "https://static.poptennis.com.cn/court/icon/store.webp",
    "shop": "https://static.poptennis.com.cn/court/icon/shop.webp",
    "no_smoking": "https://static.poptennis.com.cn/court/icon/no_smoking.webp",
    "lounge": "https://static.poptennis.com.cn/court/icon/lounge.webp",
    "restroom": "https://static.poptennis.com.cn/court/icon/restroom.webp",
    "heating": "https://static.poptennis.com.cn/court/icon/heating.webp",
    "free_food": "https://static.poptennis.com.cn/court/icon/free_food.webp",
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
    """将配套设施文本转换为 JSON 对象，key=config_name, value=icon_url"""
    if not text:
        return {}

    facilities = {}
    text = text.replace("\n", " ").replace("\r", " ")

    for config_name, keywords in FACILITY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                facilities[config_name] = FACILITY_ICONS.get(config_name, "")
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
    region = row_data.get("区", "").strip().rstrip("区")
    region_info = REGION_MAPPING.get(region, {"province_id": 1, "city_id": 2, "district_id": 0})

    # name: 换行符替换为空格
    name = row_data.get("名称", "").strip()
    name = name.replace("\n", " ").replace("\r", " ")

    # address: 换行符替换为空格，清理特殊字符
    address = row_data.get("地址", "").strip()
    address = address.replace("\n", " ").replace("\r", " ")
    address = re.sub(r'[<>]', '', address)

    # contact_number: 提取最长连续数字
    contact_number = extract_phone(row_data.get("电话", ""))

    # 经纬度处理
    city = row_data.get("城市", "").strip()
    district = row_data.get("区", "").strip()
    geocode_addr = city + district + address
    lat, lng = 0.0, 0.0
    cache_key = geocode_addr
    if cache_key not in geocode_cache:
        lat, lng = geocode_address(geocode_addr, city=city)
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

    # court_types: 根据硬地/红土/草地列构建
    hard_count = parse_court_count(row_data.get("硬地", ""))
    clay_count = parse_court_count(row_data.get("红土", ""))
    grass_count = parse_court_count(row_data.get("草地", ""))
    court_types_list = []
    if hard_count > 0:
        court_types_list.append(0)
    if clay_count > 0:
        court_types_list.append(1)
    if grass_count > 0:
        court_types_list.append(2)
    if not court_types_list:
        court_types_list = [0]
    court_types = json.dumps(court_types_list, ensure_ascii=False)

    # court_qty: 室内 + 室外
    court_qty = indoor_count + outdoor_count

    # is_indoor: JSON数组，室内+室外
    is_indoor = []
    if indoor_count > 0:
        is_indoor.append(1)
    if outdoor_count > 0:
        is_indoor.append(0)
    if not is_indoor:
        is_indoor = [1]
    is_indoor_json = json.dumps(is_indoor, ensure_ascii=False)

    # opening_hours: JSON数组
    hours_text = parse_opening_hours(row_data.get("营业时间", ""))
    opening_hours = json.dumps([
        {"weekdays": [1, 2, 3, 4, 5, 6, 7], "start_time": hours_text.split(" - ")[0], "end_time": hours_text.split(" - ")[1]}
    ], ensure_ascii=False)

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
        "opening_hours": opening_hours,
        "court_types": court_types,
        "is_indoor": is_indoor_json,
        "facilities": json.dumps(facilities, ensure_ascii=False),
        "court_qty": court_qty,
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
        "court_qty", "base_price", "description", "rating", "enrolling_count", "status"
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def main():
    input_path = os.path.join(os.path.dirname(__file__), "..", "data", "input2.csv")
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