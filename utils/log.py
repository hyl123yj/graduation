def login_user(db, username, password):
    """
    用户登录
    :param db: 数据库连接对象
    :param username: 用户名
    :param password: 密码
    :return: 登录成功返回 True，否则返回 False
    """
    # 查询用户信息
    query = "SELECT * FROM user WHERE name = %s AND password = %s"
    result = db.execute_query(query, (username, password))
    if result:
        print("登录成功！")
        return True
    else:
        print("用户名或密码错误。")
        return False