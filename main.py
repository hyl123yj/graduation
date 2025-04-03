import os
os.environ["PNG_SKIP_sRGB_CHECK_PROFILE"] = "1"  # 必须在导入前设置！
import sys
import warnings

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (QApplication, QStackedWidget, QMessageBox)
from PyQt5.QtCore import QTimer




class TyphoonApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self._shutting_down = False  # 关闭状态标志
        self.setWindowTitle('台风数据可视化分析系统 - 欢迎')
        self.init_ui()

    def init_ui(self):
        # 初始化登录和主界面
        from ui.login_window import LoginRegisterSystem

        self.login_system = LoginRegisterSystem()
        self.login_system.setParent(self)  # 设置父对象

        # 移除登录窗口自己的关闭处理
        self.login_system.closeEvent = lambda event: event.ignore()

        self.addWidget(self.login_system)
        self.main_system = None
        # 连接信号
        self.login_system.login_success.connect(self.show_main_window)

    def show_main_window(self,username):
        """显示主窗口并移除登录窗口的关闭处理"""
        from ui.index import TyphoonAnalysisSystem

        if self.main_system is None:
            self.main_system = TyphoonAnalysisSystem(username)
            self.main_system.setParent(self)
            # 移除主窗口自己的关闭处理
            self.main_system.closeEvent = lambda event: event.ignore()
            self.addWidget(self.main_system)

        self.setCurrentIndex(1)

    def request_shutdown(self):
        """统一的关闭请求处理"""
        if self._shutting_down:
            return

        self._shutting_down = True
        reply = QMessageBox.question(
            self,
            '退出确认',
            '确定要退出台风数据可视化系统吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.safe_shutdown()
        else:
            self._shutting_down = False

    def safe_shutdown(self):
        """安全的关闭流程"""
        print("开始安全关闭流程...")

        # 第一步：隐藏所有窗口
        self.hide()

        # 第二步：异步释放资源
        QTimer.singleShot(100, self.cleanup_resources)

    def cleanup_resources(self):
        """资源清理"""
        try:
            # 关闭数据库连接
            if hasattr(self.login_system, 'db'):
                self.login_system.db.disconnect()
                print("数据库连接已关闭")

            # 销毁窗口
            if self.main_system:
                self.main_system.deleteLater()
            self.login_system.deleteLater()

            print("资源清理完成")
        except Exception as e:
            print(f"清理资源时出错: {e}")
        finally:
            # 最后退出应用
            QApplication.quit()

    def closeEvent(self, event):
        """重写主窗口关闭事件"""
        event.ignore()  # 始终忽略原生关闭事件
        self.request_shutdown()  # 使用统一关闭流程


def main():

    # 设置全局关闭策略
    app.setQuitOnLastWindowClosed(False)

    window = TyphoonApp()
    window.show()

    # 处理Ctrl+C等中断信号
    import signal
    signal.signal(signal.SIGINT, lambda *_: window.request_shutdown())

    sys.exit(app.exec_())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main()