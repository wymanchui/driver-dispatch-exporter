"""最终验证 - 只用文本对比"""
import sys, os
sys.path.insert(0, r"E:/projects/new-freight-exe")
from robust_parser import parse_driver_message, format_report_text, RowData

all_drivers_text = """7月9号 陈俞任 张信海
第一车 希欧 去4小回1小
第二车 百诺森 去1大1小
第三车 宜点 去1大3小回3小
第四车 宜点 去1大3小回2小
第五车 互盈 去1小回1小  小麦 去1件玻璃  发物流 去2大回1大5小

7月9号 帅文晓
第一车 ：宜点去4小回1大6小
第二车 ：奥合去2大回0
第三车 ：星格丽去3小回3小，铝霸去1小回1小
第四车 ：帝一去4小回4小
第五车 ：喜居安去1小回1小，唯家思去1大回1大，兴泰物流园

7月9号 邓亚雄
第一车 :  希罗米 去4小回5小
第二车 : 新翡翠 去4小回5小
第三车 :  希罗米 去4小回5小
第四车 :  宜点  去4小回0
第五车 :  发物流 去1大2小回2小

7月9号 宋江鸿
第一车 晶彩去3小回3小
第二车 亿昌去1大回1大3小
第三车 凯旋去1大2小回2小
第四车 美亿佳去4小回1大4小
第五车 晶科达去4小回4小➕越莱顺回2大10小
第六车 凯旋去2小回1小➕鑫远去1小
第七车 安昊去2大回1大

7月9号 王新建
第一车 ：晶科达去4小
第二车 ：美亿佳去 2 小回4 小
第三车 ：好帝去4小回1大1 小
第四车 ：创亿去4 小回 2 小
第五车 ：豪昇去4小回9 小
第六车 ：鸿昌去1大 3小

7月9号 方远为
第一车 ，打沙出1小+汇兴出3小回2大5小
第二车 ，润亚森出1大1小回1大1小
第三车 ，美艺佳出4小回4小
第四车 ，豪昇出3小回7小
第五车 ，晶彩出1大2小回1大3小
第六车 ，华盛出3小回2小"""

results = []
all_rows = []
total = 0
for text in all_drivers_text.strip().split("\n\n"):
    text = text.strip()
    if not text:
        continue
    r = parse_driver_message(text)
    results.append(r)
    all_rows.extend(r["rows"])
    total += len(r["rows"])
    print(f"  {r['driver']}: {len(r['rows'])} 行")

print(f"\n总计: {total} 行")

first_date = results[0]["date"]
full_report = format_report_text(all_rows, first_date)

# 保存 TXT
save_dir = r"C:\Users\ADMIN\Desktop\每天司机数据\2026-07-09"
os.makedirs(save_dir, exist_ok=True)
txt_path = os.path.join(save_dir, "new_freight_output_0709.txt")
with open(txt_path, "w", encoding="utf-8") as f:
    f.write(full_report)
print(f"已保存: {txt_path}")

# 保存 XLSX (通过 subprocess 调用 pip-installed python)
import subprocess
script = """
import sys
sys.path.insert(0, 'E:/projects/new-freight-exe')
from robust_parser import parse_driver_message, format_report_text, RowData
import openpyxl, os

all_drivers_text = '''7月9号 陈俞任 张信海
第一车 希欧 去4小回1小
第二车 百诺森 去1大1小
第三车 宜点 去1大3小回3小
第四车 宜点 去1大3小回2小
第五车 互盈 去1小回1小  小麦 去1件玻璃  发物流 去2大回1大5小

7月9号 帅文晓
第一车 ：宜点去4小回1大6小
第二车 ：奥合去2大回0
第三车 ：星格丽去3小回3小，铝霸去1小回1小
第四车 ：帝一去4小回4小
第五车 ：喜居安去1小回1小，唯家思去1大回1大，兴泰物流园

7月9号 邓亚雄
第一车 :  希罗米 去4小回5小
第二车 : 新翡翠 去4小回5小
第三车 :  希罗米 去4小回5小
第四车 :  宜点  去4小回0
第五车 :  发物流 去1大2小回2小

7月9号 宋江鸿
第一车 晶彩去3小回3小
第二车 亿昌去1大回1大3小
第三车 凯旋去1大2小回2小
第四车 美亿佳去4小回1大4小
第五车 晶科达去4小回4小➕越莱顺回2大10小
第六车 凯旋去2小回1小➕鑫远去1小
第七车 安昊去2大回1大

7月9号 王新建
第一车 ：晶科达去4小
第二车 ：美亿佳去 2 小回4 小
第三车 ：好帝去4小回1大1 小
第四车 ：创亿去4 小回 2 小
第五车 ：豪昇去4小回9 小
第六车 ：鸿昌去1大 3小

7月9号 方远为
第一车 ，打沙出1小+汇兴出3小回2大5小
第二车 ，润亚森出1大1小回1大1小
第三车 ，美艺佳出4小回4小
第四车 ，豪昇出3小回7小
第五车 ，晶彩出1大2小回1大3小
第六车 ，华盛出3小回2小'''

results = []
all_rows = []
for text in all_drivers_text.strip().split('\\n\\n'):
    text = text.strip()
    if not text:
        continue
    r = parse_driver_message(text)
    results.append(r)
    all_rows.extend(r['rows'])

first_date = results[0]['date']
full_report = format_report_text(all_rows, first_date)

save_dir = r'C:\\Users\\ADMIN\\Desktop\\每天司机数据\\2026-07-09'
os.makedirs(save_dir, exist_ok=True)

xlsx_path = os.path.join(save_dir, 'new_freight_0709.xlsx')
wb = openpyxl.Workbook()
ws = wb.active
ws.title = '台账'
ws.append(RowData.header())
for r in all_rows:
    ws.append(r.to_list())
wb.save(xlsx_path)
print(f'XLSX saved: {xlsx_path}')
"""
result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:200])

# 对比原版
orig_txt = r"C:\Users\ADMIN\Desktop\每天司机数据\2026-07-09\freight_output_0709.txt"
with open(orig_txt, "r", encoding="utf-8") as f:
    orig = f.read()

orig_data = [l for l in orig.strip().split("\n") if l.startswith("2026-07\t")]
new_data = [l for l in full_report.strip().split("\n") if l.startswith("2026-07\t")]
print(f"\n对比: 原版{len(orig_data)}行, 新版{len(new_data)}行")
if len(orig_data) == len(new_data):
    print("✅ 数据行数完全匹配!")
else:
    print(f"⚠️ 行数不匹配")

# 逐司机对比汇总
for line in orig.strip().split("\n"):
    if ":" in line and "行" in line and "台账" not in line and "制表符" not in line:
        if line not in full_report:
            print(f"⚠️ 丢失: {line}")
