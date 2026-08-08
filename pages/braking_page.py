from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QFrame, QTableWidget, QTableWidgetItem,
)
from PySide6.QtCore import Qt

from matplotlib.figure import Figure
import numpy as np

from widgets.zoomable_canvas import ZoomableCanvas
from analysis.lockup_detection import detect_all_lockups


class ClickableLockupCanvas(ZoomableCanvas):
    """A ZoomableCanvas that also handles picking a lockup marker and
    selecting the corresponding row in the lockup table, this is works bilaterally 
    users can highlight a lockup on track map by interacting with table and vice versa by interacting with lockup on track map"""

    def __init__(self, fig, parent_window):
        super().__init__(fig)
        self.parent_window = parent_window
        self.mpl_connect('pick_event', self.on_pick)

    def on_pick(self, event):
        if (event.artist != self.parent_window.lockup_scatter and
                event.artist != getattr(self.parent_window, 'lockup_scatter_normal', None)):
            return

        ind = event.ind[0]
        clicked_point = event.artist.get_offsets()[ind]
        clicked_lon = clicked_point[0]
        clicked_lat = clicked_point[1]

        for row_idx, lockup in enumerate(self.parent_window.lockup_all_events):
            if abs(lockup['lon'] - clicked_lon) < 0.000001 and abs(lockup['lat'] - clicked_lat) < 0.000001:
                self.parent_window.lockup_table_widget.selectRow(row_idx)
                self.parent_window.highlight_selected_lockup(self.parent_window.lockup_table_widget)
                break


