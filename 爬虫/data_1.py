import requests
import pandas as pd
from bs4 import BeautifulSoup

# 目标URL
url = "https://g.hyyb.org/systems/TY/info/tcdataCMA/dlrdqx_zl.html"

# 发送HTTP请求获取网页内容
response = requests.get(url)
response.encoding = 'utf-8'  # 设置编码

# 使用BeautifulSoup解析网页内容
soup = BeautifulSoup(response.text, 'html.parser')

# 找到表格所在的标签（假设表格是第一个<table>标签）
table = soup.find('table')

# 使用pandas读取表格数据
df = pd.read_html(str(table))[0]

# 打印表格数据
print(df)

# 如果需要保存到CSV文件
df.to_csv('table_data.csv', index=False, encoding='utf-8-sig')