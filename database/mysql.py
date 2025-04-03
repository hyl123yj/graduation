import pymysql
from PyQt5.QtWidgets import QMessageBox
from pymysql.cursors import DictCursor

class MySQLConnector:
    def __init__(self, host, user, password, database):
        """
        初始化数据库连接
        :param host: 数据库地址
        :param user: 用户名
        :param password: 密码
        :param database: 数据库名称
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        """
        连接到MySQL数据库
        """
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=DictCursor  # 返回字典形式的结果
            )
            print("数据库连接成功！")
            return True
        except pymysql.MySQLError as e:
            print(f"数据库连接失败: {e}")
            return False

    def disconnect(self):
        """
        关闭数据库连接
        """
        if self.connection:
            self.connection.close()
            print("数据库连接已关闭。")

    def execute_query(self, query, params=None):
        """
        执行查询语句
        :param query: SQL查询语句
        :param params: 查询参数（可选）
        :return: 查询结果（列表形式）
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"查询执行失败: {e}")
            return None

    def execute_update(self, query, params=None):
        """
        执行更新语句（插入、更新、删除）
        :param query: SQL更新语句
        :param params: 更新参数（可选）
        :return: 受影响的行数
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()  # 提交事务
                return cursor.rowcount
        except pymysql.MySQLError as e:
            self.connection.rollback()  # 回滚事务
            print(f"更新执行失败: {e}")
            return 0

    def check_connection(self):
        """
        检查数据库连接是否正常
        :return: 连接成功返回 True，失败返回 False
        """
        try:
            # 尝试连接数据库
            self.connect()
            if self.connection:
                # 执行一个简单的查询（例如查询数据库版本）
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    result = cursor.fetchone()
                    print(f"数据库连接正常，数据库版本: {result['VERSION()']}")
                return True
        except pymysql.MySQLError as e:
            print(f"数据库连接异常: {e}")
            return False


