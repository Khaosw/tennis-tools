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
| name | varchar(128) | NO | | 场馆名称 |
| cover | varchar(255) | NO | | 封面图URL |
| province_id | bigint unsigned | NO | | 省份ID |
| city_id | bigint unsigned | NO | | 城市ID |
| district_id | bigint unsigned | NO | MUL | 区县ID |
| address | varchar(512) | NO | | 详细地址 |
| latitude | decimal(10,6) unsigned | NO | | 纬度 |
| longitude | decimal(10,6) unsigned | NO | | 经度 |
| geo_point | point | NO | MUL | 地理坐标 |
| contact_number | varchar(20) | NO | | 联系电话 |
| opening_hours | varchar(64) | NO | | 营业时间 |
| court_types | tinyint unsigned | NO | | 场地类型(0/1) |
| is_indoor | tinyint unsigned | NO | | 是否室内(0/1) |
| facilities | json | NO | | 设施配置 |
| base_price | int unsigned | NO | | 基础价格(元) |
| description | text | YES | | 场馆描述 |
| rating | decimal(2,1) unsigned | NO | | 评分(0-5) |
| enrolling_count | int unsigned | NO | | 报名人数 |
| status | tinyint unsigned | NO | | 状态(0/1) |
| created_at | datetime | NO | | 创建时间 |
| updated_at | datetime | NO | | 更新时间 |
| deleted_at | datetime | YES | | 删除时间 |

### facilities 字段说明 (JSON)

```json
{
  "wifi": 1,
  "coach": 0,
  "light": true,
  "rental": 0,
  "shower": 1,
  "parking": 0,
  "vending": 0
}
```