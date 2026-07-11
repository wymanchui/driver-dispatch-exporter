"""
robust_parser.py - 全新的正向解析引擎
对标 MiniMax Code 输出，用逐行逐车前向解析，不用反向正则匹配。

关键改进：
1. 客户名提取用"遇到去/回/出/（/收就停"策略，不吃掉后面的字
2. 架子解析支持链式表达（"去1大2小"→去大1,去小2）
3. 空格智能分隔：以去/回/出/收开头的token归为架子而非客户
4. 回0→跳过，去一件→只有主行
5. 年月格式正确（2026-07）
"""

import re
from typing import List, Optional, Tuple

# ---------- 数据结构 ----------

class RowData:
    """一行表格数据（11 列）"""
    def __init__(self):
        self.年月: str = ""
        self.日期: str = ""
        self.姓名: str = ""
        self.类型: str = ""
        self.客户: str = ""
        self.数量: str = ""
        self.拼车: str = ""
        self.车号: str = ""
        self.流水号: str = ""
        self.跟车: str = ""
        self.原始数据: str = ""

    def to_list(self) -> List[str]:
        return [
            self.年月, self.日期, self.姓名, self.类型,
            self.客户, self.数量, self.拼车, self.车号,
            self.流水号, self.跟车, self.原始数据,
        ]

    @staticmethod
    def header() -> List[str]:
        return ["年月", "日期", "姓名", "类型", "客户", "数量",
                "拼车", "车号", "流水号", "跟车", "原始数据"]


# ---------- 配置 ----------

# 默认司机类型
DEFAULT_DRIVER_TYPES = {
    "宋江鸿": "单片货", "方远为": "单片货", "潘庆裕": "单片货",
    "黄宜告": "单片货", "王新建": "单片货", "孔令会": "单片货",
    "帅文小": "中空货", "陈俞任": "中空货", "邓亚雄": "中空货",
    "罗勇": "中空货",
}

# 姓名纠错
NAME_CORRECTIONS = {
    "帅文晓": "帅文小",
}

# 跟车名单
RIDERS = ["罗勇", "张信海"]

# 特殊地点
SPECIAL_PLACES = ["兴泰物流园"]

DEFAULT_YEAR = "2026"


# ---------- 中文数字 ----------

CN_NUM = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
}

def cn_to_int(cn: str) -> int:
    if cn.isdigit():
        return int(cn)
    if cn == "十":
        return 10
    total = 0
    for ch in cn:
        total = total * 10 + CN_NUM.get(ch, 0)
    return total


# ---------- 正则 ----------

# 车号: 第一车, 第二车, ...
RE_CHEHAO = re.compile(r'第([一二三四五六七八九十百]+)车')

# 日期: X月Y号/日 (允许数字前后有空格)
RE_DATE = re.compile(r'(\d{1,2})\s*月\s*(\d{1,2})\s*[号日]')

# 去一件/去1件
RE_QUYIJIAN = re.compile(r'去\s*[一1]\s*件')

# (中空) 标记
RE_ZHONGKONG = re.compile(r'[（(]中空[）)]')

# 收架子
RE_SHOUJIAZI = re.compile(r'收架子\s*(\d+)\s*(大|小)')

# 动词标记
SHELF_VERBS = {'去', '回', '出', '收'}


# ============================================================
#  核心解析函数
# ============================================================

def _normalize_shelf(action: str, count: int, size: str) -> Tuple[str, int]:
    """归一化架子类型: 出→去"""
    std_action = "去" if action == "出" else action
    return (f"{std_action}{size}架子", count)


def _extract_shelves(rest_text: str) -> List[Tuple[str, int]]:
    """
    从客户剩余文本中提取所有架子信息。
    使用正向tokenizer，支持链式表达（"去1大2小"→去大1,去小2）。
    忽略回0。
    """
    results = []
    text = rest_text.strip()
    i = 0
    last_verb = None

    while i < len(text):
        # 跳过空白
        if text[i] in (' ', '\u3000', '\t'):
            i += 1
            continue

        # 尝试匹配动词
        if text[i] in ('去', '回', '出'):
            last_verb = text[i]
            i += 1
            continue
        elif text[i] == '收':
            # 收架子模式：收架子 N大/N小
            if text[i:i+3] == '收架子' or (i+2 < len(text) and text[i:i+2] == '收架'):
                m = RE_SHOUJIAZI.search(text[i:])
                if m:
                    count = int(m.group(1))
                    size = m.group(2)
                    if count > 0:
                        results.append((f"回{size}架子", count))
                    i += m.end()
                    continue
            i += 1
            continue

        # 尝试匹配 数字+大小
        m = re.match(r'(\d+)\s*(大|小)', text[i:])
        if m and last_verb:
            count = int(m.group(1))
            size = m.group(2)
            if count > 0:
                results.append((f"{last_verb}{size}架子" if last_verb != '出' else f"去{size}架子", count))
            i += m.end()
            continue

        # 跳过其他字符
        i += 1

    return results


