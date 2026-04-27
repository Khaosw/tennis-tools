import yaml
import os
import pymysql


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_connection():
    config = load_config()
    db_config = config["database"]
    return pymysql.connect(
        host=db_config["host"],
        port=db_config["port"],
        user=db_config["username"],
        password=db_config["password"],
        database=db_config["name"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def get_read_only_connection():
    config = load_config()
    db_config = config["database"]
    # pymysql 不支持 readonly 参数，应用层只使用 SELECT
    return pymysql.connect(
        host=db_config["host"],
        port=db_config["port"],
        user=db_config["username"],
        password=db_config["password"],
        database=db_config["name"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )