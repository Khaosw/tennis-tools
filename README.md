# TennisCourtImport

连接阿里云 MySQL 数据库（只读），查询网球场地数据。

## 快速开始

```bash
cd src
pip install -r requirements.txt
python main.py
```

## court 表结构

| 字段 | 类型 | 可空 | 主键 | 说明 |
|------|------|:----:|:----:|------|
| id | bigint unsigned | NO | PRI | 主键 |
| application_id | bigint unsigned | NO | | 应用ID |
| name | varchar(128) | NO | | 场馆名称 |
| cover | varchar(255) | NO | | 封面图URL |
| user_id | bigint unsigned | NO | | 用户ID |
| province_id | bigint unsigned | NO | | 省份ID |
| city_id | bigint unsigned | NO | | 城市ID |
| district_id | bigint unsigned | NO | MUL | 区县ID |
| address | varchar(512) | NO | | 详细地址 |
| latitude | decimal(10,6) unsigned | NO | | 纬度 |
| longitude | decimal(10,6) unsigned | NO | | 经度 |
| geo_point | point | NO | MUL | 地理坐标 |
| contact_number | varchar(20) | NO | | 联系电话 |
| business_license_url | varchar(255) | NO | | 营业执照URL |
| court_qty | smallint unsigned | NO | | 场地数量 |
| court_types | json | NO | | 场地类型，见下方说明 |
| is_indoor | json | NO | | 室内/室外，见下方说明 |
| opening_hours | json | NO | | 营业时间，见下方说明 |
| facilities | json | NO | | 设施配置，见下方说明 |
| base_price | int unsigned | NO | | 基础价格(元) |
| description | text | YES | | 场馆描述 |
| rating | decimal(2,1) unsigned | NO | | 评分(0-5) |
| enrolling_count | int unsigned | NO | | 报名人数 |
| status | tinyint unsigned | NO | | 状态(0/1) |
| created_at | datetime | NO | | 创建时间 |
| updated_at | datetime | NO | | 更新时间 |
| deleted_at | datetime | YES | | 删除时间 |

### court_types 字段说明 (JSON 数组)

```json
[0, 1, 2, 3]
```

| 值 | 含义 |
|:--:|------|
| 0 | 硬地 |
| 1 | 红土 |
| 2 | 草地 |
| 3 | 地毯 |

### is_indoor 字段说明 (JSON 数组)

```json
[0, 1]
```

| 值 | 含义 |
|:--:|------|
| 0 | 室外 |
| 1 | 室内 |

### opening_hours 字段说明 (JSON 数组)

```json
[
  {"weekdays": [1, 2, 3, 4, 5], "start_time": "08:00", "end_time": "22:00"},
  {"weekdays": [6, 7], "start_time": "09:00", "end_time": "20:00"}
]
```

- `weekdays`: 1=周一 ... 7=周日
- `start_time` / `end_time`: 该组日期的营业时间段

### facilities 字段说明 (JSON)

```json
{
  "shower": "https://tennis.52emo.com/court/icon/shower.webp",
  "parking": "https://tennis.52emo.com/court/icon/parking.webp"
}
```

- key: 设施名称（对应 `court_facilities_config.name`）
- value: 设施图标 URL

## court_facilities_config 表（设施配置）

| id | name | content | pic |
|----|------|---------|-----|
| 1 | shower | 淋浴 | https://static.poptennis.com.cn/court/icon/shower.webp |
| 2 | parking | 停车 | https://static.poptennis.com.cn/court/icon/parking.webp |
| 3 | rent | 租赁 | https://static.poptennis.com.cn/court/icon/rent.webp |
| 4 | change | 更衣室 | https://static.poptennis.com.cn/court/icon/change.webp |
| 5 | ac | 空调 | https://static.poptennis.com.cn/court/icon/ac.webp |
| 6 | night | 夜场 | https://static.poptennis.com.cn/court/icon/night.webp |
| 7 | store | 储物 | https://static.poptennis.com.cn/court/icon/store.webp |
| 8 | shop | 购物 | https://static.poptennis.com.cn/court/icon/shop.webp |
| 9 | coach | 教练 | https://static.poptennis.com.cn/court/icon/coach.webp |
| 10 | 24h | 24小时 | https://static.poptennis.com.cn/court/icon/24h.webp |
| 11 | no_smoking | 无烟环境 | https://static.poptennis.com.cn/court/icon/no_smoking.webp |
| 12 | lounge | 有休息区 | https://static.poptennis.com.cn/court/icon/lounge.webp |
| 13 | restroom | 有卫生间 | https://static.poptennis.com.cn/court/icon/restroom.webp |
| 14 | heating | 暖气 | https://static.poptennis.com.cn/court/icon/heating.webp |
| 15 | free_food | 免费饮食 | https://static.poptennis.com.cn/court/icon/free_food.webp |