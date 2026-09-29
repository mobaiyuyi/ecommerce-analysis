import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import String, Integer, Float, DateTime

host = '127.0.0.1'
port = 3306
user = 'root'
password = 'root'
database = 'portfolio'
csv_path = r'D:\JupyterNoteBook\portfolio\Project4_电商\data\clear_电商销售数据.csv'

table_schema = {
    'sales_data': {
        '订单ID': String(64),
        '用户ID': String(64),
        '订单日期': DateTime(),
        '商品分类': String(64),
        '商品名称': String(64),
        '购买数量': Integer(),
        '单价': Float(),
        '订单金额': Float(),
        '支付方式': String(8),
        '用户所在地区': String(10),
        '是否促销': Integer(),
        '订单状态': String(4),
    }
}

engine = create_engine(
    f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4'
)

data = pd.read_csv(csv_path, encoding='utf-8-sig')
print(f'读取数据：{len(data)} 行 × {len(data.columns)} 列')

data['订单日期'] = pd.to_datetime(data['订单日期'], errors='coerce')
nat = int(data['订单日期'].isna().sum())
if nat > 0:
    raise ValueError(f'存在 {nat} 条无法解析的订单日期')
print('订单日期解析成功，dtype =', data['订单日期'].dtype)

for col, dtype in table_schema['sales_data'].items():
    if isinstance(dtype, String) and dtype.length and col in data.columns:
        max_len = int(data[col].astype(str).str.len().max())
        if max_len > dtype.length:
            raise ValueError(f'{col} 最大长度 {max_len} 超出字段定义 {dtype.length}')

for table, dtype in table_schema.items():
    data.to_sql(
        name=table,
        con=engine,
        if_exists='replace',
        index=False,
        dtype=dtype
    )
    print(f'{table} 导入完毕：{len(data)} 行')