def _has_quyijian(text: str) -> bool:
    """检查是否包含去一件/去1件模式"""
    return bool(RE_QUYIJIAN.search(text))


def _has_zhongkong(text: str) -> bool:
    """检查是否包含(中空)标记"""
    return bool(RE_ZHONGKONG.search(text))


def _has_shelf_info(text: str) -> bool:
    """检查文本是否包含任何架子信息"""
    if re.search(r'(去|回|出)\s*\d+\s*(大|小)', text):
        return True
    if re.search(r'收架子', text):
        return True
    return False


def _extract_customer_name_and_rest(section: str) -> Tuple[str, str]:
    """
    从客户段落中提取客户名和剩余文本。
    客户名是连续的中文字符+字母数字，截止到: 去/回/出/收/（/(
    返回 (客户名, 剩余文本)
    
    注意：如果section以去/回/出开头，说明这是架子信息而非客户名
    返回 ("", section)
    """
    section = section.strip()
    if not section:
        return ("", "")

    # 如果以去/回/出开头，这不是客户名
    if section[0] in ('去', '回', '出'):
        return ("", section)

    name_chars = []
    rest_start = len(section)

    for i, ch in enumerate(section):
        if ch in ('去', '回', '出', '收', '（', '('):
            rest_start = i
            break
        if ch == ' ' or ch == '\u3000':
            # 面对空格，检查后面是否是动词或新客户
            next_part = section[i:].lstrip()
            if next_part:
                next_first = next_part[0]
                if next_first in ('去', '回', '出', '收', '（', '('):
                    rest_start = i
                    break
                # 如果后面是中文名+动词结构（如"鑫远去1小"），那个空格是客户分隔符
                # 判断：后面看起来像客户名（中文，不以动词开头）
                if '\u4e00' <= next_first <= '\u9fff' and next_first not in SHELF_VERBS:
                    # 检查后面是否真的是新客户（有架子信息跟随）
                    inner_name, inner_rest = _extract_customer_name_and_rest(next_part)
                    if inner_name and len(inner_name) >= 2 and _has_shelf_info(inner_rest):
                        rest_start = i
                        break
            # 否则空格是名中的干扰，停止
            rest_start = i
            break
        # 收集中文和字母数字
        if '\u4e00' <= ch <= '\u9fff' or ch.isalnum():
            name_chars.append(ch)
        else:
            rest_start = i
            break
    else:
        rest_start = len(section)

    name = ''.join(name_chars).strip()
    rest = section[rest_start:].strip()

    # 如果名字为空或过短，尝试取连续中文（但不包含去/回/出/收）
    if not name or len(name) < 2:
        # 逐个字符收集，遇到去/回/出/收就停
        alt_name = []
        for ch in section:
            if ch in ('去', '回', '出', '收', '（', '('):
                break
            if ch == ' ' or ch == '\u3000':
                break
            if '\u4e00' <= ch <= '\u9fff' or ch.isalnum():
                alt_name.append(ch)
            else:
                break
        if alt_name:
            name = ''.join(alt_name)
            rest = section[len(name):].strip()
        else:
            name = ""
            rest = section

    return name, rest


