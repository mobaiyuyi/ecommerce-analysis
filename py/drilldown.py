# -*- coding: utf-8 -*-
"""品类 / 地区下钻：执行 sql/GMV_Drilldown.sql -> data/GMV_Drilldown.xlsx + Img/*.png"""
import os
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_PATH = os.path.join(BASE_DIR, 'sql', 'GMV_Drilldown.sql')
XLSX_PATH = os.path.join(BASE_DIR, 'data', 'GMV_Drilldown.xlsx')
IMG_DIR = os.path.join(BASE_DIR, 'Img')

DB_URL = 'mysql+pymysql://root:root@127.0.0.1:3306/portfolio?charset=utf8mb4'

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

DOWN_COLOR, UP_COLOR = '#C0504D', '#2E7D5B'
TITLE_01_04 = '2026年1月 → 4月'


def load_queries(path):
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    # pymysql 执行前会把 % 当占位符，这里统一转义为 %%
    return [s.strip().replace('%', '%%') for s in raw.split(';') if s.strip()]


def plot_mechanism(panels, out_path):
    """量价四象限：区分「量崩」与「价崩」两种下滑机制"""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), dpi=150)
    for ax, (name, df, dim_col) in zip(axes, panels):
        colors = [DOWN_COLOR if v < 0 else UP_COLOR for v in df['GMV变化额']]
        ax.scatter(df['下单量变化'], df['客单价变化率'], c=colors, s=95,
                   zorder=3, edgecolors='white', linewidths=0.9)
        for _, r in df.iterrows():
            ax.annotate(r[dim_col], (r['下单量变化'], r['客单价变化率']),
                        textcoords='offset points', xytext=(0, 10),
                        ha='center', fontsize=9)

        ax.axhline(0, color='#808080', linewidth=0.8, linestyle='--')
        ax.axvline(0, color='#808080', linewidth=0.8, linestyle='--')
        ax.text(0.02, 0.96, '量减价升', transform=ax.transAxes, fontsize=9, color='#A6A6A6')
        ax.text(0.02, 0.04, '量价双杀', transform=ax.transAxes, fontsize=9, color='#A6A6A6')
        ax.text(0.98, 0.96, '量价双升', transform=ax.transAxes, fontsize=9, color='#A6A6A6', ha='right')
        ax.text(0.98, 0.04, '量增价崩', transform=ax.transAxes, fontsize=9, color='#A6A6A6', ha='right')

        ax.set_xlabel('下单量变化（单）')
        ax.set_ylabel('客单价变化率（%）')
        ax.set_title('%s：量价变化机制（2026年1月 → 4月）' % name)
        ax.grid(color='#D9D9D9', linewidth=0.6)
        ax.set_axisbelow(True)
        ax.margins(x=0.28, y=0.28)
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print('图表已输出：%s' % out_path)


def plot_contribution(df, dim_col, title, out_path):
    d = df.sort_values('GMV变化额')          # 最差在前
    colors = [DOWN_COLOR if v < 0 else UP_COLOR for v in d['GMV变化额']]
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    ax.barh(d[dim_col], d['GMV变化额'] / 10000, color=colors, height=0.62)

    for i, (v, share) in enumerate(zip(d['GMV变化额'], d['GMV贡献占比'])):
        offset = -0.35 if v < 0 else 0.35
        label = '%.1f万' % (v / 10000)
        if v < 0:
            label += '（%.1f%%）' % share
        ax.text(v / 10000 + offset, i, label, va='center',
                ha='right' if v < 0 else 'left', fontsize=9,
                color=DOWN_COLOR if v < 0 else UP_COLOR)

    ax.axvline(0, color='#808080', linewidth=0.8)
    ax.set_xlabel('完成订单GMV变化额（万元）')
    ax.set_title('%s 各%s完成订单GMV变化贡献' % (TITLE_01_04, title))
    ax.grid(axis='x', color='#D9D9D9', linewidth=0.6)
    ax.set_axisbelow(True)
    ax.margins(x=0.30)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print('图表已输出：%s' % out_path)


engine = create_engine(DB_URL)
queries = load_queries(SQL_PATH)
assert len(queries) == 2, '预期 2 条查询，实际 %d 条' % len(queries)

with engine.connect() as conn:
    df_cat = pd.read_sql(queries[0], conn)
    df_region = pd.read_sql(queries[1], conn)

for name, df in [('品类', df_cat), ('地区', df_region)]:
    total = df['GMV变化额'].sum()
    print('=' * 22, '%s下钻' % name)
    print(df.to_string(index=False))
    print('%s 合计变化额：%.2f 元，贡献占比合计 %.2f%%'
          % (name, total, df['GMV贡献占比'].sum()))

os.makedirs(IMG_DIR, exist_ok=True)
plot_contribution(df_cat, '商品分类', '品类', os.path.join(IMG_DIR, 'category_contribution.png'))
plot_contribution(df_region, '用户所在地区', '地区', os.path.join(IMG_DIR, 'region_contribution.png'))
plot_mechanism([('品类', df_cat, '商品分类'), ('地区', df_region, '用户所在地区')],
               os.path.join(IMG_DIR, 'drilldown_summary.png'))

with pd.ExcelWriter(XLSX_PATH, engine='openpyxl') as w:
    df_cat.to_excel(w, sheet_name='品类下钻', index=False)
    df_region.to_excel(w, sheet_name='地区下钻', index=False)
print('\n下钻结果已输出：%s' % XLSX_PATH)