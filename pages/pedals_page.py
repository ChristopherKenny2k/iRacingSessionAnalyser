from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QComboBox, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch
from scipy.ndimage import median_filter
import numpy as np

from widgets.zoomable_canvas import ZoomableCanvas


class PedalsPageMixin:
    """Pedal Usage page:
        -throttle/brake/gear track map with time-synced playback
        - rolling pedal + gear trace charts.
    """

    def make_pedals_page(self):
        page = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(5, 5, 5, 1)
        layout.setSpacing(1)

        title = QLabel("Pedal Usage Data")
        title.setStyleSheet("font-size: 38px; font-weight: bold; color: #000007;")
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        main_row = QHBoxLayout()
        main_row.setSpacing(int(15 * self.scale_factor))

        lap_selector_container = QWidget()
        lap_selector_container.setFixedWidth(int(280 * self.scale_factor))
        lap_selector_container.setStyleSheet("""
            QWidget { background-color: white; border-radius: 0px; border: none; }
        """)
        lap_selector_layout = QVBoxLayout(lap_selector_container)
        lap_selector_layout.setContentsMargins(0, 0, 0, 0)
        lap_selector_layout.setSpacing(0)

        order_layout = QHBoxLayout()
        order_label = QLabel("Order by:")
        order_label.setStyleSheet("font-size: 18px; color: black; font-weight: bold;")

        self.lap_order_selector = QComboBox()
        self.lap_order_selector.addItem("Chronological", "chronological")
        self.lap_order_selector.addItem("Fastest to Slowest", "fastest")
        self.lap_order_selector.addItem("Slowest to Fastest", "slowest")
        self.lap_order_selector.setStyleSheet("""
            QComboBox { font-size: 16px; color: black; background-color: white; padding: 5px; border: 1px solid #d1d5db; border-radius: 4px; }
            QComboBox QAbstractItemView { color: black; background-color: white; selection-background-color: #2563eb; selection-color: white; }
        """)
        self.lap_order_selector.currentIndexChanged.connect(self.update_lap_list)

        order_layout.addWidget(order_label)
        order_layout.addWidget(self.lap_order_selector)
        lap_selector_layout.addLayout(order_layout)

        self.lap_list = QListWidget()
        self.lap_list.setStyleSheet("""
            QListWidget { background-color: white; border: 1px solid #e5e7eb; border-radius: 4px; font-size: 18px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #f3f4f6; color: #000000; }
            QListWidget::item:selected { background-color: #2563eb; color: white; }
            QListWidget::item:hover { background-color: #eff6ff; color: #000000; }
        """)
        self.lap_list.itemClicked.connect(self.update_pedal_track_map_from_list)
        lap_selector_layout.addWidget(self.lap_list)

        lap_selector_wrapper = QWidget()
        lap_selector_wrapper.setFixedWidth(int(284 * self.scale_factor))
        lap_selector_wrapper.setStyleSheet("""
            QWidget { background-color: white; border: 2px solid #000000; border-radius: 8px; }
        """)
        lap_selector_wrapper_layout = QVBoxLayout(lap_selector_wrapper)
        lap_selector_wrapper_layout.setContentsMargins(2, 2, 2, 2)
        lap_selector_wrapper_layout.setAlignment(Qt.AlignTop)
        lap_selector_wrapper_layout.addWidget(lap_selector_container)

        main_row.addWidget(lap_selector_wrapper)

        map_column = QVBoxLayout()
        map_column.setSpacing(int(9 * self.scale_factor))

        toggle_container = QWidget()
        toggle_container.setFixedHeight(int(40 * self.scale_factor))
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(10)

        toggle_label = QLabel("Map View:")
        toggle_label.setStyleSheet("font-size: 12px; color: black; font-weight: bold;")
        toggle_layout.addWidget(toggle_label)

        self.map_mode_throttle = QPushButton("Throttle/Brake")
        self.map_mode_gear = QPushButton("Gear")
        self.map_mode_throttle.setCheckable(True)
        self.map_mode_gear.setCheckable(True)
        self.map_mode_throttle.setChecked(True)
        self.map_mode_throttle.setFixedSize(int(110 * self.scale_factor), int(30 * self.scale_factor))
        self.map_mode_gear.setFixedSize(int(70 * self.scale_factor), int(30 * self.scale_factor))

        map_toggle_style = """
            QPushButton { background-color: #e5e7eb; color: #6b7280; border: 1px solid #d1d5db; border-radius: 4px; font-size: 11px; font-weight: bold; }
            QPushButton:checked { background-color: #2563eb; color: white; border: 1px solid #2563eb; }
            QPushButton:hover { background-color: #d1d5db; }
            QPushButton:checked:hover { background-color: #1d4ed8; }
        """
        self.map_mode_throttle.setStyleSheet(map_toggle_style)
        self.map_mode_gear.setStyleSheet(map_toggle_style)

        self.map_mode_throttle.clicked.connect(lambda: self.toggle_map_mode("throttle"))
        self.map_mode_gear.clicked.connect(lambda: self.toggle_map_mode("gear"))

        toggle_layout.addWidget(self.map_mode_throttle)
        toggle_layout.addWidget(self.map_mode_gear)
        toggle_layout.addStretch()

        map_column.addWidget(toggle_container)

        map_content_row = QHBoxLayout()
        map_content_row.setSpacing(int(50 * self.scale_factor))

        self.pedal_map_container = QWidget()
        self.pedal_map_container.setFixedWidth(int(1000 * self.scale_factor))
        self.pedal_map_layout = QVBoxLayout(self.pedal_map_container)
        self.pedal_map_layout.setContentsMargins(0, 0, 0, 0)
        self.pedal_map_layout.setSpacing(0)
        map_content_row.addWidget(self.pedal_map_container)

        right_side_column = QVBoxLayout()
        right_side_column.setSpacing(int(10 * self.scale_factor))
        right_side_column.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        right_side_column.setContentsMargins(int(45 * self.scale_factor), 0, 0, 0)

        self.legend_placeholder = QWidget()
        self.legend_placeholder_layout = QVBoxLayout(self.legend_placeholder)
        self.legend_placeholder_layout.setContentsMargins(0, 0, 0, 0)
        right_side_column.addWidget(self.legend_placeholder)

        self.speed_display_widget = QWidget()
        self.speed_display_widget.setFixedHeight(int(150 * self.scale_factor))
        self.speed_display_widget.setFixedWidth(int(150 * self.scale_factor))
        self.speed_display_widget.setStyleSheet("""
            QWidget { background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e5e7eb; }
        """)
        speed_display_layout = QVBoxLayout(self.speed_display_widget)
        speed_display_layout.setContentsMargins(10, 8, 10, 8)
        speed_display_layout.setSpacing(3)

        speed_label = QLabel("Speed")
        speed_label.setStyleSheet("font-size: 11px; color: #6b7280; font-weight: 500;")
        speed_display_layout.addWidget(speed_label)

        self.speed_value_label = QLabel("0")
        self.speed_value_label.setStyleSheet("font-size: 36px; color: #111827; font-weight: bold;")
        speed_display_layout.addWidget(self.speed_value_label)

        unit_row = QHBoxLayout()
        unit_row.setSpacing(5)

        self.speed_unit_kmh = QPushButton("km/h")
        self.speed_unit_mph = QPushButton("mph")
        self.speed_unit_kmh.setCheckable(True)
        self.speed_unit_mph.setCheckable(True)
        self.speed_unit_kmh.setChecked(True)
        self.speed_unit_kmh.setFixedSize(int(55 * self.scale_factor), int(25 * self.scale_factor))
        self.speed_unit_mph.setFixedSize(int(55 * self.scale_factor), int(25 * self.scale_factor))

        toggle_style = """
            QPushButton { background-color: #e5e7eb; color: #6b7280; border: 1px solid #d1d5db; border-radius: 4px; font-size: 10px; font-weight: bold; }
            QPushButton:checked { background-color: #2563eb; color: white; border: 1px solid #2563eb; }
            QPushButton:hover { background-color: #d1d5db; }
            QPushButton:checked:hover { background-color: #1d4ed8; }
        """
        self.speed_unit_kmh.setStyleSheet(toggle_style)
        self.speed_unit_mph.setStyleSheet(toggle_style)

        self.speed_unit_kmh.clicked.connect(lambda: self.toggle_speed_unit("kmh"))
        self.speed_unit_mph.clicked.connect(lambda: self.toggle_speed_unit("mph"))

        unit_row.addWidget(self.speed_unit_kmh)
        unit_row.addWidget(self.speed_unit_mph)
        speed_display_layout.addLayout(unit_row)

        right_side_column.addWidget(self.speed_display_widget)

        self.pedal_graph_container = QWidget()
        self.pedal_graph_layout = QVBoxLayout(self.pedal_graph_container)
        self.pedal_graph_layout.setContentsMargins(0, 0, 0, 0)
        right_side_column.addWidget(self.pedal_graph_container)

        self.gear_graph_container = QWidget()
        self.gear_graph_layout = QVBoxLayout(self.gear_graph_container)
        self.gear_graph_layout.setContentsMargins(0, 0, 0, 0)
        right_side_column.addWidget(self.gear_graph_container)

        map_content_row.addLayout(right_side_column)
        map_column.addLayout(map_content_row)

        controls_widget = QWidget()
        controls_widget.setFixedHeight(50)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        controls_layout.setSpacing(10)

        self.play_pause_btn = QPushButton("▶ Play")
        self.play_pause_btn.setFixedWidth(int(100 * self.scale_factor))
        self.play_pause_btn.setStyleSheet("""
            QPushButton { background-color: #2563eb; color: white; border-radius: 4px; font-size: 14px; font-weight: bold; padding: 5px; }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        self.play_pause_btn.clicked.connect(self.toggle_playback)

        self.reset_btn = QPushButton("↺ Reset")
        self.reset_btn.setFixedWidth(int(100 * self.scale_factor))
        self.reset_btn.setStyleSheet("""
            QPushButton { background-color: #6b7280; color: white; border-radius: 4px; font-size: 14px; font-weight: bold; padding: 5px; }
            QPushButton:hover { background-color: #4b5563; }
        """)
        self.reset_btn.clicked.connect(self.reset_playback)

        speed_label_ctrl = QLabel("Speed:")
        speed_label_ctrl.setStyleSheet("font-size: 14px; font-weight: bold; color: black;")

        self.speed_selector = QComboBox()
        self.speed_selector.addItem("1x", 1)
        self.speed_selector.addItem("2x", 2)
        self.speed_selector.addItem("4x", 4)
        self.speed_selector.addItem("8x", 8)
        self.speed_selector.setFixedWidth(int(70 * self.scale_factor))
        self.speed_selector.setStyleSheet("QComboBox { color: black; padding: 3px; }")

        self.playback_time_label = QLabel("0.000s / 0.000s")
        self.playback_time_label.setStyleSheet("font-size: 14px; color: black; font-weight: bold;")

        controls_layout.addWidget(self.play_pause_btn)
        controls_layout.addWidget(self.reset_btn)
        controls_layout.addWidget(speed_label_ctrl)
        controls_layout.addWidget(self.speed_selector)
        controls_layout.addWidget(self.playback_time_label)
        controls_layout.addStretch()

        map_column.addWidget(controls_widget)

        main_row.addLayout(map_column)
        layout.addLayout(main_row)
        layout.addStretch()

        self.playback_index = 0
        self.playback_active = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.playback_step)
        self.current_lap_data = None
        self.playback_interval = 100
        self.lap_data_dict = {}

        valid_laps = sorted(self.telemetry_df[self.telemetry_df["Lap"] > 0]["Lap"].unique())

        for lap in valid_laps:
            lap_times = self.telemetry_df[
                (self.telemetry_df["Lap"] == lap + 1) &
                (self.telemetry_df["LapLastLapTime"] > 0)
            ]["LapLastLapTime"]

            if len(lap_times) > 0:
                lap_time = lap_times.iloc[-1]
            else:
                lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap]
                if len(lap_data) > 1:
                    lap_time = (lap_data["SessionTick"].iloc[-1] - lap_data["SessionTick"].iloc[0]) / 60
                else:
                    lap_time = None

            if lap_time and lap_time > 0:
                minutes = int(lap_time // 60)
                seconds = int(lap_time % 60)
                millis = int((lap_time - int(lap_time)) * 1000)
                self.lap_data_dict[int(lap)] = {'time': lap_time, 'time_str': f"{minutes:02}:{seconds:02}.{millis:03}"}
            else:
                self.lap_data_dict[int(lap)] = {'time': float('inf'), 'time_str': 'N/A'}

        if len(self.lap_data_dict) > 0:
            last_lap = max(self.lap_data_dict.keys())
            if last_lap in self.lap_data_dict:
                del self.lap_data_dict[last_lap]

        self.update_lap_list()

        if self.lap_list.count() > 0:
            self.lap_list.setCurrentRow(0)
            self.update_pedal_track_map_from_list()

        scroll.setWidget(content_widget)

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        return page

    def toggle_speed_unit(self, unit):
        if unit == "kmh":
            self.speed_unit_kmh.setChecked(True)
            self.speed_unit_mph.setChecked(False)
        else:
            self.speed_unit_kmh.setChecked(False)
            self.speed_unit_mph.setChecked(True)

    def toggle_map_mode(self, mode):
        if mode == "throttle":
            self.map_mode_throttle.setChecked(True)
            self.map_mode_gear.setChecked(False)
        else:
            self.map_mode_throttle.setChecked(False)
            self.map_mode_gear.setChecked(True)

        current_item = self.lap_list.currentItem()
        if current_item:
            selected_lap = current_item.data(Qt.UserRole)
            self.update_pedal_track_map(selected_lap)

    def update_lap_list(self):
        self.lap_list.clear()
        order_mode = self.lap_order_selector.currentData()

        if order_mode == "chronological":
            sorted_laps = sorted(self.lap_data_dict.keys())
        elif order_mode == "fastest":
            sorted_laps = sorted(self.lap_data_dict.keys(), key=lambda x: self.lap_data_dict[x]['time'])
        else:
            sorted_laps = sorted(self.lap_data_dict.keys(), key=lambda x: self.lap_data_dict[x]['time'], reverse=True)

        for lap in sorted_laps:
            lap_info = self.lap_data_dict[lap]
            item = QListWidgetItem(f"Lap {lap} - {lap_info['time_str']}")
            item.setData(Qt.UserRole, lap)
            self.lap_list.addItem(item)

    def update_pedal_track_map_from_list(self):
        current_item = self.lap_list.currentItem()
        if current_item:
            selected_lap = current_item.data(Qt.UserRole)
            self.reset_playback()
            self.update_pedal_track_map(selected_lap)

    def update_pedal_track_map(self, selected_lap):
        self.playback_timer.stop()
        self.playback_active = False
        self.play_pause_btn.setText("▶ Play")

        for layout_attr in (self.pedal_map_layout, self.pedal_graph_layout, self.gear_graph_layout):
            while layout_attr.count():
                child = layout_attr.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        if selected_lap is None:
            return

        lap_data = self.telemetry_df[(self.telemetry_df["Lap"] == selected_lap)].copy()

        if len(lap_data) == 0:
            error_label = QLabel("No data available for this lap")
            error_label.setAlignment(Qt.AlignCenter)
            self.pedal_map_layout.addWidget(error_label)
            return

        lap_data = lap_data.sort_values("SessionTick").reset_index(drop=True)

        self.current_lap_data = lap_data
        self.playback_index = 0

        lap_time_val = self.lap_data_dict.get(selected_lap, {}).get('time', 0)
        lap_time_str = self.lap_data_dict.get(selected_lap, {}).get('time_str', 'N/A')
        row_count = len(lap_data)

        if lap_time_val > 0 and lap_time_val != float('inf') and row_count > 0:
            self.playback_interval = (lap_time_val / row_count) * 1000
        else:
            self.playback_interval = 100

        self.playback_time_label.setText(f"0.000s / {lap_time_val:.3f}s")

        fig_map = Figure(figsize=(15, 10), facecolor='#bfbec1')
        ax_map = fig_map.add_subplot(111)

        points = np.array([lap_data["Lon"].values, lap_data["Lat"].values]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        throttle = lap_data["Throttle"].values
        brake = lap_data["Brake"].values
        gear = lap_data["Gear"].values
        COAST_THRESHOLD = 3

        colors = []
        if self.map_mode_throttle.isChecked():
            for i in range(len(throttle) - 1):
                if throttle[i] < COAST_THRESHOLD and brake[i] < COAST_THRESHOLD:
                    colors.append('#ffcd03')
                elif throttle[i] > brake[i]:
                    colors.append('#079902')
                else:
                    colors.append('#ff0318')
        else:
            gear_color_map = {
                -1: '#002aff', 0: '#00aaff', 1: '#00ff91', 2: '#48a82a', 3: '#d8f51d',
                4: '#faac0f', 5: '#fa750f', 6: '#fa0f0f', 7: '#aa44ff', 8: '#f308ff',
            }
            for i in range(len(gear) - 1):
                colors.append(gear_color_map.get(int(gear[i]), '#ffffff'))

        lc = LineCollection(segments, colors=colors, linewidths=3.5)
        ax_map.add_collection(lc)

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

        ax_map.plot([start_lon - perp_dx, start_lon + perp_dx],
                    [start_lat - perp_dy, start_lat + perp_dy],
                    color='black', linewidth=2.5, zorder=10)

        self.driver_dot, = ax_map.plot(lap_data["Lon"].iloc[0], lap_data["Lat"].iloc[0],
                                        'o', color='black', markersize=10, zorder=20)

        map_title = f"Lap {selected_lap} - Throttle/Brake Usage" if self.map_mode_throttle.isChecked() \
            else f"Lap {selected_lap} - Gear Usage"

        ax_map.set_title(map_title, fontsize=14, fontweight='bold', pad=10, loc='left')
        ax_map.text(0.98, 0.98, f"Lap Time: {lap_time_str}", transform=ax_map.transAxes, fontsize=12,
                    verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax_map.set_aspect('equal')
        ax_map.set_facecolor('#d6d6d6')
        ax_map.set_xticks([])
        ax_map.set_yticks([])
        ax_map.set_xlim(lap_data["Lon"].min() - 0.0005, lap_data["Lon"].max() + 0.0005)
        ax_map.set_ylim(lap_data["Lat"].min() - 0.0005, lap_data["Lat"].max() + 0.0005)
        fig_map.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.01)

        self.map_canvas = ZoomableCanvas(fig_map)
        self.map_canvas.setFixedSize(int(1000 * self.scale_factor), int(1000 * self.scale_factor))
        self.map_ax = ax_map

        legend_widget = QWidget()
        legend_widget.setFixedWidth(int(150 * self.scale_factor))
        legend_widget.setStyleSheet("""
            QWidget { background-color: #f8f9fa; border-radius: 8px; border: 1px solid #e5e7eb; }
        """)
        legend_layout = QVBoxLayout(legend_widget)
        legend_layout.setContentsMargins(10, 10, 10, 10)
        legend_layout.setSpacing(5)

        legend_title = QLabel("Legend")
        legend_title.setStyleSheet("font-size: 13px; color: #111827; font-weight: bold;")
        legend_layout.addWidget(legend_title)

        if self.map_mode_throttle.isChecked():
            legend_items = [("#079902", "Throttle"), ("#ff0318", "Brake"), ("#ffcd03", "Coasting")]
        else:
            gear_color_map = {
                -1: '#002aff', 0: '#00aaff', 1: '#00ff91', 2: '#48a82a', 3: '#d8f51d',
                4: '#faac0f', 5: '#fa750f', 6: '#fa0f0f', 7: '#aa44ff', 8: '#f308ff',
            }
            min_gear = int(lap_data["Gear"].min())
            max_gear = int(lap_data["Gear"].max())
            gear_range = range(min_gear if min_gear < 0 else 0, max_gear + 1)

            legend_items = []
            for g in gear_range:
                gear_label = 'R' if g == -1 else 'N' if g == 0 else f"Gear {g}"
                legend_items.append((gear_color_map.get(g, '#ffffff'), gear_label))

        for color, label in legend_items:
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

        while self.legend_placeholder_layout.count():
            child = self.legend_placeholder_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.legend_placeholder_layout.addWidget(legend_widget, alignment=Qt.AlignTop)

        self.pedal_map_layout.addWidget(self.map_canvas)

        fig_pedal = Figure(figsize=(10, 3.5), facecolor='#bfbec1')
        self.pedal_ax = fig_pedal.add_subplot(111)
        self.pedal_ax.set_facecolor('#1a1a2e')
        self.pedal_ax.set_xlim(0, 5)
        self.pedal_ax.set_ylim(-5, 105)
        self.pedal_ax.set_ylabel("Input %", fontsize=10, color='black')
        self.pedal_ax.tick_params(colors='black')
        self.pedal_ax.set_xlabel("Time (s)", fontsize=10, color='black')
        for spine in self.pedal_ax.spines.values():
            spine.set_edgecolor('#444444')

        for y_val in [25, 50, 75]:
            self.pedal_ax.axhline(y=y_val, color='#adadad', linewidth=1, linestyle='--', alpha=0.3, zorder=1)

        legend_elements = [Patch(facecolor='#079902', label='Throttle'), Patch(facecolor='#ff0318', label='Brake')]
        self.pedal_ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, -.20), ncol=2,
                              facecolor='#bfbec1', labelcolor='black', fontsize=9, framealpha=1, edgecolor='#444444')

        self.throttle_line, = self.pedal_ax.plot([], [], color='#04ff00', linewidth=1)
        self.brake_line, = self.pedal_ax.plot([], [], color='#ff0000', linewidth=1)

        fig_pedal.subplots_adjust(left=0.065, right=0.98, top=0.90, bottom=0.25)

        self.pedal_canvas = FigureCanvas(fig_pedal)
        self.pedal_canvas.setFixedSize(int(1100 * self.scale_factor), int(375 * self.scale_factor))
        self.pedal_graph_layout.addWidget(self.pedal_canvas, alignment=Qt.AlignTop | Qt.AlignLeft)

        self.playback_time_data = []
        self.playback_throttle_data = []
        self.playback_brake_data = []
        self.current_time = 0.0

        min_gear = int(lap_data["Gear"].min())
        max_gear = int(lap_data["Gear"].max())
        y_min = -1.5 if min_gear < 0 else -0.5
        y_max = max_gear + 0.5

        fig_gear = Figure(figsize=(10, 2.5), facecolor='#bfbec1')
        self.gear_ax = fig_gear.add_subplot(111)
        self.gear_ax.set_facecolor('#1a1a2e')
        self.gear_ax.set_xlim(0, 5)
        self.gear_ax.set_ylim(y_min, y_max)
        self.gear_ax.set_ylabel("Gear", fontsize=12, color='black')
        self.gear_ax.tick_params(colors='black')
        self.gear_ax.set_xlabel("Time (s)", fontsize=10, color='black')
        for spine in self.gear_ax.spines.values():
            spine.set_edgecolor('#444444')

        gear_ticks = list(range(min_gear if min_gear < 0 else 0, max_gear + 1))
        gear_labels = ['R' if g == -1 else 'N' if g == 0 else str(g) for g in gear_ticks]
        self.gear_ax.set_yticks(gear_ticks)
        self.gear_ax.set_yticklabels(gear_labels, color='black', fontsize=9)

        for g in gear_ticks:
            self.gear_ax.axhline(y=g, color='#adadad', linewidth=1, linestyle='--', alpha=0.3, zorder=1)

        self.gear_line, = self.gear_ax.plot([], [], color='#05f7ef', linewidth=1)

        fig_gear.subplots_adjust(left=0.065, right=0.98, top=0.90, bottom=0.19)

        self.gear_canvas = FigureCanvas(fig_gear)
        self.gear_canvas.setFixedSize(int(1100 * self.scale_factor), int(300 * self.scale_factor))
        self.gear_graph_layout.addWidget(self.gear_canvas, alignment=Qt.AlignTop | Qt.AlignLeft)

        self.playback_gear_data = []

    def toggle_playback(self):
        if self.current_lap_data is None:
            return

        if self.playback_active:
            self.playback_timer.stop()
            self.playback_active = False
            self.play_pause_btn.setText("▶ Play")
        else:
            if self.playback_index >= len(self.current_lap_data) - 1:
                self.reset_playback()

            self.playback_active = True
            self.play_pause_btn.setText("⏸ Pause")
            self.playback_timer.start(50)

    def reset_playback(self):
        self.playback_timer.stop()
        self.playback_active = False
        self.play_pause_btn.setText("▶ Play")
        self.playback_index = 0
        self.current_time = 0.0
        self.current_tick = 0
        self.playback_time_data = []
        self.playback_throttle_data = []
        self.playback_brake_data = []
        self.playback_gear_data = []
        self._last_plotted_index = 0

        self.speed_value_label.setText("0")

        if self.current_lap_data is not None:
            if hasattr(self, 'driver_dot') and hasattr(self, 'map_canvas'):
                self.driver_dot.set_data(
                    [self.current_lap_data["Lon"].iloc[0]],
                    [self.current_lap_data["Lat"].iloc[0]]
                )
                self.map_canvas.draw()

            if hasattr(self, 'throttle_line'):
                self.throttle_line.set_data([], [])
                self.brake_line.set_data([], [])
                self.pedal_ax.set_xlim(0, 5)
                self.pedal_canvas.draw()

            if hasattr(self, 'gear_line'):
                self.gear_line.set_data([], [])
                self.gear_ax.set_xlim(0, 5)
                self.gear_canvas.draw()

            lap_start_tick = self.current_lap_data["SessionTick"].iloc[0]
            lap_end_tick = self.current_lap_data["SessionTick"].iloc[-1]
            total_time = (lap_end_tick - lap_start_tick) / 60
            self.playback_time_label.setText(f"0.000s / {total_time:.3f}s")

    def playback_step(self):
        if self.current_lap_data is None:
            return

        speed = self.speed_selector.currentData()
        ticks_per_second = 60
        tick_increment = int((0.05 * speed) * ticks_per_second)

        lap_start_tick = self.current_lap_data["SessionTick"].iloc[0]
        lap_end_tick = self.current_lap_data["SessionTick"].iloc[-1]
        total_lap_ticks = lap_end_tick - lap_start_tick

        if not hasattr(self, 'current_tick'):
            self.current_tick = 0

        self.current_tick += tick_increment

        if self.current_tick >= total_lap_ticks:
            self.playback_timer.stop()
            self.playback_active = False
            self.play_pause_btn.setText("▶ Play")
            self.current_tick = total_lap_ticks
            self.playback_index = len(self.current_lap_data) - 1
            current_row = self.current_lap_data.iloc[self.playback_index]
        else:
            target_tick = lap_start_tick + self.current_tick
            tick_diffs = (self.current_lap_data["SessionTick"] - target_tick).abs()
            self.playback_index = tick_diffs.idxmin()
            current_row = self.current_lap_data.loc[self.playback_index]

        self.driver_dot.set_data([current_row["Lon"]], [current_row["Lat"]])
        self.map_canvas.draw()

        current_speed_ms = float(current_row["Speed"])
        if self.speed_unit_kmh.isChecked():
            self.speed_value_label.setText(f"{current_speed_ms * 3.6:.0f}")
        else:
            self.speed_value_label.setText(f"{current_speed_ms * 2.23694:.0f}")

        last_plotted_index = getattr(self, '_last_plotted_index', 0)

        if self.playback_index > last_plotted_index:
            for idx in range(last_plotted_index + 1, self.playback_index + 1):
                if idx < len(self.current_lap_data):
                    row = self.current_lap_data.iloc[idx]
                    row_tick = row["SessionTick"] - lap_start_tick
                    row_time = row_tick / ticks_per_second

                    if len(self.playback_time_data) == 0 or row_time > self.playback_time_data[-1]:
                        throttle_val = float(row["Throttle"])
                        brake_val = float(row["Brake"])

                        # Spike filtering
                        # i noticed some innacuracies in throttle and brake mapping (sharp sudden spikes / anomalies) 
                        # most commonly during a transition from brake to throttle
                        # some 
                        if len(self.playback_throttle_data) > 0:
                            last_throttle = self.playback_throttle_data[-1]
                            if brake_val > 20 and throttle_val > last_throttle + 30:
                                throttle_val = last_throttle

                        self.playback_time_data.append(row_time)
                        self.playback_throttle_data.append(throttle_val)
                        self.playback_brake_data.append(brake_val)
                        self.playback_gear_data.append(float(row["Gear"]))

        self._last_plotted_index = self.playback_index

        window_seconds = 5.0
        times = self.playback_time_data
        throttles = self.playback_throttle_data
        brakes = self.playback_brake_data
        gears = self.playback_gear_data

        current_time_seconds = self.current_tick / ticks_per_second

        window_start = current_time_seconds - window_seconds
        start_idx = 0
        for i, t in enumerate(times):
            if t >= window_start:
                start_idx = i
                break

        windowed_times = times[start_idx:]
        windowed_throttle_raw = throttles[start_idx:]
        windowed_brake_raw = brakes[start_idx:]
        windowed_gear = gears[start_idx:]

        # further data cleaning to remove anomalies present in iRacing's raw export
        windowed_throttle = []
        for i, (thr, brk) in enumerate(zip(windowed_throttle_raw, windowed_brake_raw)):
            if brk > 10 and thr > 10:
                if i > 0 and windowed_throttle[-1] < 5:
                    windowed_throttle.append(windowed_throttle[-1])
                else:
                    windowed_throttle.append(0)
            else:
                windowed_throttle.append(thr)
                
        if len(windowed_throttle) > 3:
            windowed_throttle = list(median_filter(windowed_throttle, size=5))

        windowed_brake = list(median_filter(windowed_brake_raw, size=3)) if len(windowed_brake_raw) > 3 else windowed_brake_raw

        self.throttle_line.set_data(windowed_times, windowed_throttle)
        self.brake_line.set_data(windowed_times, windowed_brake)

        if current_time_seconds > window_seconds:
            self.pedal_ax.set_xlim(current_time_seconds - window_seconds, current_time_seconds)
        else:
            self.pedal_ax.set_xlim(0, window_seconds)

        self.pedal_canvas.draw()

        self.gear_line.set_data(windowed_times, windowed_gear)

        if current_time_seconds > window_seconds:
            self.gear_ax.set_xlim(current_time_seconds - window_seconds, current_time_seconds)
        else:
            self.gear_ax.set_xlim(0, window_seconds)

        self.gear_canvas.draw()
        total_lap_time = total_lap_ticks / ticks_per_second
        self.playback_time_label.setText(f"{current_time_seconds:.3f}s / {total_lap_time:.3f}s")