def _split_car_text_into_sections(clean_text: str) -> List[str]:
    """
    将清洗后的车次文本按客户分隔符拆分为段落。
    智能处理：以去/回/出/收开头的token归为架子信息，合并到前一个客户。
    """
    text = clean_text.strip()
    if not text:
        return []

    # 1. 显式分隔符 ➕ ＋ +
    for sep in ['➕', '＋', '+']:
        text = text.replace(sep, '|SEP|')

    if '|SEP|' in text:
        return [p.strip() for p in text.split('|SEP|') if p.strip()]

    # 2. 逗号分割（中文或英文）
    for sep in ['，', ',']:
        parts = [p.strip() for p in text.split(sep) if p.strip()]
        if len(parts) > 1:
            valid_parts = []
            all_valid = True
            for p in parts:
                name, _ = _extract_customer_name_and_rest(p)
                if name and len(name) >= 2:
                    valid_parts.append(p)
                else:
                    all_valid = False
                    break
            if all_valid:
                return valid_parts

    # 3. 空格分割（智能合并架子信息）
    tokens = text.split()
    if len(tokens) <= 1:
        return [text]

    sections = []
    current = tokens[0]

    for token in tokens[1:]:
        if not token:
            continue
        first_ch = token[0]
        if first_ch in ('去', '回', '出', '收', '（', '('):
            # 架子信息，合并到当前客户
            current += " " + token
        else:
            # 可能是新客户：必须有中文名
            name, rest = _extract_customer_name_and_rest(token)
            if name and len(name) >= 2 and '\u4e00' <= name[0] <= '\u9fff':
                # 确实是新客户
                sections.append(current)
                current = token
            else:
                # 可能也是架子信息（数字开头等）
                current += " " + token

    if current:
        sections.append(current)

    # 检查是否真的有多客户
    if len(sections) > 1:
        # 验证每个section都有客户名
        valid = []
        for s in sections:
            name, _ = _extract_customer_name_and_rest(s)
            if name and len(name) >= 2:
                valid.append(s)
            else:
                # 没有客户名→合并到前一个
                if valid:
                    valid[-1] += " " + s
                else:
                    valid.append(s)
        if len(valid) > 1:
            return valid
        return [text]

    return [text]


# ============================================================
#  司机消息解析器
# ============================================================

