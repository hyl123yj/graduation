import math
import random

from PyQt5 import Qt
from PyQt5.QtCore import QPointF, QTimer
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QRadialGradient, QBrush
from PyQt5.QtWidgets import QWidget


class WeatherBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = [
            {'x': random.random(), 'y': random.random(), 'speed': random.uniform(0.01, 0.03)}
            for _ in range(100)
        ]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(50)  # 20fps动画

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制渐变背景
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(10, 31, 58))
        gradient.setColorAt(1, QColor(26, 58, 113))
        painter.fillRect(self.rect(), gradient)

        # 绘制粒子（模拟气流）
        for p in self.particles:
            pos = QPointF(p['x'] * self.width(), p['y'] * self.height())
            radial = QRadialGradient(pos, 8)
            radial.setColorAt(0, QColor(100, 180, 255, 150))
            radial.setColorAt(1, Qt.transparent)
            painter.setBrush(QBrush(radial))
            painter.drawEllipse(pos, 6, 6)

    def update_particles(self):
        for p in self.particles:
            # 粒子螺旋运动模拟气旋
            p['x'] = (p['x'] + p['speed'] * 0.1) % 1
            p['y'] = (p['y'] + p['speed'] * 0.05 + 0.005 * math.sin(p['x'] * 10)) % 1
        self.update()
