from utils.validate import validate_username, validate_password


def register_user(db, username, password):
    """
    注册新用户
    :param db: 数据库连接对象
    :param username: 用户名
    :param password: 密码
    :return: 注册成功返回 True，否则返回 False
    """
    # 校验用户名和密码格式
    if not validate_username(username):
        print("用户名格式错误：只能包含字母、数字和下划线。")
        return False
    if not validate_password(password):
        print("密码格式错误：只能包含字母和数字，且长度不能超过15位。")
        return False

    # 检查用户名是否已存在
    query = "SELECT * FROM user WHERE name = %s"
    result = db.execute_query(query, (username,))
    if result:
        print("用户名已存在，请选择其他用户名。")
        return False

    # 插入新用户
    query = "INSERT INTO user (name, password) VALUES (%s, %s)"
    affected_rows = db.execute_update(query, (username, password))
    if affected_rows > 0:
        print("注册成功！")
        return True
    else:
        print("注册失败，请重试。")
        return False