class DriverMessageParser:
    """
    正向解析司机消息，对标 MiniMax Code。
    """

    def __init__(self, driver_types: dict = None, riders: list = None,
                 special_places: list = None, year: str = None,
                 name_corrections: dict = None):
        self.driver_types = driver_types or DEFAULT_DRIVER_TYPES
        self.riders = set(riders or RIDERS)
        self.special_places = set(special_places or SPECIAL_PLACES)
        self.year = year or DEFAULT_YEAR

        self.all_drivers = set(self.driver_types.keys())
        self.name_corrections = name_corrections or NAME_CORRECTIONS

    def _correct_name(self, text: str) -> str:
        for wrong, correct in self.name_corrections.items():
            text = text.replace(wrong, correct)
        return text

    def _find_date(self, text: str) -> Optional[str]:
        m = RE_DATE.search(text)
        if m:
            month = m.group(1)
            day = m.group(2)
            return f"{self.year}/{int(month)}/{int(day)}"
        return None

    def _find_driver(self, text: str) -> Optional[str]:
        for name in sorted(self.all_drivers, key=len, reverse=True):
            if name in text:
                return name
        return None

    def _find_riders(self, text: str) -> list:
        found = []
        for rider in self.riders:
            if rider in text:
                found.append(rider)
        return found

    def _has_no_rider(self, text: str) -> bool:
        return "（无跟车）" in text or "(无跟车)" in text

    def _get_driver_type(self, driver: str, car_text: str) -> str:
        """获取司机类型。如果该车文本中有(中空)标记，则覆盖为中空货"""
        if _has_zhongkong(car_text):
            return "中空货"
        return self.driver_types.get(driver, "单片货")

    def _clean_for_parse(self, car_text: str, driver: str) -> str:
        """
        清洗车次文本，去除干扰信息，保留客户名和架子信息。
        """
        t = car_text

        # 去除车号标记
        t = RE_CHEHAO.sub('', t)

        # 去除日期标记
        t = RE_DATE.sub('', t)

        # 去除司机名
        if driver:
            t = t.replace(driver, '')

        # 去除 "中空货-" "单片货-" 前缀
        t = re.sub(r'^(中空货|单片货)[-：:]?', '', t)

        # 去除 (跟车...) (无跟车) 标记
        t = re.sub(r'[（(]跟车[^）)]*[）)]', '', t)
        t = re.sub(r'[（(]无跟车[）)]', '', t)

        # 去除首尾冒号逗号空格
        t = t.strip().lstrip('：:，,。、').strip()

        # 去除前置"姓名"等干扰
        t = re.sub(r'^姓名\s*[,，]?\s*', '', t)

        # 去除 "中空：" "中空：" 前缀
        t = re.sub(r'^中空[：:]?\s*', '', t)

        return t.strip()

    def parse(self, text: str) -> dict:
        """
        主解析入口。
        返回:
        {
            "date": "2026/7/9",
            "driver": "宋江鸿",
            "riders": ["罗勇"],
            "rows": [RowData, ...],
        }
        """
        # 1. 纠错姓名
        text = self._correct_name(text)

        # 2. 元数据
        date_str = self._find_date(text)
        driver = self._find_driver(text)
        riders_found = self._find_riders(text)
        has_no_rider = self._has_no_rider(text)
        has_rider = len(riders_found) > 0 and not has_no_rider

        if not date_str:
            date_str = f"{self.year}/?/?"

        # 年月格式: "2026-07"
        date_parts = date_str.split('/')
        year_month = f"{date_parts[0]}-{int(date_parts[1]):02d}"

        # 3. 按行拆分车次
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        # 去除零宽空格等不可见字符
        lines = [re.sub(r'[\u200b\u200c\u200d\ufeff]', '', l) for l in lines]

        cars_raw = []
        current_car_text = None
        current_car_original = None
        current_car_name = None

        for line in lines:
            che_match = RE_CHEHAO.search(line)
            if che_match:
                if current_car_name:
                    cars_raw.append((current_car_name, current_car_text, current_car_original))

                cn_num = che_match.group(1)
                current_car_name = f"第{cn_num}车"
                current_car_text = line
                current_car_original = line
            else:
                if current_car_text is not None:
                    current_car_text += "\n" + line
                    current_car_original += "\n" + line

        if current_car_name:
            cars_raw.append((current_car_name, current_car_text, current_car_original))

        # 4. 逐车解析
        rows: List[RowData] = []
        seq = 0
        first_car_for_driver = True

        for car_name, car_text, car_original in cars_raw:
            clean_text = self._clean_for_parse(car_text, driver)

            if not clean_text.strip():
                continue

            sections = _split_car_text_into_sections(clean_text)

            # 解析每个客户
            parsed_customers = []
            for section in sections:
                cust_name, rest = _extract_customer_name_and_rest(section)

                if not cust_name or len(cust_name) < 2:
                    continue

                # 跳过司机名/跟车名
                if cust_name in self.all_drivers or cust_name in self.riders:
                    continue

                has_zk = _has_zhongkong(rest) or _has_zhongkong(section)
                has_qyj = _has_quyijian(rest) or _has_quyijian(section)

                # 提取架子
                if has_qyj and not _has_shelf_info(rest):
                    shelves = []  # 去一件无架子
                else:
                    shelves = _extract_shelves(rest)

                is_special = cust_name in self.special_places

                parsed_customers.append({
                    "name": cust_name,
                    "shelves": shelves,
                    "has_quyijian": has_qyj,
                    "has_zhongkong": has_zk,
                    "is_special": is_special,
                    "has_shelf_info": len(shelves) > 0 or _has_shelf_info(rest),
                })

            if not parsed_customers:
                continue

            # 确定该车类型
            car_driver_type = self._get_driver_type(driver, car_text)

            # 拼车列表: 所有后续客户名，排除不生成行(无架子)的
            carpool_names = []
            for pc in parsed_customers[1:]:
                # 排除不生成行的: 去一件无架子 / 特殊地点无架子
                if pc["has_quyijian"] and not pc["has_shelf_info"]:
                    continue
                if pc["is_special"] and not pc["has_shelf_info"]:
                    continue
                carpool_names.append(pc["name"])
            carpool_str = ",".join(carpool_names)

            # 原始数据列 — 原样保留，不构造
            if first_car_for_driver:
                # 取原始块中的日期行 + 姓名行 + 第一车原文
                raw_lines = text.strip().split('\n')
                date_line = ""
                name_line = ""
                for rl in raw_lines:
                    rls = rl.strip()
                    if not rls:
                        continue
                    # 跳过时间戳行（含有HH:MM:SS格式）
                    if re.search(r'\d+:\d+:\d+', rls):
                        continue
                    if re.match(r'\d{1,2}\s*月', rls) and not date_line:
                        date_line = rls
                    elif any(d in rls for d in self.all_drivers) and not name_line:
                        name_line = rls
                raw_data = f"{date_line}\n{name_line}\n{car_original.strip()}"
            else:
                raw_data = car_original.strip()

            for idx, pc in enumerate(parsed_customers):
                is_first = (idx == 0)
                name = pc["name"]
                shelves = pc["shelves"]
                has_qyj = pc["has_quyijian"]
                is_special = pc["is_special"]
                has_shelf_info = pc["has_shelf_info"]

                actual_type = car_driver_type
                if pc["has_zhongkong"]:
                    actual_type = "中空货"

                if is_first:
                    # ---- 主行 ----
                    seq += 1
                    row = RowData()
                    row.年月 = year_month
                    row.日期 = date_str
                    row.姓名 = driver or ""
                    row.类型 = actual_type
                    row.客户 = name
                    row.数量 = "1"
                    row.拼车 = carpool_str
                    row.车号 = car_name
                    row.流水号 = str(seq)
                    row.跟车 = ", ".join(riders_found) if has_rider and not has_no_rider else ""
                    row.原始数据 = raw_data
                    rows.append(row)
                    first_car_for_driver = False

                    # ---- 架子行 ----
                    for st, sc in shelves:
                        seq += 1
                        s = RowData()
                        s.年月 = year_month
                        s.日期 = date_str
                        s.姓名 = driver or ""
                        s.类型 = st
                        s.客户 = name
                        s.数量 = str(sc)
                        s.车号 = car_name
                        s.流水号 = str(seq)
                        rows.append(s)
                else:
                    # ---- 后续客户: 仅架子行 ----
                    if is_special and not has_shelf_info:
                        continue
                    if has_qyj and not has_shelf_info:
                        continue
                    for st, sc in shelves:
                        seq += 1
                        s = RowData()
                        s.年月 = year_month
                        s.日期 = date_str
                        s.姓名 = driver or ""
                        s.类型 = st
                        s.客户 = name
                        s.数量 = str(sc)
                        s.车号 = car_name
                        s.流水号 = str(seq)
                        rows.append(s)

        return {
            "date": date_str,
            "driver": driver or "",
            "riders": riders_found,
            "rows": rows,
        }


