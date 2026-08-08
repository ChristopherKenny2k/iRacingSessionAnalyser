from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor, QPalette

from PySide6.QtWidgets import QToolTip

from utils.resource_path import resource_path
from analysis.lap_timing import calculate_lap_timings as _calculate_lap_timings
from analysis.lockup_detection import detect_all_lockups as _detect_all_lockups

from pages.overview_page import OverviewPageMixin
from pages.timings_page import TimingsPageMixin
from pages.pedals_page import PedalsPageMixin
from pages.braking_page import BrakingPageMixin
from pages.tyres_page import TyresPageMixin
from pages.fuel_page import FuelPageMixin
from pages.gforce_page import GForcePageMixin
from pages.data_viewer_page import DataViewerPageMixin


class TelemetryWindow(
    QWidget,
    OverviewPageMixin,
    TimingsPageMixin,
    PedalsPageMixin,
    BrakingPageMixin,
    TyresPageMixin,
    FuelPageMixin,
    GForcePageMixin,
    DataViewerPageMixin,
):
    #main application window (visualisations etc) shown after a CSV is loaded from the initial csv_loader window spun up in main.py

    def __init__(self, session_info, telemetry_df, session_type):
        super().__init__()

        self.scale_factor = 1.0

        self.session_info = session_info
        self.telemetry_df = telemetry_df
        self.session_type = session_type
        self.calculate_lap_timings()
        self.setWindowIcon(QIcon(resource_path("icons/c2k.png")))

        palette = QPalette()
        palette.setColor(QPalette.ToolTipBase, QColor("white"))
        palette.setColor(QPalette.ToolTipText, QColor("black"))
        QApplication.setPalette(palette)

        self.setWindowTitle("iRacing Telemetry Viewer")
        self.resize(1600, 900)
        self.setStyleSheet("background-color: #a2a2a2;")

        QToolTip.setFont(QFont('Segoe UI', 10))
        self.setStyleSheet("""
            QToolTip {
            background-color: white;
            color: black;
            border: 1px solid black;
            padding: 4px;
            border-radius: 4px;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(1, 0, 0, 0)
        self.setLayout(main_layout)

        header = QWidget()
        header.setFixedHeight(100)
        header.setStyleSheet("background-color: #c7c9c8;")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(1, 0, 1, 0)
        header.setLayout(header_layout)
        header_layout.setSpacing(8)

        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("icons/c2k.png"))
        logo_pixmap = logo_pixmap.scaled(125, 125, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        logo_label.setFixedSize(logo_pixmap.size())
        logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        header_layout.addWidget(logo_label)

        # session info from first 8 lines of ibt->csv converted file, fallbacksd in case of error
        driver = session_info.get("Driver", "Unknown Driver")
        vehicle = session_info.get("Vehicle", "Unknown Vehicle")
        venue = session_info.get("Venue", "Unknown Venue")

        header_label = QLabel(f"{driver} | {vehicle} | {venue}")
        header_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        header_label.setStyleSheet("color: black; font-size: 42px; font-weight: bold;")
        header_layout.addWidget(header_label, alignment=Qt.AlignLeft)

        main_layout.addWidget(header)

        body = QWidget()
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body.setLayout(body_layout)
        main_layout.addWidget(body)

        left_panel = QWidget()
        left_panel.setFixedWidth(int(280 * self.scale_factor))
        left_panel.setStyleSheet("background-color: #e7bdc0;")

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 20, 0, 20)
        left_layout.setSpacing(5)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #bfbec1;")

        self.page_overview = self.make_overview_page()
        self.page_timings = self.make_timings_page()
        self.page_pedals = self.make_pedals_page()
        self.page_brakes = self.make_braking_page()
        self.page_tyres = self.make_tyres_page()
        self.page_fuel = self.make_fuel_page()
        self.page_gforce = self.make_gforce_page()
        self.page_data = self.make_page("Data Viewer")

        self.stack.addWidget(self.page_overview)  # 0
        self.stack.addWidget(self.page_timings)   # 1
        self.stack.addWidget(self.page_pedals)    # 2
        self.stack.addWidget(self.page_brakes)    # 3
        self.stack.addWidget(self.page_tyres)     # 4
        self.stack.addWidget(self.page_fuel)      # 5
        self.stack.addWidget(self.page_gforce)    # 6
        self.stack.addWidget(self.page_data)      # 7

        nav_items = [
            ("Session Overview", resource_path("icons/icon_Overview.png"), 0),
            ("Timing Data", resource_path("icons/icon_Timings.png"), 1),
            ("Pedal Usage Data", resource_path("icons/icon_Pedals.png"), 2),
            ("Lock-up Data", resource_path("icons/icon_Brakes.png"), 3),
            ("Tyre Data", resource_path("icons/icon_Tyre.png"), 4),
            ("Fuel Usage Data", resource_path("icons/icon_Fuel.png"), 5),
            ("G-Force Data", resource_path("icons/icon_gforce.png"), 6),
            ("Data Previewer", resource_path("icons/icon_Data.png"), 7),
        ]

        for label, icon_path, page_index in nav_items:
            item_container = QWidget()
            item_container.setFixedHeight(60)
            item_layout = QHBoxLayout(item_container)
            item_layout.setContentsMargins(15, 10, 15, 10)
            item_layout.setSpacing(8)
            item_layout.setAlignment(Qt.AlignVCenter)

            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(50, 50))
            btn.setFixedSize(50, 50)
            btn.setStyleSheet("""
                QPushButton { background-color: transparent; border: none; border-radius: 8px; }
                QPushButton:hover { background-color: #374151; }
                QPushButton:pressed { background-color: #4b5563; }
            """)
            btn.clicked.connect(lambda checked, idx=page_index: self.stack.setCurrentIndex(idx))

            text_label = QLabel(label)
            text_label.setStyleSheet("QLabel { color: #000000; font-size: 16px; font-weight: bold; }")

            item_layout.addWidget(btn)
            item_layout.addWidget(text_label)
            item_layout.addStretch()

            left_layout.addWidget(item_container)

            if page_index < len(nav_items) - 1:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setStyleSheet("background-color: #2d2d2d; max-height: 1px;")
                left_layout.addWidget(separator)

        left_layout.addStretch()

        body_layout.addWidget(left_panel)
        body_layout.addWidget(self.stack)

    def calculate_lap_timings(self):
        self.lap_timings, self.best_lap, self.best_lap_time = _calculate_lap_timings(self.telemetry_df)

    def detect_all_lockups(self):
        self.all_lockups = _detect_all_lockups(self.telemetry_df)

    def showEvent(self, event):
        super().showEvent(event)

        if not hasattr(self, '_scale_factor_set'):
            screen = self.screen()
            if screen is None:
                screen = QApplication.primaryScreen()

            screen_width = screen.geometry().width()

            if screen_width <= 1920:
                self.scale_factor = 0.7
            elif screen_width <= 2560:
                self.scale_factor = 0.85
            else:
                self.scale_factor = 1.0

            self._scale_factor_set = True
            self.rebuild_pages()

    def rebuild_pages(self):
        for page in (self.page_overview, self.page_timings, self.page_pedals,
                     self.page_brakes, self.page_tyres, self.page_fuel, self.page_gforce, self.page_data):
            self.stack.removeWidget(page)

        self.page_overview = self.make_overview_page()
        self.page_timings = self.make_timings_page()
        self.page_pedals = self.make_pedals_page()
        self.page_brakes = self.make_braking_page()
        self.page_tyres = self.make_tyres_page()
        self.page_fuel = self.make_fuel_page()
        self.page_gforce = self.make_gforce_page()
        self.page_data = self.make_page("Data Viewer")

        self.stack.addWidget(self.page_overview)
        self.stack.addWidget(self.page_timings)
        self.stack.addWidget(self.page_pedals)
        self.stack.addWidget(self.page_brakes)
        self.stack.addWidget(self.page_tyres)
        self.stack.addWidget(self.page_fuel)
        self.stack.addWidget(self.page_gforce)
        self.stack.addWidget(self.page_data)

        self.load_table_preview()
