# 读取CSV文件
import pandas as pd
from sqlalchemy import create_engine

data = pd.read_csv('museum_collection_modified.csv')

# 创建数据库引擎
# 请将 "username", "password", "host", "dbname" 替换为你的MySQL实际信息
engine = create_engine('mysql+pymysql://root:admin@localhost:3306/knowledge_base?charset=utf8')

# 将数据写入数据库
data.to_sql('museum_collection', engine, index=False, if_exists='append')