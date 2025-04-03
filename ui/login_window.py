import os
import sys
import re
import warnings
os.environ["PNG_SKIP_sRGB_CHECK_PROFILE"] = "1"  # 必须在导入前设置！
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox,
                             QStackedWidget, QFrame, QSizePolicy)
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QFont, QRegExpValidator
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal, QTimer, QRegExp

from database.database_config import db_config
from database.mysql import MySQLConnector  # 导入你的MySQLConnector类
from utils.register import register_user
from utils.validate import validate_username,validate_password

class LoginRegisterSystem(QWidget):
    login_success = pyqtSignal(str)  # 添加这行定义信号
    def __init__(self):
        super().__init__()
        self.setWindowTitle('台风数据可视化系统')
        self.resize(800, 600)  # 初始大小
        self.setMinimumSize(600, 450)  # 最小大小限制

        # 初始化数据库连接器
        self.db = MySQLConnector(**db_config)

        # 尝试连接数据库
        if not self.db.connect():
            QMessageBox.critical(self, '数据库错误', '无法连接到数据库，请检查配置')
            sys.exit(1)

        # 基础字体大小，将根据窗口大小调整
        self.base_font_size = 12
        self.base_padding = 12
        self.base_spacing = 20

        self.init_ui()
        self.update_styles()  # 初始样式更新

    def init_ui(self):
        # 创建堆叠窗口用于页面切换
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 创建登录页面
        self.login_page = self.create_login_page()
        # 创建注册页面
        self.register_page = self.create_register_page()

        # 添加页面到堆叠窗口
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.register_page)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

    def create_login_page(self):
        """创建登录页面"""
        self.login_page = QWidget()
        self.login_page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 主布局
        self.login_layout = QVBoxLayout(self.login_page)
        self.login_layout.setContentsMargins(50, 50, 50, 50)

        # 标题
        self.login_title = QLabel('台风数据可视化系统', self.login_page)
        self.login_title.setAlignment(Qt.AlignCenter)

        # 表单容器
        self.login_form_container = QFrame(self.login_page)
        self.login_form_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.login_form_layout = QVBoxLayout(self.login_form_container)
        self.login_form_layout.setContentsMargins(30, 30, 30, 30)

        # 用户名输入
        self.login_username = QLineEdit(self.login_form_container)
        self.login_username.setPlaceholderText('用户名')

        # 密码输入
        self.login_password = QLineEdit(self.login_form_container)
        self.login_password.setPlaceholderText('密码')
        self.login_password.setEchoMode(QLineEdit.Password)

        # 登录按钮
        self.login_btn = QPushButton('登录', self.login_form_container)
        self.login_btn.clicked.connect(self.handle_login)

        # 注册链接
        self.register_link = QLabel('<a href="#" style="text-decoration: none; color: black;">没有账号？立即注册</a>',
                                    self.login_form_container)
        self.register_link.setAlignment(Qt.AlignCenter)
        self.register_link.setOpenExternalLinks(False)
        self.register_link.linkActivated.connect(self.show_register_page)

        # 添加到表单布局
        self.login_form_layout.addWidget(self.login_username)
        self.login_form_layout.addSpacing(self.base_spacing)
        self.login_form_layout.addWidget(self.login_password)
        self.login_form_layout.addSpacing(self.base_spacing)
        self.login_form_layout.addWidget(self.login_btn)
        self.login_form_layout.addSpacing(self.base_spacing)
        self.login_form_layout.addWidget(self.register_link)

        # 主布局添加组件
        self.login_layout.addStretch()
        self.login_layout.addWidget(self.login_title)
        self.login_layout.addWidget(self.login_form_container, alignment=Qt.AlignCenter)
        self.login_layout.addStretch()

        return self.login_page

    def create_register_page(self):
        """创建带邮箱字段的注册页面"""
        self.register_page = QWidget()
        self.register_page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 主布局
        self.register_layout = QVBoxLayout(self.register_page)
        self.register_layout.setContentsMargins(50, 50, 50, 50)

        # 标题
        self.register_title = QLabel('用户注册', self.register_page)
        self.register_title.setAlignment(Qt.AlignCenter)
        self.register_title.setStyleSheet("""
            QLabel {
                font: bold 24px;
                color: #2c3e50;
                padding-bottom: 20px;
            }
        """)

        # 表单容器
        self.register_form_container = QFrame(self.register_page)
        self.register_form_container.setFrameShape(QFrame.StyledPanel)
        self.register_form_container.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
        """)
        self.register_form_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.register_form_container.setFixedWidth(400)

        self.register_form_layout = QVBoxLayout(self.register_form_container)
        self.register_form_layout.setContentsMargins(30, 30, 30, 30)
        self.register_form_layout.setSpacing(15)

        # 用户名输入
        self.register_username = QLineEdit(self.register_form_container)
        self.register_username.setPlaceholderText('用户名只能包含字母、数字和下划线')
        self._setup_line_edit_style(self.register_username)


        # 密码输入
        self.register_password = QLineEdit(self.register_form_container)
        self.register_password.setPlaceholderText('密码只能包含字母和数字，且长度应为6-15位')
        self.register_password.setEchoMode(QLineEdit.Password)
        self._setup_line_edit_style(self.register_password)

        # 确认密码
        self.register_confirm_password = QLineEdit(self.register_form_container)
        self.register_confirm_password.setPlaceholderText('确认密码')
        self.register_confirm_password.setEchoMode(QLineEdit.Password)
        self._setup_line_edit_style(self.register_confirm_password)

        # 邮箱输入
        self.register_email = QLineEdit(self.register_form_container)
        self.register_email.setPlaceholderText('电子邮箱')
        self._setup_line_edit_style(self.register_email)
        self.register_email.setValidator(QRegExpValidator(
            QRegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        ))

        # 注册按钮
        self.register_btn = QPushButton('注册', self.register_form_container)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font: bold 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.register_btn.clicked.connect(self.handle_register)

        # 返回登录链接
        self.login_link = QLabel(
            '<a href="#" style="text-decoration: none; color: black;">已有账号？返回登录</a>',
            self.register_form_container
        )
        self.login_link.setAlignment(Qt.AlignCenter)
        self.login_link.linkActivated.connect(self.show_login_page)

        # 表单组件布局
        form_items = [
            self.register_username,
            self.register_email,
            self.register_password,
            self.register_confirm_password,
            self.register_btn,
            self.login_link
        ]
        for item in form_items:
            self.register_form_layout.addWidget(item)

        # 主布局
        self.register_layout.addStretch()
        self.register_layout.addWidget(self.register_title)
        self.register_layout.addWidget(self.register_form_container, alignment=Qt.AlignCenter)
        self.register_layout.addStretch()

        return self.register_page
    def _setup_line_edit_style(self, line_edit):
        """统一设置输入框样式"""
        line_edit.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)

    def resizeEvent(self, event):
        """窗口大小改变时更新UI尺寸"""
        super().resizeEvent(event)
        self.update_styles()

    def update_styles(self):
        """根据窗口大小更新所有样式"""
        # 计算缩放因子 - 基于窗口高度和宽度的最小值
        min_dimension = min(self.width(), self.height())
        scale_factor = min_dimension / 800  # 800是我们的基准大小

        # 计算动态尺寸
        font_size = max(12, int(self.base_font_size * scale_factor * 1.2))
        padding = max(8, int(self.base_padding * scale_factor))
        spacing = max(10, int(self.base_spacing * scale_factor))
        title_font_size = max(24, int(font_size * 2))
        form_width = max(300, int(400 * scale_factor))
        radius = max(5, int(10 * scale_factor))

        # 基础样式
        base_style = f"""
            font-size: {font_size}px;
            padding: {padding}px;
        """

        # 更新登录页面样式
        self.login_title.setStyleSheet(f"""
            font-size: {title_font_size}px;
            font-weight: bold;
            color: white;
            margin-bottom: {spacing * 2}px;
        """)

        self.login_form_container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: {radius}px;
            }}
        """)
        self.login_form_container.setFixedWidth(form_width)

        input_style = f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.8);
                border-radius: {radius}px;
                padding: {padding}px;
                font-size: {font_size}px;
                border: none;
                min-height: {padding * 3}px;
            }}
        """
        self.login_username.setStyleSheet(input_style)
        self.login_password.setStyleSheet(input_style)

        btn_style = f"""
            QPushButton {{
                background-color: #3498db;
                color: white;
                border-radius: {radius}px;
                padding: {padding}px;
                font-size: {font_size}px;
                border: none;
                min-height: {padding * 3}px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
        """
        self.login_btn.setStyleSheet(btn_style)

        # 更新注册页面样式
        self.register_title.setStyleSheet(f"""
            font-size: {title_font_size}px;
            font-weight: bold;
            color: white;
            margin-bottom: {spacing * 2}px;
        """)

        self.register_form_container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: {radius}px;
            }}
        """)
        self.register_form_container.setFixedWidth(form_width)

        self.register_username.setStyleSheet(input_style)
        self.register_password.setStyleSheet(input_style)
        self.register_confirm_password.setStyleSheet(input_style)
        self.register_email.setStyleSheet(input_style)

        register_btn_style = f"""
            QPushButton {{
                background-color: #2ecc71;
                color: white;
                border-radius: {radius}px;
                padding: {padding}px;
                font-size: {font_size}px;
                border: none;
                min-height: {padding * 3}px;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
        """
        self.register_btn.setStyleSheet(register_btn_style)

        # 更新链接样式
        link_style = f"""
            font-size: {font_size}px;
            color: #3498db;
        """
        self.register_link.setStyleSheet(link_style)
        self.login_link.setStyleSheet(link_style)

        # 更新布局间距
        self.login_form_layout.setSpacing(spacing)
        self.register_form_layout.setSpacing(spacing)
        self.login_layout.setSpacing(spacing)
        self.register_layout.setSpacing(spacing)

    def paintEvent(self, event):
        """绘制渐变背景"""
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(30, 60, 90))
        gradient.setColorAt(1, QColor(10, 30, 50))
        painter.fillRect(self.rect(), gradient)

    def show_login_page(self):
        self.animate_transition(0)

    def show_register_page(self):
        self.animate_transition(1)

    def animate_transition(self, index):
        animation = QPropertyAnimation(self.stacked_widget, b"pos")
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.OutQuad)

        current_index = self.stacked_widget.currentIndex()
        if index > current_index:
            animation.setStartValue(self.stacked_widget.pos() + QPoint(-100, 0))
        else:
            animation.setStartValue(self.stacked_widget.pos() + QPoint(100, 0))

        animation.setEndValue(self.stacked_widget.pos())
        animation.start()
        self.stacked_widget.setCurrentIndex(index)

    def handle_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, '输入错误', '用户名和密码不能为空')
            return

        try:
            query = "SELECT * FROM user WHERE name = %s AND password = %s"
            result = self.db.execute_query(query, (username, password))

            if result:
                # 先发射信号，再显示消息框
                self.login_success.emit(username)
                QMessageBox.information(self, '登录成功', f'欢迎登陆, {username}!!!')

            else:
                QMessageBox.warning(self, '登录失败', '用户名或密码错误')


        except Exception as e:
            QMessageBox.critical(self, '数据库错误', f'查询失败: {e}')


    def handle_register(self):
        """处理注册逻辑"""
        username = self.register_username.text().strip()
        password = self.register_password.text().strip()
        confirm_password = self.register_confirm_password.text().strip()
        email=self.register_email.text().strip()

        if not username or not password or not confirm_password or not email:
            QMessageBox.warning(self, '输入错误', '所有字段都必须填写')
            return

        if password != confirm_password:
            QMessageBox.warning(self, '密码不匹配', '两次输入的密码不一致')
            return

        if len(password) < 6:
            QMessageBox.warning(self, '密码太短', '密码长度至少为6个字符')
            return

        if not validate_username(username):
            QMessageBox.warning(self,"用户名格式错误","用户名只能包含字母、数字和下划线")
            return

        if not validate_password(password):
            QMessageBox.warning(self,"密码格式错误","密码只能包含字母和数字，且长度不能超过15位")
            return

        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            QMessageBox.warning(self, "格式错误", "请输入有效的电子邮箱地址")
            return

        try:
            # 检查用户名是否已存在
            check_query = "SELECT * FROM user WHERE name = %s"
            result = self.db.execute_query(check_query, (username,))
            if result:
                QMessageBox.warning(self, '注册失败', '用户名已存在')
                return

            # 插入新用户
            insert_query = "INSERT INTO user (name, password,email) VALUES (%s, %s, %s)"
            affected_rows = self.db.execute_update(insert_query, (username, password,email))

            if affected_rows > 0:
                QMessageBox.information(self, '注册成功', '用户注册成功，现在可以登录了')
                self.show_login_page()
                self.register_username.clear()
                self.register_password.clear()
                self.register_confirm_password.clear()
                self.register_email.clear()
            else:
                QMessageBox.warning(self, '注册失败', '用户注册失败，请重试')



        except Exception as e:
            QMessageBox.critical(self, '数据库错误', f'注册失败: {e}')



    def closeEvent(self, event):
        """完全交由主程序控制关闭"""
        event.ignore()



   


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = LoginRegisterSystem()
    window.show()
    sys.exit(app.exec_())