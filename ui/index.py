import os
import sys
import warnings
os.environ["PNG_SKIP_sRGB_CHECK_PROFILE"] = "1"  # 必须在导入前设置！
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fontTools.merge import layout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QToolBar, QAction, QStackedWidget, QVBoxLayout,
                             QMenuBar, QMenu, QStatusBar, QMessageBox, QLayout, QSizePolicy, QDialog, QScrollArea,
                             QHBoxLayout, QTextBrowser, QPushButton, QFrame, QShortcut, QFormLayout, QLineEdit,
                             QDoubleSpinBox, QDateEdit, QDialogButtonBox)
from PyQt5.QtGui import QIcon, QFont, QKeySequence
from PyQt5.QtCore import Qt, QSize

import matplotlib.pyplot as plt
from matplotlib import rcParams
from mpl_toolkits.basemap import Basemap

from database.database_config import db_config
from database.mysql import MySQLConnector
from ui.ground import WeatherBackground
from visualization.land import TyphoonMapWidget

class MplCanvas(FigureCanvas):
    """Matplotlib画布封装类"""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)


class TyphoonAnalysisSystem(QMainWindow):
    def __init__(self, username):
        super().__init__()
        # 在创建主窗口类之前添加字体设置
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']  # 设置中文显示
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        rcParams['font.size'] = 12  # 设置默认字体大小
        self.username = username
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        self.db=MySQLConnector(**db_config)
        # 尝试连接数据库
        if not self.db.connect():
            QMessageBox.critical(self, '数据库错误', '无法连接到数据库，请检查配置')
            sys.exit(1)

        # 模拟台风数据
        self.typhoon_data = self.generate_sample_data()

        # 初始化UI
        self.init_ui()

    def init_ui(self):

        # 设置中心窗口
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 创建堆叠窗口用于切换不同图表
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.setStyleSheet("""
               QMainWindow {
                   background: qlineargradient(
                       x1:0, y1:0, x2:1, y2:1,
                       stop:0 #0a1f3a,  /* 深海蓝 */
                       stop:0.5 #1a3a6e, /* 风暴蓝 */
                       stop:1 #0c2d52    /* 夜空蓝 */
                   );
                   border: 1px solid #2a5278;
               }

               /* 状态栏样式 */
               QStatusBar {
                   background: rgba(10, 31, 58, 0.7);
                   color: #b0c4de;
                   font: 10pt "微软雅黑";
                   border-top: 1px solid #2a5278;
               }
               /* 菜单栏样式 */
               QMenuBar {
                   background: rgba(16, 42, 87, 0.9);
                   color: #d9e3f0;
                   border-bottom: 1px solid #3a6ea5;
                   font: 11pt "微软雅黑";
               }
               QMenuBar::item:selected {
                   background: #3a6ea5;
               }
               /* 堆叠窗口背景透明 */
               QStackedWidget {
                   background: transparent;
               }
           """)

        # 初始化所有可视化图表
        self.init_charts()

        # 默认显示第一个图表
        self.switch_chart(0)

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 数据分析菜单
        analysis_menu = menubar.addMenu('📈 数据分析')
        analysis_menu.setStyleSheet("""
                               QMenu {
                                   background: #142b54;
                                   color: #c0d0e8;
                                   border: 1px solid #3a6ea5;
                               }
                               QMenu::item:selected {
                                   background: #2a5278;
                               }
                           """)

        # 分析菜单项
        analysis_actions = [
            ("路径分析", "显示台风路径数据", 0),
            ("强度分析", "显示台风强度变化", 1),
            ("频率分析", "显示台风发生频率", 2),
            ("预测分析", "显示台风预测模型", 3),
            ("影响范围", "显示台风影响范围", 4),
            ("历史对比", "显示历史台风对比", 5)
        ]
        analysis_icons = {
            0: "🌀",  # 路径
            1: "🌊",  # 强度
            2: "📊",  # 频率
            3: "🔮",  # 预测
            4: "🗺️",  # 范围
            5: "⏳"  # 历史
        }
        for idx, (name, tip, _) in enumerate(analysis_actions):
            action = QAction(f"{analysis_icons.get(idx, '')} {name}", self)
            action.setStatusTip(tip)
            action.triggered.connect(lambda checked, i=idx: self.switch_chart(i))
            analysis_menu.addAction(action)


        # 帮助菜单
        #help_menu = menubar.addMenu('帮助')
        #about_action = QAction('关于', self)
        #about_action.triggered.connect(self.show_about)
        #help_menu.addAction(about_action)

        # 帮助菜单（带气象图标和悬浮效果）
        help_menu = menubar.addMenu('✋ 帮助')  # 使用求救符号图标
        help_menu.setStyleSheet("""
            QMenu {
                background: #142b54;
                color: #c0d0e8;
                border: 1px solid #3a6ea5;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 25px 5px 10px;
            }
            QMenu::item:selected {
                background: #2a5278;
                color: #ffffff;
            }
        """)

        # 关于动作（带图标和快捷键）
        about_action = QAction('📝 关于系统', self)
        about_action.setStatusTip("查看系统版本和开发者信息")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # 刷新菜单
        refresh_menu = menubar.addMenu('🔄 数据')  # 使用循环箭头符号
        refresh_menu.setStyleSheet("""
            QMenu {
                background: #142b54;
                color: #c0d0e8;
                border: 1px solid #3a6ea5;
            }
            QMenu::item {
                background: transparent;
            }
            QMenu::item:disabled {
                color: #6a7b8c;  /* 禁用项灰色 */
            }
        """)

        # 刷新动作（带加载动画效果）
        refresh_action = QAction('⏳ 立即刷新数据', self)
        refresh_action.setStatusTip("从服务器获取最新台风数据")
        refresh_action.triggered.connect(self.refresh_data)  # 连接到新方法
        refresh_menu.addAction(refresh_action)




        # 数据子菜单项
        insert_actions = [
            ("台风路径数据", "插入新的台风路径记录", "path_data", 0),
            ("强度指标", "添加台风强度观测数据", "intensity_data", 1),
            ("频率统计", "录入年度台风频率", "frequency_data", 2),
            ("预测模型", "导入预测模型参数", "prediction_data", 3),
            ("影响区域", "标记台风影响范围", "affected_area", 4),
            ("历史记录", "添加历史台风对比", "historical_data", 5)
        ]

        # 图标映射
        insert_icons = {
            0: "🛤️",  # 路径
            1: "💪",  # 强度
            2: "📈",  # 频率
            3: "🔍",  # 预测
            4: "📍",  # 范围
            5: "📜"  # 历史
        }
        # 在菜单栏添加插入主菜单
        data_menu = menubar.addMenu('📥 插入')
        data_menu.setStyleSheet("""
                               QMenu {
                                   background: #142b54;
                                   color: #c0d0e8;
                                   border: 1px solid #3a6ea5;
                               }
                               QMenu::item:selected {
                                   background: #2a5278;
                               }
                           """)

        for text, tip, table_name, idx in insert_actions:
            action = QAction(f"{insert_icons.get(idx, '')} {text}", self)
            action.setStatusTip(tip)
            action.triggered.connect(lambda _, t=table_name: self.show_insert_dialog(t))
            data_menu.addAction(action)

        # 添加分隔线和批量操作
        data_menu.addSeparator()
        batch_import = QAction("📦 批量导入数据...", self)
        batch_import.setStatusTip("批量导入数据")
        batch_import.triggered.connect(self.batch_import_data)
        data_menu.addAction(batch_import)

        # 文件菜单
        file_menu = menubar.addMenu('🌪️ 文件')
        file_menu.setStyleSheet("""
                       QMenu {
                           background: #142b54;
                           color: #c0d0e8;
                           border: 1px solid #3a6ea5;
                       }
                       QMenu::item:selected {
                           background: #2a5278;
                       }
                   """)
        for text, tip, table_name, idx in insert_actions:
            action = QAction(f"{insert_icons.get(idx, '')} {text}", self)
            action.setStatusTip(tip)
            action.triggered.connect(lambda _, t=table_name: self.show_select_dialog(t))
            file_menu.addAction(action)

        # 预测菜单
        prediction_menu=menubar.addMenu("🔮 预测")
        prediction_menu.setStyleSheet("""
                               QMenu {
                                   background: #142b54;
                                   color: #c0d0e8;
                                   border: 1px solid #3a6ea5;
                               }
                               QMenu::item:selected {
                                   background: #2a5278;
                               }
                           """)
        prediction_action=QAction("📈 预测路径",self)
        prediction_action.setStatusTip("预测路径")
        prediction_action.triggered.connect(self.predict)
        prediction_menu.addAction(prediction_action)

        # 个人信息
        person_menu = menubar.addMenu('👨 用户信息')
        person_menu.setStyleSheet("""
                               QMenu {
                                   background: #142b54;
                                   color: #c0d0e8;
                                   border: 1px solid #3a6ea5;
                               }
                               QMenu::item:selected {
                                   background: #2a5278;
                               }
                          """)
        person_action = QAction("👤 查看个人信息", self)
        person_action.setStatusTip("查看个人信息")
        person_action.triggered.connect(self.person)
        person_menu.addAction(person_action)

        alter_ation=QAction("🔒 修改个人信息",self)
        alter_ation.setStatusTip("修改个人信息")
        alter_ation.triggered.connect(self.alter)
        person_menu.addAction(alter_ation)





        # 更多菜单
        more_menu=menubar.addMenu("☁️ 更多")
        more_menu.setStyleSheet("""
                                       QMenu {
                                           background: #142b54;
                                           color: #c0d0e8;
                                           border: 1px solid #3a6ea5;
                                       }
                                       QMenu::item:selected {
                                           background: #2a5278;
                                       }
                                   """)
        more_action=QAction("☁️ 更多....",self)
        more_action.setStatusTip("更多功能")
        more_action.triggered.connect(self.more)
        more_menu.addAction(more_action)





    def show_insert_dialog(self, table_name):
        """通用数据插入对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"插入数据 - {table_name.replace('_', ' ').title()}")
        dialog.setMinimumWidth(500)

        layout = QFormLayout(dialog)

        # 动态生成字段输入框
        fields = self.get_table_fields(table_name)  # 从数据库获取字段
        inputs = {}
        for field in fields:
            if field['type'] == 'text':
                inputs[field['name']] = QLineEdit()
            elif field['type'] == 'number':
                inputs[field['name']] = QDoubleSpinBox()
            elif field['type'] == 'date':
                inputs[field['name']] = QDateEdit(calendarPopup=True)
            layout.addRow(field['label'], inputs[field['name']])

        # 操作按钮
        btn_box = QDialogButtonBox()
        btn_box.addButton("提交", QDialogButtonBox.AcceptRole).clicked.connect(
            lambda: self.insert_data(table_name, inputs))
        btn_box.addButton("取消", QDialogButtonBox.RejectRole).clicked.connect(dialog.reject)
        layout.addRow(btn_box)

        dialog.exec_()

    def insert_data(self, table_name, inputs):
        return

    def show_select_dialog(self,table_name):
        return

    def select_data(self,table_name):
        return

    def batch_import_data(self):
        return

    def predict(self):
        return

    def more(self):
        """显示关于对话框"""
        QMessageBox.about(self, "更多...",
                          "更多功能正在开发中，敬请期待...."
                         )

    def person(self):
        try:
            query = "SELECT * FROM user WHERE name = %s"
            result = self.db.execute_query(query, (self.username,))
            if result:
               email=result[0]["email"]
        except Exception as e:
            QMessageBox.critical(self, '数据库错误', f'查询失败: {e}')

        QMessageBox.about(self,"用户信息",f"用户名：{self.username}\n邮箱：{email}")


    def alter(self):
        return





    def init_charts(self):
        """初始化所有图表视图"""
        # 路径分析图
        self.path_chart = TyphoonMapWidget()
        self.stacked_widget.addWidget(self.path_chart)

        # 强度分析图
        self.intensity_chart = self.create_intensity_chart()
        self.stacked_widget.addWidget(self.intensity_chart)

        # 频率分析图
        self.frequency_chart = self.create_frequency_chart()
        self.stacked_widget.addWidget(self.frequency_chart)

        # 预测分析图
        self.predict_chart = self.create_predict_chart()
        self.stacked_widget.addWidget(self.predict_chart)

        # 影响范围图
        self.area_chart = self.create_area_chart()
        self.stacked_widget.addWidget(self.area_chart)

        # 历史对比图
        self.history_chart = self.create_history_chart()
        self.stacked_widget.addWidget(self.history_chart)

    def generate_sample_data(self):
        """生成模拟台风数据"""
        np.random.seed(42)

        # 生成10个台风的模拟数据
        typhoons = []
        for i in range(1, 11):
            days = np.random.randint(3, 10)
            dates = pd.date_range('2023-01-01', periods=days)
            wind_speeds = np.random.randint(20, 50, days) + np.random.rand(days) * 10
            pressures = np.random.randint(950, 1010, days) - np.random.rand(days) * 20
            latitudes = np.linspace(10, 30, days) + np.random.rand(days) * 5
            longitudes = np.linspace(120, 140, days) + np.random.rand(days) * 10

            typhoon_df = pd.DataFrame({
                '台风编号': f'TY2023-{i:02d}',
                '日期': dates,
                '风速(m/s)': wind_speeds,
                '气压(hPa)': pressures,
                '纬度': latitudes,
                '经度': longitudes
            })
            typhoons.append(typhoon_df)

        return pd.concat(typhoons)


    def create_intensity_chart(self):
        """创建台风强度分析图"""
        canvas = MplCanvas(self, width=10, height=8, dpi=100)

        # 使用pandas处理数据
        typhoon_groups = self.typhoon_data.groupby('台风编号')

        # 绘制风速变化
        for name, group in typhoon_groups:
            canvas.axes.plot(
                group['日期'],
                group['风速(m/s)'],
                marker='o',
                label=name
            )

        # 设置图表属性
        canvas.axes.set_title('台风强度变化分析')
        canvas.axes.set_xlabel('日期')
        canvas.axes.set_ylabel('风速 (m/s)')
        canvas.axes.grid(True)
        canvas.axes.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        canvas.fig.autofmt_xdate()
        canvas.fig.tight_layout()

        return canvas

    def create_frequency_chart(self):
        """创建台风频率分析图"""
        canvas = MplCanvas(self, width=10, height=8, dpi=100)

        # 使用pandas处理数据
        monthly_counts = self.typhoon_data['日期'].dt.month.value_counts().sort_index()

        # 绘制柱状图
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_counts.reindex(range(1, 13), fill_value=0).plot.bar(
            ax=canvas.axes,
            color='skyblue'
        )

        # 设置图表属性
        canvas.axes.set_title('台风月份频率分析')
        canvas.axes.set_xlabel('月份')
        canvas.axes.set_ylabel('台风数量')
        canvas.axes.set_xticklabels(months)
        canvas.axes.grid(True, axis='y')
        canvas.fig.tight_layout()

        return canvas

    def create_predict_chart(self):
        """创建台风预测分析图"""
        canvas = MplCanvas(self, width=10, height=8, dpi=100)

        # 模拟预测数据
        typhoon_groups = self.typhoon_data.groupby('台风编号')
        sample_typhoon = next(iter(typhoon_groups))[1]

        # 实际数据
        canvas.axes.plot(
            sample_typhoon['日期'],
            sample_typhoon['风速(m/s)'],
            'bo-',
            label='实际风速'
        )

        # 预测数据
        pred_dates = pd.date_range(
            sample_typhoon['日期'].iloc[-1],
            periods=3
        )
        pred_speeds = np.linspace(
            sample_typhoon['风速(m/s)'].iloc[-1],
            sample_typhoon['风速(m/s)'].iloc[-1] - 10,
            3
        )
        canvas.axes.plot(
            pred_dates,
            pred_speeds,
            'ro--',
            label='预测风速'
        )

        # 设置图表属性
        canvas.axes.set_title('台风风速预测分析')
        canvas.axes.set_xlabel('日期')
        canvas.axes.set_ylabel('风速 (m/s)')
        canvas.axes.grid(True)
        canvas.axes.legend()
        canvas.fig.autofmt_xdate()
        canvas.fig.tight_layout()

        return canvas

    def create_area_chart(self):
        """创建台风影响范围图"""
        canvas = MplCanvas(self, width=10, height=8, dpi=100)

        # 使用pandas处理数据
        typhoon_groups = self.typhoon_data.groupby('台风编号')

        # 绘制影响范围
        for name, group in typhoon_groups:
            # 简单模拟影响半径
            radius = group['风速(m/s)'] / 5
            for _, row in group.iterrows():
                circle = plt.Circle(
                    (row['经度'], row['纬度']),
                    radius=radius.mean(),
                    color='red',
                    alpha=0.2
                )
                canvas.axes.add_patch(circle)
            canvas.axes.plot(
                group['经度'],
                group['纬度'],
                'b-',
                alpha=0.5
            )

        # 设置图表属性
        canvas.axes.set_title('台风影响范围分析')
        canvas.axes.set_xlabel('经度')
        canvas.axes.set_ylabel('纬度')
        canvas.axes.grid(True)
        canvas.axes.set_aspect('equal')
        canvas.fig.tight_layout()

        return canvas

    def create_history_chart(self):
        """创建历史对比图"""
        canvas = MplCanvas(self, width=10, height=8, dpi=100)

        # 使用pandas处理数据
        typhoon_groups = self.typhoon_data.groupby('台风编号')

        # 计算每个台风的平均风速
        avg_speeds = [group['风速(m/s)'].mean() for _, group in typhoon_groups]
        typhoon_ids = [name for name, _ in typhoon_groups]

        # 绘制柱状图
        canvas.axes.bar(
            typhoon_ids,
            avg_speeds,
            color='lightgreen'
        )

        # 设置图表属性
        canvas.axes.set_title('历史台风强度对比')
        canvas.axes.set_xlabel('台风编号')
        canvas.axes.set_ylabel('平均风速 (m/s)')
        canvas.axes.grid(True, axis='y')
        canvas.fig.autofmt_xdate()
        canvas.fig.tight_layout()

        return canvas

    def switch_chart(self, index):
        """切换图表视图"""
        self.stacked_widget.setCurrentIndex(index)
        chart_names = [
            "路径分析", "强度分析", "频率分析",
            "预测分析", "影响范围", "历史对比"
        ]
        self.status_bar.showMessage(f"当前视图: {chart_names[index]}", 3000)

    def refresh_data(self):
        """刷新数据"""
        self.typhoon_data = self.generate_sample_data()
        self.init_charts()  # 重新初始化图表
        self.status_bar.showMessage("数据已刷新", 3000)

    def show_about(self):
        """完全自定义的关于对话框（100%确保内容完整显示）"""
        dialog = QDialog(self)
        dialog.setWindowTitle("🌀 关于台风分析系统")
        dialog.setMinimumSize(600, 400)  # 设置绝对最小尺寸

        # 主布局（垂直排列）
        layout = QVBoxLayout(dialog)

        # 1. 标题部分
        title = QLabel("🌪️ 台风数据可视化分析系统 v2.1")
        title.setStyleSheet("""
            QLabel {
                color: #50a3ba;
                font: bold 18pt "微软雅黑";
                padding: 10px;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(title)

        # 2. 内容部分（使用QScrollArea确保超长内容可滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QHBoxLayout(content)

        # 左列 - 核心功能
        left_col = QTextBrowser()
        left_col.setHtml("""
            <p style='font-size: 12pt;'><b>📊 核心功能：</b></p>
            <ul style='margin-left: -20px;'>
                <li>实时台风路径追踪与预测分析</li>
                <li>历史台风数据多维统计对比</li>
                <li>基于机器学习的灾害影响评估</li>
                <li>多源数据融合可视化展示</li>
            </ul>
        """)

        # 右列 - 技术特性
        right_col = QTextBrowser()
        right_col.setHtml("""
            <p style='font-size: 12pt;'><b>⚙️ 技术特性：</b></p>
            <ul style='margin-left: -20px;'>
                <li>PyQt5跨平台界面框架</li>
                <li>PyEcharts动态可视化引擎</li>
                <li>Pandas高性能数据处理</li>
                <li>多线程异步加载技术</li>
            </ul>
        """)

        for browser in [left_col, right_col]:
            browser.setStyleSheet("""
                QTextBrowser {
                    background: transparent;
                    font: 12pt "微软雅黑 Light";
                    border: none;
                    padding: 5px 15px;
                }
                /* 关键修复：强制所有子元素背景透明 */
                QTextBrowser QFrame {
                    background: transparent;
                    border: none;
                }
                QTextBrowser QScrollBar {
                    background: rgba(30, 60, 90, 0.5);
                }
            """)
            browser.setFrameShape(QFrame.NoFrame)  # 移除默认边框
            browser.setMinimumWidth(280)

            # 额外确保Viewport透明
            browser.setViewportMargins(0, 0, 0, 0)
            browser.viewport().setStyleSheet("background: transparent;")

        content_layout.addWidget(left_col)
        content_layout.addWidget(right_col)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # 3. 底部信息
        footer = QLabel("© 2023 气象科技研究中心 | 应急管理部合作项目")
        footer.setStyleSheet("""
            QLabel {
                color: #b0c4de;
                font: 10pt "微软雅黑";
                padding: 10px;
                qproperty-alignment: AlignCenter;
            }
        """)
        layout.addWidget(footer)

        # 4. 确定按钮
        btn = QPushButton("确定")
        btn.setStyleSheet("""
            QPushButton {
                background: #2a5278;
                color: white;
                border: 1px solid #3a6ea5;
                padding: 8px 25px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #3a6ea5;
            }
        """)
        btn.clicked.connect(dialog.close)
        layout.addWidget(btn, 0, Qt.AlignCenter)

        # 对话框整体样式
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a1f3a,
                    stop:1 #1a3a6e
                );
                border: 2px solid #3a6ea5;
            }
            QScrollArea {
                border: none;
            }
        """)

        # 显示对话框（模态显示）
        dialog.exec_()

    def closeEvent(self, event):
        """完全交由主程序控制关闭"""
        event.ignore()







if __name__ == '__main__':
    # 测试运行
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    window = TyphoonAnalysisSystem("测试用户")
    window.show()
    sys.exit(app.exec_())