# ============================================================
#  输出格式化
# ============================================================

def format_tsv(rows: List[RowData]) -> str:
    """输出制表符分隔文本"""
    if not rows:
        return "\t".join(RowData.header())
    lines = ["\t".join(RowData.header())]
    for r in rows:
        lines.append("\t".join(r.to_list()))
    return "\n".join(lines)


def format_report_text(rows: List[RowData], date_str: str) -> str:
    """
    生成完整报告文本，对标 MiniMax Code 输出格式。
    """
    if not rows:
        return f"=== {date_str} 台账 ===\n总计: 0 行\n"

    # 司机汇总（保留输入顺序）
    driver_counts = {}
    drivers_order = []
    for r in rows:
        if r.姓名:
            if r.姓名 not in driver_counts:
                drivers_order.append(r.姓名)
            driver_counts[r.姓名] = driver_counts.get(r.姓名, 0) + 1

    lines = []
    lines.append(f"=== {date_str} 台账 ===")
    lines.append(f"总计: {len(rows)} 行")
    lines.append("")
    lines.append("=== 司机汇总 ===")
    for d in drivers_order:
        lines.append(f"{d}: {driver_counts[d]} 行")
    lines.append("")
    lines.append("=== 制表符文本 ===")
    lines.append(format_tsv(rows))

    return "\n".join(lines)


# ============================================================
#  便捷函数
# ============================================================

def parse_driver_message(text: str, year: str = DEFAULT_YEAR,
                         driver_types: dict = None,
                         riders: list = None,
                         special_places: list = None,
                         name_corrections: dict = None) -> dict:
    """解析司机消息，返回包含日期、司机、跟车和行的字典
    支持自定义司机类型、跟车名单等配置
    """
    parser = DriverMessageParser(
        year=year,
        driver_types=driver_types,
        riders=riders,
        special_places=special_places,
        name_corrections=name_corrections,
    )
    return parser.parse(text)


def parse(text: str, year: str = DEFAULT_YEAR) -> List[RowData]:
    """解析司机消息，返回 RowData 列表（兼容旧接口）"""
    parser = DriverMessageParser(year=year)
    result = parser.parse(text)
    return result["rows"]


if __name__ == "__main__":
    sample = ("7月9号 邓亚雄\n"
              "第一车 :  希罗米 去4小回5小\n"
              "第二车 : 新翡翠 去4小回5小\n"
              "第三车 :  希罗米 去4小回5小\n"
              "第四车 :  宜点  去4小回0\n"
              "第五车 :  发物流 去1大2小回2小")
    result = parse_driver_message(sample)
    print(f"日期: {result['date']}, 司机: {result['driver']}, 跟车: {result['riders']}")
    print(f"行数: {len(result['rows'])}")
    for row in result['rows']:
        print("|".join(row.to_list()))
    print("\n" + format_report_text(result['rows'], result['date']))
