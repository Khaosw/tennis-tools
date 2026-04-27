import yaml
import os
import requests


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_amap_key():
    config = load_config()
    return config.get("amap", {}).get("key", "")


def geocode_address(address: str, city: str = "北京") -> tuple:
    """
    使用高德地图 API 获取地址的经纬度
    返回: (latitude, longitude)
    """
    key = get_amap_key()
    if not key:
        return (0.0, 0.0)

    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": key,
        "address": address,
        "city": city,
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get("status") == "1" and data.get("geocodes"):
            location = data["geocodes"][0].get("location", "0,0")
            lng, lat = location.split(",")
            return (float(lat), float(lng))
    except Exception:
        pass
    return (0.0, 0.0)