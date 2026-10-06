# -*- coding: utf-8 -*-
"""数据质量检查与清洗：data/电商销售数据.csv -> data/clear_电商销售数据.csv"""
import os
import pandas as pd

RAW_PATH = r'D:\JupyterNoteBook\portfolio\Project1_电商\data\电商销售数据.csv'
CLEAN_PATH = r'D:\JupyterNoteBook\portfolio\Project1_电商\data\clear_电商销售数据.csv'

VALID_STATUS = ['已完成', '待发货', '已取消', '退款中']
MIN_DATE, MAX_DATE = pd.Timestamp('2025-06-01'), pd.Timestamp('2026-05-31 23:59:59')

data = pd.read_csv(RAW_PATH, encoding='gbk')
print('原始数据规模：%d 行 × %d 列' % data.shape)

# 字段与类型
required_cols = ['订单ID', '用户ID', '订单日期', '商品分类', '商品名称', '购买数量',
                 '单价', '订单金额', '支付方式', '用户所在地区', '是否促销', '订单状态']
missing_cols = [c for c in required_cols if c not in data.columns]
assert not missing_cols, '缺失必需字段：%s' % missing_cols
print('字段完整，共 %d 列' % len(required_cols))

raw_date_str = data['订单日期'].copy()
order_dt = pd.to_datetime(raw_date_str, format='%m/%d/%Y %H:%M', errors='coerce')
assert order_dt.notna().all(), '存在无法解析的订单日期'
print('订单日期解析成功，每行均有日期值')

# 缺失值
null_cnt = data.isnull().sum()
if null_cnt.sum() > 0:
    print('存在缺失值，分布如下：')
    print(null_cnt[null_cnt > 0].to_string())
else:
    print('无缺失值')

# 重复值
dup_row = int(data.duplicated().sum())
dup_id = int(data['订单ID'].duplicated().sum())
print('完全重复行：%d 行' % dup_row)
print('订单ID重复：%d 个' % dup_id)
assert dup_id == 0, '订单ID不唯一'

before = len(data)
if dup_row > 0:
    data = data.drop_duplicates()
    print('去重完成：%d 行 → %d 行' % (before, len(data)))
else:
    print('无重复行')

# 取值合法性
bad_status = set(data['订单状态'].unique()) - set(VALID_STATUS)
assert not bad_status, '订单状态存在未定义取值：%s' % bad_status
bad_promo = set(data['是否促销'].unique()) - {0, 1}
assert not bad_promo, '是否促销存在非 0/1 取值：%s' % bad_promo
assert set(data['订单ID'].astype(str).str[:3]) == {'ORD'}, '订单ID 前缀不符合 ORD 规则'
print('订单状态、是否促销、订单ID 前缀取值均在定义范围内')

# 数值合理性
for col in ['购买数量', '单价', '订单金额']:
    bad = int((data[col] <= 0).sum())
    assert bad == 0, '%s 存在 %d 条非正值' % (col, bad)
    print(' %s 全部为正数，范围 %.2f ~ %.2f' % (col, data[col].min(), data[col].max()))

out_of_range = data[(order_dt < MIN_DATE) | (order_dt > MAX_DATE)]
assert len(out_of_range) == 0, '存在 %d 条订单日期超出 2025-06-01~2026-05-31 范围' % len(out_of_range)
print('订单日期全部落在 2025-06-01 ~ 2026-05-31（%s ~ %s）'
      % (order_dt.min().date(), order_dt.max().date()))

# 标价（单价 × 购买数量）与实付金额的差异
TOL = 0.05
tag_price = data['单价'] * data['购买数量']
diff = data['订单金额'] - tag_price

promo = data['是否促销'] == 1
disc = diff < -TOL                      # 实付明显低于标价
over = diff > TOL                       # 实付明显高于标价
full = diff.abs() <= TOL                # 实付 = 标价

promo_not_disc = int((promo & ~disc).sum())   # 标为促销却无折扣
nonpromo_disc = int((~promo & disc).sum())    # 未标促销却打折
over_cnt = int(over.sum())                    # 实付高于标价
disc_min = float(diff[disc].abs().min()) if disc.any() else 0.0
print('折扣单的最小折扣额 %.2f 元' % disc_min)

print('实付 = 标价（全价单）：%d 行' % int(full.sum()))
print('实付 < 标价（折扣单）：%d 行' % int(disc.sum()))
print('实付 > 标价（异常）  ：%d 行' % over_cnt)
print('标为促销但未打折     ：%d 行' % promo_not_disc)
print('未标促销但打了折     ：%d 行' % nonpromo_disc)

promo_mean = data.loc[promo, '订单金额'].mean()
nonpromo_mean = data.loc[~promo, '订单金额'].mean()
print('促销单平均实付 %.2f 元，非促销单平均实付 %.2f 元' % (promo_mean, nonpromo_mean))
assert promo_mean < nonpromo_mean, '促销单平均实付不低于非促销单，促销标记逻辑存疑'

promo_ratio = (data.loc[promo, '订单金额'] / tag_price[promo])
print('促销单折扣率范围 %.4f ~ %.4f' % (promo_ratio.min(), promo_ratio.max()))

if over_cnt == 0 and promo_not_disc == 0:
    print('「是否促销」与实付金额自洽：无实付高于标价的记录，促销单全部享受折扣')
    if nonpromo_disc > 0:
        print('       另有 %d 行（%.1f%%）未标记促销但实付低于标价，幅度均在 %.2f 元以内'
              % (nonpromo_disc, nonpromo_disc / max(int(disc.sum()), 1) * 100,
                 float(diff[~promo & disc].abs().max())))
else:
    print('「是否促销」与实付金额存在矛盾（实付高于标价 %d 行，促销单未打折 %d 行）'
          % (over_cnt, promo_not_disc))

# 订单ID 内嵌日期与订单日期是否一致
embedded = pd.to_datetime(data['订单ID'].astype(str).str[3:11], format='%Y%m%d', errors='coerce')
mismatch = int((embedded.dt.date != order_dt.dt.date).sum())
assert mismatch == 0, '订单ID 内嵌日期与订单日期有 %d 行不一致' % mismatch
print('订单ID 内嵌日期与订单日期 100%% 一致（%d 行全量校验）' % len(data))

# 订单金额分布（仅观察，不做剔除）
q1, q3 = data['订单金额'].quantile([0.25, 0.75])
iqr = q3 - q1
upper = q3 + 1.5 * iqr
outliers = int((data['订单金额'] > upper).sum())
print(' 按 IQR 规则，订单金额 > %.2f 的高值订单 %d 行（占 %.1f%%）'
      % (upper, outliers, outliers / len(data) * 100))
print('订单金额偏度 %.2f，呈右偏分布，保留不剔除' % data['订单金额'].skew())

# 输出
os.makedirs(os.path.dirname(CLEAN_PATH), exist_ok=True)
data.to_csv(CLEAN_PATH, index=False, encoding='utf-8-sig')
print('\n清洗后数据已输出：%s' % CLEAN_PATH)
print('输出规模：%d 行 × %d 列' % data.shape)
print('\n各订单状态分布：')
print(data['订单状态'].value_counts().to_string())