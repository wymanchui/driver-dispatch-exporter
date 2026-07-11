"""
config.py - 配置管理（与现有版本兼容）
"""
import json
import os

DEFAULT_CONFIG = {
    "drivers": {
        "宋江鸿": "单片货", "方远为": "单片货", "潘庆裕": "单片货",
        "黄宜告": "单片货", "王新建": "单片货", "孔令会": "单片货",
        "帅文小": "中空货", "陈俞任": "中空货", "邓亚雄": "中空货",
        "罗勇": "中空货",
    },
    "name_corrections": {
        "帅文晓": "帅文小",
    },
    "riders": ["罗勇", "张信海"],
    "special_places": ["兴泰物流园"],
    "default_year": "2026",
}

CONFIG_FILE = "freight_config.json"


def get_config_path() -> str:
    """获取配置文件路径（exe 同目录或当前目录）"""
    # 如果是打包的exe，在exe同目录
    if getattr(__import__('sys'), 'frozen', False):
        base = os.path.dirname(__import__('sys').executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, CONFIG_FILE)


def load_config() -> dict:
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return dict(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
