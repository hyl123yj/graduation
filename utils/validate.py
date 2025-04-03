import re

def validate_username(username):
    """
    校验用户名格式
    :param username: 用户名
    :return: 校验通过返回 True，否则返回 False
    """
    pattern = r'^[a-zA-Z0-9_]+$'  # 只能包含字母、数字和下划线
    return re.match(pattern, username) is not None

def validate_password(password):
    """
    校验密码格式
    :param password: 密码
    :return: 校验通过返回 True，否则返回 False
    """
    if len(password) > 15:
        return False
    pattern = r'^[a-zA-Z0-9]+$'  # 只能包含字母和数字
    return re.match(pattern, password) is not None