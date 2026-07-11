"""与 MiniMax Code 输出进行对比测试"""
import sys
sys.path.insert(0, r"E:/projects/new-freight-exe")
from robust_parser import parse_driver_message, format_report_text, RowData

# 模拟 2026/7/9 原始输入（从 TXT 输出的原始数据列反推）
# 注意：每个司机的输入文本是分开的
test_cases = [
    # 陈俞任 (中空货, 张信海跟车)
    ("陈俞任", """7月9号 陈俞任 张信海
第一车 希欧 去4小回1小
第二车 百诺森 去1大1小
第三车 宜点 去1大3小回3小
第四车 宜点 去1大3小回2小
第五车 互盈 去1小回1小  小麦 去1件玻璃  发物流 去2大回1大5小""", 20),

    # 帅文小 (中空货, 无跟车)
    ("帅文小", """7月9号 帅文晓
第一车 ：宜点去4小回1大6小
第二车 ：奥合去2大回0
第三车 ：星格丽去3小回3小，铝霸去1小回1小
第四车 ：帝一去4小回4小
第五车 ：喜居安去1小回1小，唯家思去1大回1大，兴泰物流园""", 19),

    # 邓亚雄 (中空货, 罗勇跟车)
    ("邓亚雄", """7月9号 邓亚雄
第一车 :  希罗米 去4小回5小
第二车 : 新翡翠 去4小回5小
第三车 :  希罗米 去4小回5小
第四车 :  宜点  去4小回0
第五车 :  发物流 去1大2小回2小""", 15),

    # 宋江鸿 (单片货, 无跟车)
    ("宋江鸿", """7月9号 宋江鸿
第一车 晶彩去3小回3小
第二车 亿昌去1大回1大3小
第三车 凯旋去1大2小回2小
第四车 美亿佳去4小回1大4小
第五车 晶科达去4小回4小➕越莱顺回2大10小
第六车 凯旋去2小回1小➕鑫远去1小
第七车 安昊去2大回1大""", 27),

    # 王新建 (单片货, 无跟车)
    ("王新建", """7月9号 王新建
第一车 ：晶科达去4小
第二车 ：美亿佳去 2 小回4 小
第三车 ：好帝去4小回1大1 小
第四车 ：创亿去4 小回 2 小
第五车 ：豪昇去4小回9 小
第六车 ：鸿昌去1大 3小""", 18),

    # 方远为 (单片货, 无跟车)
    ("方远为", """7月9号 方远为
第一车 ，打沙出1小+汇兴出3小回2大5小
第二车 ，润亚森出1大1小回1大1小
第三车 ，美艺佳出4小回4小
第四车 ，豪昇出3小回7小
第五车 ，晶彩出1大2小回1大3小
第六车 ，华盛出3小回2小""", 24),
]

total_rows = 0
all_rows = []
all_pass = True

for name, text, expected_count in test_cases:
    result = parse_driver_message(text)
    actual = len(result["rows"])
    if actual == expected_count:
        print(f"✅ {name}: {actual} 行 (预期 {expected_count})")
        total_rows += actual
        all_rows.extend(result["rows"])
    else:
        print(f"❌ {name}: {actual} 行 (预期 {expected_count})")
        all_pass = False

print(f"\n总计: {total_rows} 行 (预期 123)")
print(f"全部通过: {'✅' if all_pass else '❌' if total_rows == 123 else '⚠️ 部分不匹配'}")

# 输出完整报告
print("\n" + "=" * 60)
report = format_report_text(all_rows, "2026/7/9")
print(report)
