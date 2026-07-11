"""快速测试 robust_parser"""
import sys
sys.path.insert(0, r"E:/projects/new-freight-exe")
from robust_parser import parse_driver_message, format_report_text

# 测试1: 邓亚雄（中空货 + 罗勇跟车 + 回0）
sample1 = """7月9号 邓亚雄
第一车 :  希罗米 去4小回5小
第二车 : 新翡翠 去4小回5小
第三车 :  希罗米 去4小回5小
第四车 :  宜点  去4小回0
第五车 :  发物流 去1大2小回2小"""

result1 = parse_driver_message(sample1)
print("=" * 60)
print("测试1: 邓亚雄")
print(f"日期: {result1['date']}, 司机: {result1['driver']}, 跟车: {result1['riders']}")
print(f"行数: {len(result1['rows'])}")
for row in result1['rows']:
    print(" | ".join(row.to_list()))
print()
print("--- 报告 ---")
print(format_report_text(result1['rows'], result1['date']))

# 测试2: 陈俞任多客户（含拼接、去一件）
sample2 = """7月9号 陈俞任
第一车 希欧 去4小回1小
第二车 百诺森 去1大1小
第三车 宜点 去1大3小回3小
第四车 宜点 去1大3小回2小
第五车 互盈 去1小回1小  小麦 去1件玻璃  发物流 去2大回1大5小"""

result2 = parse_driver_message(sample2)
print("\n" + "=" * 60)
print("测试2: 陈俞任")
print(f"日期: {result2['date']}, 司机: {result2['driver']}, 跟车: {result2['riders']}")
print(f"行数: {len(result2['rows'])}")
for row in result2['rows']:
    print(" | ".join(row.to_list()))

# 测试3: 宋江鸿多车
sample3 = """7月9号 宋江鸿
第一车 晶彩去3小回3小
第二车 亿昌去1大回1大3小
第三车 凯旋去1大2小回2小
第四车 美亿佳去4小回1大4小
第五车 晶科达去4小回4小➕越莱顺回2大10小
第六车 凯旋去2小回1小➕鑫远去1小
第七车 安昊去2大回1大"""

result3 = parse_driver_message(sample3)
print("\n" + "=" * 60)
print("测试3: 宋江鸿")
print(f"行数: {len(result3['rows'])}")
for row in result3['rows']:
    print(" | ".join(row.to_list()))

# 测试4: 方远为（出→去）
sample4 = """7月9号 方远为
第一车 ，打沙出1小+汇兴出3小回2大5小
第二车 ，润亚森出1大1小回1大1小
第三车 ，美艺佳出4小回4小
第四车 ，豪昇出3小回7小
第五车 ，晶彩出1大2小回1大3小
第六车 ，华盛出3小回2小"""

result4 = parse_driver_message(sample4)
print("\n" + "=" * 60)
print("测试4: 方远为 (出→去)")
print(f"行数: {len(result4['rows'])}")
for row in result4['rows']:
    print(" | ".join(row.to_list()))

# 测试5: 王新建（带空格的架子）
sample5 = """7月9号 王新建
第一车 ：晶科达去4小
第二车 ：美亿佳去 2 小回4 小
第三车 ：好帝去4小回1大1 小
第四车 ：创亿去4 小回 2 小
第五车 ：豪昇去4小回9 小
第六车 ：鸿昌去1大 3小"""

result5 = parse_driver_message(sample5)
print("\n" + "=" * 60)
print("测试5: 王新建 (空格架子)")
print(f"行数: {len(result5['rows'])}")
for row in result5['rows']:
    print(" | ".join(row.to_list()))

print("\n✅ 所有测试完成")