class BrakingPageMixin:
    """Braking Analysis / Lockup Detection page."""

    def make_braking_page(self):
        page = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        title = QLabel("Braking Analysis - Lockup Detection")
        title.setStyleSheet("font-size: 45px; font-weight: bold; color: #000007;")
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        wheel_filter_container = QWidget()
        wheel_filter_layout = QHBoxLayout(wheel_filter_container)
        wheel_filter_layout.setContentsMargins(0, 0, 0, 0)
        wheel_filter_layout.setSpacing(10)

        filter_label = QLabel("Show Wheels:")
        filter_label.setStyleSheet("font-size: 15px;")
        wheel_filter_layout.addWidget(filter_label)

        self.lockup_wheel_toggles = {}
        for wheel_name in ['LF', 'RF', 'LR', 'RR']:
            btn = QPushButton(wheel_name)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedSize(int(50 * self.scale_factor), int(30 * self.scale_factor))
            btn.setStyleSheet("""
                QPushButton { background-color: #e5e7eb; color: #6b7280; border: 1px solid #d1d5db; border-radius: 4px; font-size: 14px; font-weight: bold; }
                QPushButton:checked { background-color: #2563eb; color: white; border: 1px solid #2563eb; }
                QPushButton:hover { background-color: #d1d5db; }
                QPushButton:checked:hover { background-color: #1d4ed8; }
            """)
            btn.clicked.connect(self.update_lockup_display)
            self.lockup_wheel_toggles[wheel_name] = btn
            wheel_filter_layout.addWidget(btn)

        wheel_filter_layout.addStretch()
        layout.addWidget(wheel_filter_container)

        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)

        self.lockup_map_container = QWidget()
        self.lockup_map_layout = QVBoxLayout(self.lockup_map_container)
        self.lockup_map_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.lockup_map_container)

        lap_selector_container = QWidget()
        lap_selector_container.setFixedWidth(int(250 * self.scale_factor))
        lap_selector_container.setStyleSheet("""
            QWidget { background-color: white; border-radius: 0px; border: none; }
        """)
        lap_selector_layout = QVBoxLayout(lap_selector_container)
        lap_selector_layout.setContentsMargins(10, 10, 10, 10)
        lap_selector_layout.setSpacing(10)

        selector_title = QLabel("Select Laps")
        selector_title.setStyleSheet("font-size: 17px;")
        lap_selector_layout.addWidget(selector_title)

        self.lockup_all_laps_cb = QCheckBox("All Laps")
        self.lockup_all_laps_cb.setChecked(True)
        self.lockup_all_laps_cb.setStyleSheet("""
            QCheckBox { font-size: 18px; color: #111827; font-weight: bold; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #9ca3af; border-radius: 3px; background-color: white; }
            QCheckBox::indicator:checked { background-color: #2563eb; border-color: #2563eb; }
        """)
        self.lockup_all_laps_cb.stateChanged.connect(self.toggle_all_lockup_laps)
        lap_selector_layout.addWidget(self.lockup_all_laps_cb)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #e5e7eb; max-height: 1px;")
        lap_selector_layout.addWidget(separator)

        lap_scroll = QScrollArea()
        lap_scroll.setWidgetResizable(True)
        lap_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lap_scroll.setStyleSheet("border: none; background-color: white;")

        lap_scroll_widget = QWidget()
        self.lockup_lap_cb_layout = QVBoxLayout(lap_scroll_widget)
        self.lockup_lap_cb_layout.setContentsMargins(0, 0, 0, 0)
        self.lockup_lap_cb_layout.setSpacing(8)
        self.lockup_lap_cb_layout.setAlignment(Qt.AlignTop)

        lap_scroll.setWidget(lap_scroll_widget)
        lap_selector_layout.addWidget(lap_scroll)

        lap_selector_wrapper = QWidget()
        lap_selector_wrapper.setFixedWidth(int(258 * self.scale_factor))
        lap_selector_wrapper.setStyleSheet("""
            QWidget#lap_wrapper { background-color: white; border: 2px solid #000000; border-radius: 8px; }
        """)
        lap_selector_wrapper.setObjectName("lap_wrapper")
        lap_selector_wrapper_layout = QVBoxLayout(lap_selector_wrapper)
        lap_selector_wrapper_layout.setContentsMargins(2, 2, 2, 2)
        lap_selector_wrapper_layout.addWidget(lap_selector_container)

        content_layout.addWidget(lap_selector_wrapper)
        content_layout.addWidget(self.lockup_map_container)

        layout.addWidget(content_container)

        self.lockup_stats_container = QWidget()
        self.lockup_stats_layout = QVBoxLayout(self.lockup_stats_container)
        self.lockup_stats_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.lockup_stats_container)

        layout.addStretch()

        scroll.setWidget(content_widget)

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        self.lockup_lap_checkboxes = {}
        self.detect_all_lockups()
        self.populate_lockup_lap_selector()
        self.update_lockup_display()

        return page

    def create_lockup_table(self):
        all_events = []
        for wheel_name, lockups in self.all_lockups.items():
            for lockup in lockups:
                all_events.append(lockup)

        all_events.sort(key=lambda x: (x['lap'], x['idx']))

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['Lap', 'Tyre', 'Max Temp (°C)', 'Brake (%)', 'Length (s)'])
        table.setRowCount(len(all_events))

        table.verticalHeader().setDefaultSectionSize(int(35 * self.scale_factor))

        table.setStyleSheet("""
            QTableWidget { background-color: white; gridline-color: #9ca3af; font-size: 19px; border: none; border-radius: 0px; outline: none; }
            QHeaderView::section {
                background-color: #f3f4f6; color: #111827; font-weight: bold; font-size: 16px; border: none;
                border-right: 1px solid #9ca3af; border-bottom: 2px solid #9ca3af; border-left: 1px solid #9ca3af; padding: 15px;
            }
            QHeaderView::section:first { border-left: 1px solid #d1d5db; }
            QTableWidget::item { padding: 19px; border-bottom: 1px solid #9ca3af; border-right: 1px solid #9ca3af; border-left: 1px solid #9ca3af; color: #000000; outline: none; }
            QTableWidget::item:selected { background-color: #3b82f6; color: white; }
            QTableWidget::item:focus { outline: none; }
        """)

        for row, event in enumerate(all_events):
            lap_item = QTableWidgetItem()
            lap_item.setData(Qt.ItemDataRole.DisplayRole, int(event['lap']))
            lap_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            table.setItem(row, 0, lap_item)

            tyre_item = QTableWidgetItem(event['wheel'])
            tyre_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            table.setItem(row, 1, tyre_item)

            temp_item = QTableWidgetItem()
            temp_item.setData(Qt.ItemDataRole.DisplayRole, float(event['max_temp']))
            temp_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            table.setItem(row, 2, temp_item)

            brake_item = QTableWidgetItem()
            brake_item.setData(Qt.ItemDataRole.DisplayRole, float(event['brake']))
            brake_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            table.setItem(row, 3, brake_item)

            duration_item = QTableWidgetItem()
            duration_item.setData(Qt.ItemDataRole.DisplayRole, float(event['duration']))
            duration_item.setText(f"{event['duration']:.2f}")
            duration_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            table.setItem(row, 4, duration_item)

        table.setSortingEnabled(True)
        table.setMaximumWidth(int(850 * self.scale_factor))
        table.setMinimumWidth(int(850 * self.scale_factor))

        table_container = QWidget()
        table_container.setStyleSheet("""
            QWidget { background-color: white; border: 2px solid #000000; border-radius: 8px; }
        """)
        table_container_layout = QVBoxLayout(table_container)
        table_container_layout.setContentsMargins(int(10 * self.scale_factor), int(10 * self.scale_factor),
                                                    int(10 * self.scale_factor), int(10 * self.scale_factor))
        table_container_layout.addWidget(table)

        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnWidth(0, int(80 * self.scale_factor))
        table.setColumnWidth(1, int(150 * self.scale_factor))
        table.setColumnWidth(2, int(200 * self.scale_factor))
        table.setColumnWidth(3, int(180 * self.scale_factor))
        table.setColumnWidth(4, int(120 * self.scale_factor))

        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.lockup_all_events = all_events
        table.itemSelectionChanged.connect(lambda: self.highlight_selected_lockup(table))
        self.lockup_table_widget = table

        return table_container

    def highlight_selected_lockup(self, table):
        selected_rows = table.selectionModel().selectedRows()
        if not selected_rows or not hasattr(self, 'lockup_scatter'):
            return

        selected_row = selected_rows[0].row()
        selected_event = self.lockup_all_events[selected_row]

        highlight_lons, highlight_lats = [], []
        normal_lons, normal_lats = [], []

        for lockup in self.lockup_metadata:
            if (lockup['lap'] == selected_event['lap'] and
                    abs(lockup['lon'] - selected_event['lon']) < 0.000001 and
                    abs(lockup['lat'] - selected_event['lat']) < 0.000001):
                highlight_lons.append(lockup['lon'])
                highlight_lats.append(lockup['lat'])
            else:
                normal_lons.append(lockup['lon'])
                normal_lats.append(lockup['lat'])

        self.lockup_scatter.remove()
        if hasattr(self, 'lockup_scatter_normal'):
            self.lockup_scatter_normal.remove()

        if normal_lons:
            self.lockup_scatter_normal = self.lockup_map_ax.scatter(
                normal_lons, normal_lats, color='#ef4444', s=150, alpha=0.6, zorder=5, picker=True, pickradius=15)

        if highlight_lons:
            self.lockup_scatter = self.lockup_map_ax.scatter(
                highlight_lons, highlight_lats, color='#3b82f6', s=250, alpha=0.9, zorder=10,
                picker=True, pickradius=15, edgecolors='white', linewidths=3)

        self.lockup_map_canvas.draw_idle()

    def populate_lockup_lap_selector(self):
        while self.lockup_lap_cb_layout.count():
            child = self.lockup_lap_cb_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.lockup_lap_checkboxes = {}

        for lap in sorted(self.lap_timings.keys()):
            has_lockup = any(any(l['lap'] == lap for l in lockups) for lockups in self.all_lockups.values())

            cb_text = f"Lap {lap}" + (" ⚠️" if has_lockup else "")

            cb = QCheckBox(cb_text)
            cb.setChecked(True)
            cb.setStyleSheet("""
                QCheckBox { font-size: 17px; font-weight: bold; color: #374151; }
                QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #9ca3af; border-radius: 3px; background-color: white; }
                QCheckBox::indicator:checked { background-color: #2563eb; border-color: #2563eb; }
            """)
            cb.stateChanged.connect(self.update_lockup_display)

            self.lockup_lap_checkboxes[lap] = cb
            self.lockup_lap_cb_layout.addWidget(cb)

    def toggle_all_lockup_laps(self, state):
        is_checked = (state == Qt.Checked)
        for cb in self.lockup_lap_checkboxes.values():
            cb.setChecked(is_checked)

    def update_lockup_display(self):
        selected_laps = [lap for lap, cb in self.lockup_lap_checkboxes.items() if cb.isChecked()]

        if not selected_laps:
            selected_laps = list(self.lap_timings.keys())

        for layout_attr in (self.lockup_map_layout, self.lockup_stats_layout):
            while layout_attr.count():
                child = layout_attr.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        map_and_table_container = QWidget()
        map_and_table_layout = QHBoxLayout(map_and_table_container)
        map_and_table_layout.setContentsMargins(0, 0, 0, 0)
        map_and_table_layout.setSpacing(15)

        map_widget = self.create_lockup_track_map(selected_laps)
        if map_widget:
            map_and_table_layout.addWidget(map_widget)

        table_widget = self.create_lockup_table()
        if table_widget:
            map_and_table_layout.addWidget(table_widget)

        map_and_table_layout.addStretch()
        self.lockup_map_layout.addWidget(map_and_table_container)

        stats_widget = self.create_lockup_stats(selected_laps)
        if stats_widget:
            self.lockup_stats_layout.addWidget(stats_widget)

    def create_lockup_track_map(self, selected_laps):
        first_lap = sorted(self.lap_timings.keys())[0]
        lap_data = self.telemetry_df[self.telemetry_df["Lap"] == first_lap].copy()

        if len(lap_data) == 0:
            return None

        lap_data = lap_data.sort_values("SessionTick")

        fig = Figure(figsize=(12, 10), facecolor='#BFBEC1')
        ax = fig.add_subplot(111)
        self.lockup_map_ax = ax

        ax.plot(lap_data["Lon"], lap_data["Lat"], linewidth=8, color='#d1d5db', zorder=1, alpha=0.8)

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
                color='black', linewidth=4, zorder=10)

        selected_wheels = self.get_selected_lockup_wheels()

        all_lons, all_lats = [], []
        self.lockup_metadata = []

        for wheel_name in selected_wheels:
            lockups = self.all_lockups[wheel_name]
            wheel_lockups = [l for l in lockups if l['lap'] in selected_laps]

            if wheel_lockups:
                all_lons.extend([l['lon'] for l in wheel_lockups])
                all_lats.extend([l['lat'] for l in wheel_lockups])
                self.lockup_metadata.extend(wheel_lockups)

        if all_lons:
            self.lockup_scatter = ax.scatter(all_lons, all_lats, color='#ef4444', s=150, alpha=0.6,
                                              zorder=5, picker=True, pickradius=15)
        else:
            self.lockup_metadata = []

        ax.set_title('Lockup Locations', fontsize=16, fontweight='bold', pad=10)
        ax.set_aspect('equal')
        ax.set_facecolor('white')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(lap_data["Lon"].min() - 0.0005, lap_data["Lon"].max() + 0.0005)
        ax.set_ylim(lap_data["Lat"].min() - 0.0005, lap_data["Lat"].max() + 0.0005)

        fig.subplots_adjust(left=0.001, right=0.999, top=0.95, bottom=0.001)

        self.lockup_map_canvas = ClickableLockupCanvas(fig, self)
        self.lockup_map_canvas.setFixedSize(int(880 * self.scale_factor), int(870 * self.scale_factor))

        return self.lockup_map_canvas

    def get_selected_lockup_wheels(self):
        if not hasattr(self, 'lockup_wheel_toggles'):
            return ['LF', 'RF', 'LR', 'RR']

        selected = [name for name, toggle in self.lockup_wheel_toggles.items() if toggle.isChecked()]
        return selected if selected else ['LF', 'RF', 'LR', 'RR']

    def create_lockup_stats(self, selected_laps):
        total_lockups = 0
        wheel_counts = {'LF': 0, 'RF': 0, 'LR': 0, 'RR': 0}

        for wheel_name, lockups in self.all_lockups.items():
            count = sum(1 for l in lockups if l['lap'] in selected_laps)
            wheel_counts[wheel_name] = count
            total_lockups += count

        avg_per_lap = total_lockups / len(selected_laps) if selected_laps else 0

        stats_container = QWidget()
        stats_container.setFixedHeight(int(115 * self.scale_factor))
        stats_container.setStyleSheet("""
            QWidget { background-color: white; border-radius: 8px; border: 1px solid #e5e7eb; }
        """)

        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(20, 10, 20, 10)
        stats_layout.setSpacing(30)

        stats_layout.addWidget(self.create_stat_box("Total Lockups", f"{total_lockups}"))
        stats_layout.addWidget(self.create_stat_box("Avg per Lap", f"{avg_per_lap:.1f}"))

        for wheel_name, count in wheel_counts.items():
            stats_layout.addWidget(self.create_stat_box(f"{wheel_name} Lockups", f"{count}"))

        stats_layout.addStretch()

        stats_wrapper = QWidget()
        stats_wrapper.setStyleSheet("""
            QWidget { background-color: white; border: 3px solid #000000; border-radius: 8px; }
        """)
        stats_wrapper_layout = QVBoxLayout(stats_wrapper)
        stats_wrapper_layout.setContentsMargins(2, 2, 2, 2)
        stats_wrapper_layout.addWidget(stats_container)

        return stats_wrapper

    def create_stat_box(self, label, value):
        stat_widget = QWidget()
        stat_layout = QVBoxLayout(stat_widget)
        stat_layout.setContentsMargins(0, 0, 0, 0)
        stat_layout.setSpacing(5)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 14px; color: #6b7280; font-weight: 500;")

        value_widget = QLabel(value)
        value_widget.setStyleSheet("font-size: 28px; color: #111827; font-weight: bold;")

        stat_layout.addWidget(label_widget)
        stat_layout.addWidget(value_widget)
        return stat_widget

    def select_table_row_by_lap(self, lap_num):
        if not hasattr(self, 'lockup_table_widget'):
            return

        sorted_laps = sorted(self.lockup_lap_groups.keys())
        try:
            row_index = sorted_laps.index(lap_num)
            self.lockup_table_widget.selectRow(row_index)
        except (ValueError, AttributeError):
            pass
