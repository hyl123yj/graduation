from database.mysql import MySQLConnector
from database.database_config import db_config

# 创建连接器实例
def connect_databse():
   db = MySQLConnector(**db_config)

   # 连接到数据库
   db.connect()
   # 断开数据库
   db.disconnect()
