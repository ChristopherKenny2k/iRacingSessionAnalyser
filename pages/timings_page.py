from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QFont
from PySide6.QtWidgets import QToolTip

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import Normalize
from matplotlib import cm
import numpy as np

from widgets.color_delegate import ColorDelegate
from analysis.consistency import calculate_consistency_grade


class TimingsPageMixin:
    """Session Timings page
        -lap time / sector table
        -delta/speed track map
        -lap-time progression chart.
    """

    def make_timings_page(self):
        page = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("Session Timings")
        title.setStyleSheet("font-size: 38px; font-weight: bold; color: #000007;")
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        self.speed_map_unit = 'kmh'

        self.calculate_lap_timings()

        stats_bar = self.create_session_stats_bar()
        layout.addWidget(stats_bar)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(5)

        table_title = QLabel("Lap Times & Sectors")
        table_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000;")
        table_layout.addWidget(table_title)

        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(15)
        legend_layout.setContentsMargins(0, 5, 0, 5)

        legend_items = [
            ("#fef08a", "In-Lap"),
            ("#bfdbfe", "Out-Lap"),
            ("#d4edda", "Best Lap"),
        ]

        for color, label in legend_items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(5)

            color_box = QLabel()
            color_box.setFixedSize(20, 20)
            color_box.setStyleSheet(f"background-color: {color}; border: 1px solid #d1d5db; border-radius: 3px;")

            text_label = QLabel(label)
            text_label.setStyleSheet("font-size: 12px; color: #111827;")

            item_layout.addWidget(color_box)
            item_layout.addWidget(text_label)
            legend_layout.addLayout(item_layout)

        legend_layout.addStretch()
        table_layout.addLayout(legend_layout)

        self.timing_table = self.create_timing_table()
        table_layout.addWidget(self.timing_table)

        table_container.setFixedWidth(int(850 * self.scale_factor))
        content_layout.addWidget(table_container)

        map_container = QWidget()
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.setSpacing(2)

        map_toggle_layout = QHBoxLayout()
        map_toggle_layout.setContentsMargins(0, int(25 * self.scale_factor), 0, 0)
        map_toggle_layout.addStretch()

        map_toggle_label = QLabel("Map Mode:")
        map_toggle_label.setStyleSheet("font-size: 12px; color: black; font-weight: bold;")
        map_toggle_layout.addWidget(map_toggle_label)

        self.timing_map_delta = QPushButton("Delta")
        self.timing_map_speed = QPushButton("Speed")
        self.timing_map_delta.setCheckable(True)
        self.timing_map_speed.setCheckable(True)
        self.timing_map_delta.setChecked(True)
        self.timing_map_delta.setFixedSize(80, 30)
        self.timing_map_speed.setFixedSize(80, 30)

        map_toggle_style = """
            QPushButton {
                background-color: #e5e7eb; color: #6b7280; border: 1px solid #d1d5db;
                border-radius: 4px; font-size: 11px; font-weight: bold;
            }
            QPushButton:checked { background-color: #2563eb; color: white; border: 1px solid #2563eb; }
            QPushButton:hover { background-color: #d1d5db; }
            QPushButton:checked:hover { background-color: #1d4ed8; }
        """
        self.timing_map_delta.setStyleSheet(map_toggle_style)
        self.timing_map_speed.setStyleSheet(map_toggle_style)

        self.timing_map_delta.clicked.connect(lambda: self.toggle_timing_map_mode("delta"))
        self.timing_map_speed.clicked.connect(lambda: self.toggle_timing_map_mode("speed"))

        map_toggle_layout.addWidget(self.timing_map_delta)
        map_toggle_layout.addWidget(self.timing_map_speed)
        map_layout.addLayout(map_toggle_layout)

        self.timing_map_container = QWidget()
        self.timing_map_layout = QVBoxLayout(self.timing_map_container)
        self.timing_map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.addWidget(self.timing_map_container)

        content_layout.addWidget(map_container)
        content_layout.addStretch()
        layout.addLayout(content_layout)

        lap_chart = self.create_lap_time_chart()
        if lap_chart:
            layout.addWidget(lap_chart)

        scroll.setWidget(content_widget)

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        self.draw_timing_map()

        return page

    def create_map_legend(self, items, title):
        legend_widget = QWidget()
        legend_widget.setFixedWidth(int(150 * self.scale_factor))
        legend_widget.setStyleSheet("""
            QWidget { background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e5e7eb; }
        """)

        legend_layout = QVBoxLayout(legend_widget)
        legend_layout.setContentsMargins(10, 10, 10, 10)
        legend_layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #111827; font-weight: bold;")
        legend_layout.addWidget(title_label)

        for color, label in items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(8)

            color_box = QLabel()
            color_box.setFixedSize(20, 20)
            color_box.setStyleSheet(f"background-color: {color}; border: 1px solid #d1d5db; border-radius: 3px;")

            text_label = QLabel(label)
            text_label.setStyleSheet("font-size: 11px; color: #111827;")

            item_layout.addWidget(color_box)
            item_layout.addWidget(text_label)
            item_layout.addStretch()
            legend_layout.addLayout(item_layout)

        legend_layout.addStretch()
        return legend_widget

    def create_speed_colourbar(self, min_speed, max_speed, unit='kmh'):
        if unit == 'mph':
            min_speed = min_speed * 0.621371
            max_speed = max_speed * 0.621371
            unit_label = 'mph'
        else:
            unit_label = 'km/h'

        colourbar_container = QWidget()
        colourbar_container.setFixedWidth(225)

        container_layout = QVBoxLayout(colourbar_container)
        container_layout.setContentsMargins(0, 4, 0, 0)
        container_layout.setSpacing(5)

        unit_toggle_layout = QHBoxLayout()
        unit_toggle_layout.setSpacing(5)

        self.speed_map_unit_kmh = QPushButton("km/h")
        self.speed_map_unit_mph = QPushButton("mph")
        self.speed_map_unit_kmh.setCheckable(True)
        self.speed_map_unit_mph.setCheckable(True)
        self.speed_map_unit_kmh.setChecked(unit == 'kmh')
        self.speed_map_unit_mph.setChecked(unit == 'mph')
        self.speed_map_unit_kmh.setFixedSize(70, 25)
        self.speed_map_unit_mph.setFixedSize(70, 25)

        unit_toggle_style = """
            QPushButton {
                background-color: #e5e7eb; color: #6b7280; border: 1px solid #d1d5db;
                border-radius: 4px; font-size: 10px; font-weight: bold;
            }
            QPushButton:checked { background-color: #2563eb; color: white; border: 1px solid #2563eb; }
            QPushButton:hover { background-color: #d1d5db; }
            QPushButton:checked:hover { background-color: #1d4ed8; }
        """
        self.speed_map_unit_kmh.setStyleSheet(unit_toggle_style)
        self.speed_map_unit_mph.setStyleSheet(unit_toggle_style)

        self.speed_map_unit_kmh.clicked.connect(lambda: self.toggle_speed_map_unit("kmh"))
        self.speed_map_unit_mph.clicked.connect(lambda: self.toggle_speed_map_unit("mph"))

        unit_toggle_layout.addWidget(self.speed_map_unit_kmh)
        unit_toggle_layout.addWidget(self.speed_map_unit_mph)
        unit_toggle_layout.addStretch()

        container_layout.addLayout(unit_toggle_layout)

        colourbar_widget = QWidget()
        colourbar_widget.setFixedWidth(int(300 * self.scale_factor))
        colourbar_widget.setFixedHeight(int(390 * self.scale_factor))

        fig = Figure(figsize=(2, 4), facecolor='#bfbec1')
        ax = fig.add_subplot(111)

        norm = Normalize(vmin=min_speed, vmax=max_speed)
        cmap = cm.get_cmap('RdYlGn')

        gradient = np.linspace(0, 1, 256).reshape(256, 1)
        ax.imshow(gradient, aspect='auto', cmap=cmap, origin='lower')

        ax.set_xticks([])
        ax.set_yticks([0, 64, 128, 192, 255])
        ax.set_yticklabels([f'{min_speed:.0f}', f'{max_speed*0.25:.0f}',
                             f'{max_speed*0.5:.0f}', f'{max_speed*0.75:.0f}', f'{max_speed:.0f}'])
        ax.set_ylabel(f'Speed ({unit_label})', fontsize=10, fontweight='bold')

        fig.subplots_adjust(left=0.5, right=0.95, top=0.98, bottom=0.02)

        canvas = FigureCanvas(fig)
        canvas.setFixedSize(int(150 * self.scale_factor), int(350 * self.scale_factor))

        layout = QVBoxLayout(colourbar_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(canvas)

        container_layout.addWidget(colourbar_widget)
        return colourbar_container

    def create_session_stats_bar(self):
        stats_bar = QWidget()
        stats_bar.setFixedHeight(int(150 * self.scale_factor))
        stats_bar.setStyleSheet("""
            QWidget { background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e5e7eb; }
        """)

        layout = QHBoxLayout(stats_bar)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(40)

        valid_times = [data['time'] for data in self.lap_timings.values()
                       if data['is_valid'] and data['time'] != float('inf')
                       and not data.get('is_outlap', False) and not data.get('is_inlap', False)]

        if len(valid_times) == 0:
            no_data_label = QLabel("No valid laps recorded")
            no_data_label.setStyleSheet("font-size: 16px; color: #6b7280;")
            layout.addWidget(no_data_label)
            return stats_bar

        fastest_time = min(valid_times)
        average_time = np.mean(valid_times)
        median_time = np.median(valid_times)
        std_dev = np.std(valid_times)

        total_laps = len([data for data in self.lap_timings.values()
                          if not data.get('is_outlap', False) and not data.get('is_inlap', False)])
        valid_laps = len(valid_times)
        valid_percentage = (valid_laps / total_laps * 100) if total_laps > 0 else 0

        def format_time(seconds):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            millis = int((seconds - int(seconds)) * 1000)
            return f"{minutes:02}:{secs:02}.{millis:03}"

        # Consistency grading handled in consistency.py see there for breakdown of matrix calculation and variable weighting
        consistency_grade, grade_color = calculate_consistency_grade(std_dev, valid_percentage)

        layout.addWidget(self.create_stat_widget("Fastest Lap", f"{format_time(fastest_time)}\n(Lap {self.best_lap})"))
        layout.addWidget(self.create_stat_widget("Average Lap", format_time(average_time)))
        layout.addWidget(self.create_stat_widget("Median Lap", format_time(median_time)))
        layout.addWidget(self.create_stat_widget("Std Deviation", f"±{std_dev:.3f}s"))
        layout.addWidget(self.create_stat_widget("Valid Laps", f"{valid_laps} / {total_laps}\n({valid_percentage:.0f}%)"))

        grade_widget = QWidget()
        grade_layout = QVBoxLayout(grade_widget)
        grade_layout.setSpacing(3)
        grade_layout.setContentsMargins(15, 5, 15, 5)

        grade_widget.setStyleSheet(f"""
            QWidget {{ background-color: {grade_color}; border-radius: 6px; border: 2px solid #d1d5db; }}
        """)

        grade_label = QLabel("Consistency")
        grade_label.setStyleSheet("font-size: 13px; color: #111827; font-weight: 500;")
        grade_label.setAlignment(Qt.AlignCenter)

        grade_value = QLabel(consistency_grade)
        grade_value.setStyleSheet("font-size: 42px; color: #111827; font-weight: bold;")
        grade_value.setAlignment(Qt.AlignCenter)

        grade_layout.addWidget(grade_label)
        grade_layout.addWidget(grade_value)

        layout.addWidget(grade_widget)
        layout.addStretch()

        return stats_bar

    def create_stat_widget(self, label, value):
        widget = QWidget()
        widget_layout = QVBoxLayout(widget)
        widget_layout.setSpacing(3)
        widget_layout.setContentsMargins(0, 0, 0, 0)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 13px; color: #6b7280; font-weight: 500;")

        value_widget = QLabel(value)
        value_widget.setStyleSheet("font-size: 20px; color: #111827; font-weight: bold;")

        widget_layout.addWidget(label_widget)
        widget_layout.addWidget(value_widget)
        return widget

    def create_timing_table(self):
        table = QTableWidget()

        delegate = ColorDelegate(table)
        table.setItemDelegate(delegate)

        headers = ["Lap", "Lap Time", "Sector 1", "Sector 2", "Sector 3", "Delta", "Pit", "Valid"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(self.lap_timings))

        table.setAlternatingRowColors(False)
        table.setSortingEnabled(False)

        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e5e7eb; font-size: 16px; border: 1px solid #d1d5db;
                border-radius: 4px; background-color: white;
            }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #f3f4f6; color: #000000; }
            QHeaderView::section {
                background-color: #f3f4f6; color: #111827; font-weight: bold; font-size: 15px;
                border: none; border-right: 1px solid #d1d5db; border-bottom: 2px solid #9ca3af; padding: 8px;
            }
        """)

        palette = table.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        table.setPalette(palette)

        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        for col in (1, 2, 3, 4, 5):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)

        table.setColumnWidth(0, int(70 * self.scale_factor))
        table.setColumnWidth(6, int(70 * self.scale_factor))
        table.setColumnWidth(7, int(70 * self.scale_factor))

        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        for row, (lap, data) in enumerate(sorted(self.lap_timings.items())):
            lap_item = QTableWidgetItem()
            lap_item.setData(Qt.ItemDataRole.DisplayRole, lap)
            lap_item.setTextAlignment(Qt.AlignCenter)

            time_item = QTableWidgetItem(data['time_str'])
            time_item.setTextAlignment(Qt.AlignCenter)

            def format_sector(seconds):
                return "—" if seconds == 0 else f"{seconds:.3f}s"

            s1_item = QTableWidgetItem(format_sector(data['sector1']))
            s1_item.setTextAlignment(Qt.AlignCenter)
            s2_item = QTableWidgetItem(format_sector(data['sector2']))
            s2_item.setTextAlignment(Qt.AlignCenter)
            s3_item = QTableWidgetItem(format_sector(data['sector3']))
            s3_item.setTextAlignment(Qt.AlignCenter)

            delta_item = QTableWidgetItem(data.get('delta_str', '—'))
            delta_item.setTextAlignment(Qt.AlignCenter)

            if data.get('is_outlap', False):
                pit_text = "OUT"
            elif data.get('is_inlap', False):
                pit_text = "IN"
            else:
                pit_text = "—"

            pit_item = QTableWidgetItem(pit_text)
            pit_item.setTextAlignment(Qt.AlignCenter)

            valid_item = QTableWidgetItem("✓" if data['is_valid'] else "✗")
            valid_item.setTextAlignment(Qt.AlignCenter)

            table.setItem(row, 0, lap_item)
            table.setItem(row, 1, time_item)
            table.setItem(row, 2, s1_item)
            table.setItem(row, 3, s2_item)
            table.setItem(row, 4, s3_item)
            table.setItem(row, 5, delta_item)
            table.setItem(row, 6, pit_item)
            table.setItem(row, 7, valid_item)

            if data.get('is_outlap', False):
                bg_color = QColor(191, 219, 254)
            elif data.get('is_inlap', False):
                bg_color = QColor(254, 240, 138)
            elif self.best_lap is not None and lap == self.best_lap:
                bg_color = QColor(212, 237, 218)
            else:
                bg_color = QColor(255, 255, 255)

            for col in range(8):
                item = table.item(row, col)
                if item:
                    item.setData(Qt.ItemDataRole.BackgroundRole, bg_color)

            if not data['is_valid']:
                for col in range(8):
                    table.item(row, col).setForeground(QColor(156, 163, 175))

        table.setSortingEnabled(True)
        table.sortItems(0, Qt.AscendingOrder)

        table.itemSelectionChanged.connect(self.on_timing_table_selection_changed)
        return table

    def on_timing_table_selection_changed(self):
        selected_items = self.timing_table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        lap_item = self.timing_table.item(row, 0)
        selected_lap = int(lap_item.text())

        self.draw_timing_map_for_lap(selected_lap)

    def toggle_timing_map_mode(self, mode):
        if mode == "delta":
            self.timing_map_delta.setChecked(True)
            self.timing_map_speed.setChecked(False)
        else:
            self.timing_map_delta.setChecked(False)
            self.timing_map_speed.setChecked(True)
        self.draw_timing_map()

    def toggle_speed_map_unit(self, unit):
        if unit == "kmh":
            self.speed_map_unit_kmh.setChecked(True)
            self.speed_map_unit_mph.setChecked(False)
        else:
            self.speed_map_unit_kmh.setChecked(False)
            self.speed_map_unit_mph.setChecked(True)

        self.speed_map_unit = unit

        selected_items = self.timing_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            lap_item = self.timing_table.item(row, 0)
            selected_lap = int(lap_item.text())
            self.draw_timing_map(selected_lap)
        else:
            self.draw_timing_map()

    def draw_timing_map(self, selected_lap=None):
        while self.timing_map_layout.count():
            child = self.timing_map_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if self.best_lap is None:
            error_label = QLabel("No valid laps to display")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("font-size: 14px; color: #6b7280;")
            self.timing_map_layout.addWidget(error_label)
            return

        if selected_lap is None:
            selected_lap = self.best_lap

        if selected_lap not in self.lap_timings:
            if self.best_lap and self.best_lap in self.lap_timings:
                selected_lap = self.best_lap
            else:
                if len(self.lap_timings) > 0:
                    selected_lap = min(self.lap_timings.keys())
                else:
                    error_label = QLabel("No valid laps to display")
                    error_label.setAlignment(Qt.AlignCenter)
                    error_label.setStyleSheet("font-size: 14px; color: #6b7280;")
                    self.timing_map_layout.addWidget(error_label)
                    return

        lap_data = self.telemetry_df[
            (self.telemetry_df["Lap"] == selected_lap) &
            (self.telemetry_df["IsOnTrackCar"] == 1)
        ].copy()

        if len(lap_data) == 0:
            error_label = QLabel(f"No data available for Lap {selected_lap}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("font-size: 14px; color: #6b7280;")
            self.timing_map_layout.addWidget(error_label)
            return

        lap_data = lap_data.sort_values("LapDistPct").reset_index(drop=True)

        fig = Figure(figsize=(8, 8), facecolor='#bfbec1')
        ax = fig.add_subplot(111)

        points = np.array([lap_data["Lon"].values, lap_data["Lat"].values]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        min_speed = 0
        max_speed = None

        if self.timing_map_delta.isChecked():
            if selected_lap == self.best_lap:
                colors = ['#22c55e'] * len(segments)
            else:
                best_lap_data = self.telemetry_df[
                    (self.telemetry_df["Lap"] == self.best_lap) &
                    (self.telemetry_df["IsOnTrackCar"] == 1)
                ].copy().sort_values("LapDistPct").reset_index(drop=True)

                colors = []
                for i in range(len(lap_data) - 1):
                    current_dist = lap_data["LapDistPct"].iloc[i]
                    current_time = lap_data["SessionTime"].iloc[i] - lap_data["SessionTime"].iloc[0]

                    best_idx = (best_lap_data["LapDistPct"] - current_dist).abs().idxmin()
                    best_time = best_lap_data["SessionTime"].iloc[best_idx] - best_lap_data["SessionTime"].iloc[0]
                    colors.append('#22c55e' if current_time < best_time else '#ef4444')

            legend_title = "Delta to Best Lap"
            legend_items = [('#22c55e', 'Faster'), ('#ef4444', 'Slower')]
        else:
            speeds_kmh = lap_data["Speed"].values * 3.6
            all_speeds = self.telemetry_df["Speed"].values * 3.6
            max_speed = all_speeds.max()

            norm = Normalize(vmin=min_speed, vmax=max_speed)
            cmap = cm.get_cmap('RdYlGn')

            colors = [cmap(norm(speed)) for speed in speeds_kmh[:-1]]

            legend_title = "Speed (km/h)"
            legend_items = None

        lc = LineCollection(segments, colors=colors, linewidths=4)
        ax.add_collection(lc)

        start_lon = lap_data["Lon"].iloc[0]
        start_lat = lap_data["Lat"].iloc[0]
        second_lon = lap_data["Lon"].iloc[1]
        second_lat = lap_data["Lat"].iloc[1]

        dx = second_lon - start_lon
        dy = second_lat - start_lat
        perp_dx, perp_dy = -dy, dx
        length = np.sqrt(perp_dx**2 + perp_dy**2)
        if length > 0:
            perp_dx = perp_dx / length * 0.0003
            perp_dy = perp_dy / length * 0.0003

        ax.plot([start_lon - perp_dx, start_lon + perp_dx],
                [start_lat - perp_dy, start_lat + perp_dy],
                color='black', linewidth=3, zorder=10)

        lap_info = self.lap_timings[selected_lap]
        title_suffix = " (Best Lap)" if selected_lap == self.best_lap else f" ({lap_info['delta_str']})"

        ax.set_title(f"Lap {selected_lap} - {legend_title}{title_suffix}", fontsize=14, fontweight='bold', pad=10)
        ax.set_aspect('equal')
        ax.set_facecolor('white')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(lap_data["Lon"].min() - 0.0005, lap_data["Lon"].max() + 0.0005)
        ax.set_ylim(lap_data["Lat"].min() - 0.0005, lap_data["Lat"].max() + 0.0005)
        fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02)

        canvas = FigureCanvas(fig)
        canvas.setMinimumSize(int(450 * self.scale_factor), int(450 * self.scale_factor))
        canvas.setMaximumSize(int(900 * self.scale_factor), int(900 * self.scale_factor))
        canvas.setSizePolicy(canvas.sizePolicy().horizontalPolicy(), canvas.sizePolicy().verticalPolicy())

        map_legend_container = QWidget()
        map_legend_layout = QHBoxLayout(map_legend_container)
        map_legend_layout.setContentsMargins(0, 0, 0, 0)
        map_legend_layout.setSpacing(10)

        map_legend_layout.addWidget(canvas)

        if legend_items is not None:
            legend_widget = self.create_map_legend(legend_items, legend_title)
            spacer = QWidget()
            spacer.setFixedHeight(int(50 * self.scale_factor))
            map_legend_layout.addWidget(spacer)
            map_legend_layout.addWidget(legend_widget, alignment=Qt.AlignTop)
        else:
            colourbar_widget = self.create_speed_colourbar(min_speed, max_speed, self.speed_map_unit)
            map_legend_layout.addWidget(colourbar_widget, alignment=Qt.AlignTop)

        self.timing_map_layout.addWidget(map_legend_container)

    def draw_timing_map_for_lap(self, lap):
        self.draw_timing_map(selected_lap=lap)

    def create_lap_time_chart(self):
        sorted_laps = sorted(self.lap_timings.keys())
        lap_numbers = []
        lap_times = []

        for lap in sorted_laps:
            lap_numbers.append(lap)
            lap_times.append(self.lap_timings[lap]['time'])

        if len(lap_times) == 0:
            return None

        fig = Figure(figsize=(12, 4), facecolor='#f8f9fa')
        ax = fig.add_subplot(111)

        points = np.array([lap_numbers, lap_times]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        colors = []
        for i in range(len(lap_times) - 1):
            colors.append('#22c55e' if lap_times[i + 1] < lap_times[i] else '#ef4444')

        lc = LineCollection(segments, colors=colors, linewidths=2, zorder=2)
        ax.add_collection(lc)

        for lap_num, lap_time in zip(lap_numbers, lap_times):
            lap_data = self.lap_timings[lap_num]

            if lap_data.get('is_outlap', False) or lap_data.get('is_inlap', False):
                ax.plot(lap_num, lap_time, 's', markersize=10,
                        markerfacecolor='#fef08a', markeredgecolor='#ca8a04', markeredgewidth=2, zorder=3)
            elif lap_num == self.best_lap:
                ax.plot(lap_num, lap_time, 'o', markersize=14,
                        markerfacecolor='#22c55e', markeredgecolor='white', markeredgewidth=2, zorder=4)
            else:
                ax.plot(lap_num, lap_time, 'o', markersize=8,
                        markerfacecolor='#2563eb', markeredgecolor='white', markeredgewidth=2, zorder=3)

        min_time = min(lap_times)
        max_time = max(lap_times)
        ax.set_ylim(min_time - 2, max_time + 2)

        def format_time(seconds, pos):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            millis = int((seconds - int(seconds)) * 1000)
            return f"{minutes:02}:{secs:02}.{millis:03}"

        ax.yaxis.set_major_formatter(FuncFormatter(format_time))

        ax.set_xlabel("Lap Number", fontsize=11, fontweight='bold', color='#111827')
        ax.set_ylabel("Lap Time", fontsize=11, fontweight='bold', color='#111827')
        ax.set_title("Lap Time Progression", fontsize=13, fontweight='bold', color='#111827', pad=10)

        ax.set_facecolor('white')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.tick_params(colors='#111827', labelsize=10)
        ax.set_xticks(lap_numbers)

        for spine in ax.spines.values():
            spine.set_edgecolor('#d1d5db')
            spine.set_linewidth(1)

        fig.subplots_adjust(left=0.08, right=0.98, top=0.85, bottom=0.25)

        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(int(235 * self.scale_factor))

        def on_hover(event):
            if event.inaxes == ax:
                for lap_num, lap_time in zip(lap_numbers, lap_times):
                    if abs(event.xdata - lap_num) < 0.3 and abs(event.ydata - lap_time) < 0.5:
                        minutes = int(lap_time // 60)
                        secs = int(lap_time % 60)
                        millis = int((lap_time - int(lap_time)) * 1000)
                        tooltip_text = f"Lap {lap_num}: {minutes:02}:{secs:02}.{millis:03}"
                        QToolTip.showText(canvas.mapToGlobal(event.guiEvent.pos()), tooltip_text)
                        return
                QToolTip.hideText()

        canvas.mpl_connect('motion_notify_event', on_hover)

        return canvas
