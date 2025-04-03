from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from pyecharts.charts import Geo
from pyecharts import options as opts
from pyecharts.globals import ChartType
import pandas as pd

class TyphoonMapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.province_coords = {
            # 直辖市
            "北京": (116.40, 39.90),
            "上海": (121.47, 31.23),
            "天津": (117.20, 39.13),
            "重庆": (106.50, 29.53),

            # 省份（按拼音排序）
            "安徽": (117.28, 31.86),
            "福建": (119.30, 26.08),
            "甘肃": (103.82, 36.06),
            "广东": (113.23, 23.16),
            "广西": (108.37, 22.81),
            "贵州": (106.71, 26.57),
            "海南": (110.20, 20.02),
            "河北": (114.48, 38.03),
            "河南": (113.62, 34.75),
            "黑龙江": (126.63, 45.80),
            "湖北": (114.30, 30.60),
            "湖南": (112.97, 28.20),
            "吉林": (125.35, 43.88),
            "江苏": (118.78, 32.04),
            "江西": (115.86, 28.68),
            "辽宁": (123.43, 41.80),
            "内蒙古": (111.73, 40.83),
            "宁夏": (106.27, 38.47),
            "青海": (101.78, 36.62),
            "山东": (117.00, 36.65),
            "山西": (112.53, 37.87),
            "陕西": (108.93, 34.27),
            "四川": (104.06, 30.67),
            "西藏": (91.11, 29.97),
            "新疆": (87.62, 43.82),
            "云南": (102.71, 25.04),
            "浙江": (120.15, 30.28),

            # 特别行政区
            "香港": (114.16, 22.28),
            "澳门": (113.54, 22.19),

            # 台湾地区
            "台湾": (121.30, 25.03)
        }
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        self.setLayout(layout)
        self.load_map()

    def load_map(self):
        try:
            land_data = pd.read_csv(r"D:\graduation_project\project\sql_data\land.csv")
            province_counts = land_data["land_province"].value_counts().reset_index()
            province_counts.columns = ["name", "value"]

            geo = (
                Geo()
                .add_schema(maptype="china")
                .add(
                    "台风登陆次数",
                    data_pair=[(name, cnt) for name, cnt in province_counts.values
                               if name in self.province_coords],
                    type_=ChartType.EFFECT_SCATTER
                )
                .set_global_opts(title_opts=opts.TitleOpts(title="台风登陆热力图"))
            )
            self.web_view.setHtml(geo.render_embed())
        except Exception as e:
            self.web_view.setHtml(f"<h1>Error: {str(e)}</h1>")

