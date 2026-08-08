from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QComboBox,
)
from PySide6.QtCore import Qt, QTimer

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

from utils.color_utils import get_tyre_temp_color, interpolate_color


class TyresPageMixin:
    """Tyre Data page:
        -top-down live tyre temps
        -temp-coloured track map
        -lap-time/temp correlation
        -per-lap temperature progression chart
    """

    def make_tyres_page(self):
        page = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("Tyre Data Analysis")
        title.setStyleSheet("font-size: 38px; font-weight: bold; color: #000007;")
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        main_content = QHBoxLayout()
        main_content.setSpacing(15)

        left_column = QVBoxLayout()
        left_column.setSpacing(10)

        lap_selector_container = QWidget()
        lap_selector_container.setFixedWidth(int(280 * self.scale_factor))
        lap_selector_container.setStyleSheet("""
            QWidget { background-color: white; border-radius: 0px; border: none; }
        """)
        lap_selector_layout = QVBoxLayout(lap_selector_container)
        lap_selector_layout.setContentsMargins(2, 2, 3, 2)
        lap_selector_layout.setSpacing(0)

        lap_selector_title = QLabel("Select Lap")
        lap_selector_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000;")
        lap_selector_layout.addWidget(lap_selector_title)

        self.tyre_lap_list = QListWidget()
        self.tyre_lap_list.setMaximumHeight(int(900 * self.scale_factor))
        self.tyre_lap_list.setStyleSheet("""
            QListWidget { background-color: white; border: 1px solid #e5e7eb; border-radius: 4px; font-size: 18px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #f3f4f6; color: #000000; }
            QListWidget::item:selected { background-color: #2563eb; color: white; }
            QListWidget::item:hover { background-color: #eff6ff; color: #000000; }
        """)
        self.tyre_lap_list.itemClicked.connect(self.update_tyre_data_display)
        lap_selector_layout.addWidget(self.tyre_lap_list)

        for lap in sorted(self.lap_timings.keys()):
            lap_info = self.lap_timings[lap]
            item = QListWidgetItem(f"Lap {lap} - {lap_info['time_str']}")
            item.setData(Qt.UserRole, lap)
            self.tyre_lap_list.addItem(item)

        lap_selector_wrapper = QWidget()
        lap_selector_wrapper.setFixedWidth(int(284 * self.scale_factor))
        lap_selector_wrapper.setFixedHeight(int(900 * self.scale_factor))
        lap_selector_wrapper.setStyleSheet("""
            QWidget { background-color: white; border: 2px solid #000000; border-radius: 8px; }
        """)
        lap_selector_wrapper_layout = QVBoxLayout(lap_selector_wrapper)
        lap_selector_wrapper_layout.setContentsMargins(2, 2, 2, 2)
        lap_selector_wrapper_layout.addWidget(lap_selector_container)

        left_column.addWidget(lap_selector_wrapper)

        right_column = QVBoxLayout()
        right_column.setSpacing(10)

        top_row_container = QWidget()
        top_row_layout = QHBoxLayout(top_row_container)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(10)

        self.tyre_visual_container = QWidget()
        self.tyre_visual_layout = QVBoxLayout(self.tyre_visual_container)
        self.tyre_visual_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.addWidget(self.tyre_visual_container)

        self.tyre_map_container = QWidget()
        self.tyre_map_layout = QVBoxLayout(self.tyre_map_container)
        self.tyre_map_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.addWidget(self.tyre_map_container)

        right_column.addWidget(top_row_container)

        main_content.addLayout(left_column)
        main_content.addLayout(right_column)
        main_content.addStretch()

        layout.addLayout(main_content)

        bottom_row_container = QWidget()
        bottom_row_layout = QHBoxLayout(bottom_row_container)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.setSpacing(15)

        self.tyre_correlation_container = QWidget()
        self.tyre_correlation_layout = QVBoxLayout(self.tyre_correlation_container)
        self.tyre_correlation_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.addWidget(self.tyre_correlation_container)

        self.tyre_chart_container = QWidget()
        self.tyre_chart_layout = QVBoxLayout(self.tyre_chart_container)
        self.tyre_chart_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.addWidget(self.tyre_chart_container)

        layout.addWidget(bottom_row_container)
        layout.addStretch()

        scroll.setWidget(content_widget)

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        if self.tyre_lap_list.count() > 0:
            self.tyre_lap_list.setCurrentRow(0)
            self.update_tyre_data_display()

        return page

    def create_tyre_top_down_visual(self, lap):
        lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap].copy()
        if len(lap_data) == 0:
            return None

        tyres = {
            'LF': {'L': lap_data['LFtempL'].mean(), 'M': lap_data['LFtempM'].mean(), 'R': lap_data['LFtempR'].mean()},
            'RF': {'L': lap_data['RFtempL'].mean(), 'M': lap_data['RFtempM'].mean(), 'R': lap_data['RFtempR'].mean()},
            'LR': {'L': lap_data['LRtempL'].mean(), 'M': lap_data['LRtempM'].mean(), 'R': lap_data['LRtempR'].mean()},
            'RR': {'L': lap_data['RRtempL'].mean(), 'M': lap_data['RRtempM'].mean(), 'R': lap_data['RRtempR'].mean()},
        }

        fig = Figure(figsize=(10, 8), facecolor="#ffffff")
        ax = fig.add_subplot(111)
        self.tyre_top_down_ax = ax

        car_body = Rectangle((2.05, 0.8), 3.5, 6.5, facecolor='#9ca3af', edgecolor='#000000', linewidth=2)
        ax.add_patch(car_body)

        tyre_width = 1.6
        tyre_height = 2.1
        segment_width = tyre_width / 3

        tyre_positions = [
            (0.3, 5.5, 'LF', tyres['LF']),
            (5.7, 5.5, 'RF', tyres['RF']),
            (0.3, 0.2, 'LR', tyres['LR']),
            (5.7, 0.2, 'RR', tyres['RR']),
        ]

        for x, y, label, temps in tyre_positions:
            ax.text(x + tyre_width / 2, y + tyre_height + 0.3, label, ha='center', va='bottom',
                    fontsize=14, fontweight='bold', color='#000000')

            for i, (segment_label, temp) in enumerate([('L', temps['L']), ('M', temps['M']), ('R', temps['R'])]):
                color = get_tyre_temp_color(temp)
                segment = Rectangle((x + i * segment_width, y), segment_width, tyre_height,
                                     facecolor=color, edgecolor='#000000', linewidth=1.5)
                ax.add_patch(segment)

                text_x = x + i * segment_width + segment_width / 2
                text_y = y + tyre_height / 2
                ax.text(text_x, text_y, f'{temp:.0f}°', ha='center', va='center',
                        fontsize=10, fontweight='bold', color='white')

        ax.set_xlim(-0.5, 8.5)
        ax.set_ylim(-1.0, 9.5)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_aspect('auto')
        ax.set_title(f'Lap {lap} - Tyre Temperatures (Live)', fontsize=19, fontweight='bold', pad=1)

        fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.01)

        canvas = FigureCanvas(fig)
        canvas.setFixedSize(int(800 * self.scale_factor), int(850 * self.scale_factor))

        top_down_wrapper = QWidget()
        top_down_wrapper.setStyleSheet("""
            QWidget { background-color: white; border: 2px solid #000000; border-radius: 8px; }
        """)
        top_down_wrapper_layout = QVBoxLayout(top_down_wrapper)
        top_down_wrapper_layout.setContentsMargins(2, 2, 2, 2)
        top_down_wrapper_layout.addWidget(canvas)

        self.tyre_top_down_canvas = canvas
        return top_down_wrapper

    def create_tyre_temp_track_map(self, lap):
        lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap].copy()
        if len(lap_data) == 0:
            return None

        lap_data = lap_data.sort_values("SessionTick").reset_index(drop=True)

        avg_temps = (
            lap_data['LFtempL'] + lap_data['LFtempM'] + lap_data['LFtempR'] +
            lap_data['RFtempL'] + lap_data['RFtempM'] + lap_data['RFtempR'] +
            lap_data['LRtempL'] + lap_data['LRtempM'] + lap_data['LRtempR'] +
            lap_data['RRtempL'] + lap_data['RRtempM'] + lap_data['RRtempR']
        ) / 12

        fig = Figure(figsize=(8, 8), facecolor='#BFBEC1')
        ax = fig.add_subplot(111)

        points = np.array([lap_data["Lon"].values, lap_data["Lat"].values]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        colors = [get_tyre_temp_color(temp) for temp in avg_temps[:-1]]

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

        ax.set_title(f'Lap {lap} - Tyre Temperature Track Map', fontsize=14, fontweight='bold', pad=10)
        ax.set_aspect('equal')
        ax.set_facecolor('white')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(lap_data["Lon"].min() - 0.0005, lap_data["Lon"].max() + 0.0005)
        ax.set_ylim(lap_data["Lat"].min() - 0.0005, lap_data["Lat"].max() + 0.0005)

        fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02)

        canvas = FigureCanvas(fig)

        self.tyre_driver_dot, = ax.plot(lap_data["Lon"].iloc[0], lap_data["Lat"].iloc[0],
                                         'o', color='black', markersize=10, zorder=20)

        self.tyre_map_ax = ax

        canvas.setFixedSize(int(850 * self.scale_factor), int(850 * self.scale_factor))
        self.tyre_map_canvas = canvas
        return canvas

    def create_tyre_temp_colorbar(self):
        colorbar_container = QWidget()
        colorbar_container.setFixedWidth(int(155 * self.scale_factor))

        container_layout = QVBoxLayout(colorbar_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)

        title = QLabel("Temperature")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title)

        fig = Figure(figsize=(1.5, 6), facecolor='none')
        ax = fig.add_subplot(111)

        gradient = np.linspace(0, 1, 256).reshape(256, 1)

        color_array = np.zeros((256, 3))
        for i in range(256):
            temp = 50 + (110 - 50) * (i / 255)
            hex_color = get_tyre_temp_color(temp)
            rgb = [int(hex_color[j:j + 2], 16) / 255 for j in (1, 3, 5)]
            color_array[i] = rgb

        ax.imshow(gradient, aspect='auto', cmap=LinearSegmentedColormap.from_list('temp', color_array), origin='lower')

        ax.set_xticks([])
        ax.set_yticks([0, 64, 128, 192, 255])
        ax.set_yticklabels(['50°C', '65°C', '80°C', '95°C', '110°C'], fontsize=12)
        ax.tick_params(colors='#111827', labelsize=9)

        fig.subplots_adjust(left=0.5, right=0.85, top=0.98, bottom=0.02)

        canvas = FigureCanvas(fig)
        canvas.setFixedSize(int(180 * self.scale_factor), int(750 * self.scale_factor))

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(canvas)

        colorbar_widget = QWidget()
        colorbar_widget.setLayout(layout)
        container_layout.addWidget(colorbar_widget)

        return colorbar_container

    def create_tyre_temp_correlation(self):
        lap_numbers, lap_times, avg_temps = [], [], []

        for lap in sorted(self.lap_timings.keys()):
            lap_timing_data = self.lap_timings[lap]
            if lap_timing_data.get('is_outlap', False) or lap_timing_data.get('is_inlap', False):
                continue

            lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap].copy()
            if len(lap_data) == 0:
                continue

            avg_temp = (
                lap_data['LFtempL'].mean() + lap_data['LFtempM'].mean() + lap_data['LFtempR'].mean() +
                lap_data['RFtempL'].mean() + lap_data['RFtempM'].mean() + lap_data['RFtempR'].mean() +
                lap_data['LRtempL'].mean() + lap_data['LRtempM'].mean() + lap_data['LRtempR'].mean() +
                lap_data['RRtempL'].mean() + lap_data['RRtempM'].mean() + lap_data['RRtempR'].mean()
            ) / 12

            lap_time = lap_timing_data['time']
            if lap_time != float('inf'):
                lap_numbers.append(lap)
                lap_times.append(lap_time)
                avg_temps.append(avg_temp)

        if len(lap_times) == 0:
            return None

        fig = Figure(figsize=(10, 4), facecolor='#f8f9fa')
        ax = fig.add_subplot(111)

        ax.scatter(avg_temps, lap_times, s=int(150 * self.scale_factor), c=lap_numbers,
                   cmap='Pastel1', edgecolors='black', linewidths=1.3, zorder=3)

        for lap_num, temp, time in zip(lap_numbers, avg_temps, lap_times):
            ax.annotate(f'{lap_num}', (temp, time), fontsize=8, fontweight='bold', ha='center', va='center')

        if len(avg_temps) > 1:
            z = np.polyfit(avg_temps, lap_times, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(min(avg_temps), max(avg_temps), 100)
            ax.plot(x_trend, p(x_trend), '--', color='#ef4444', linewidth=2, alpha=0.7, label='Trend', zorder=2)

            correlation = np.corrcoef(avg_temps, lap_times)[0, 1]
            ax.text(0.98, 0.98, f'Correlation: {correlation:.3f}', transform=ax.transAxes,
                    ha='right', va='top', fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax.set_xlabel('Average Tyre Temperature (°C)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_ylabel('Lap Time (s)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_title('Lap Time vs Tyre Temperature Correlation', fontsize=13, fontweight='bold', color='#111827', pad=10)

        ax.set_facecolor('white')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.tick_params(colors='#111827', labelsize=int(10 * self.scale_factor))

        for spine in ax.spines.values():
            spine.set_edgecolor('#d1d5db')
            spine.set_linewidth(1)

        if len(avg_temps) > 1:
            ax.legend(loc='upper left', fontsize=9)

        fig.subplots_adjust(left=0.10, right=0.98, top=0.90, bottom=0.20)

        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(int(380 * self.scale_factor))
        canvas.setMinimumWidth(1)

        correlation_wrapper = QWidget()
        correlation_wrapper.setStyleSheet("""
            QWidget { background-color: white; border: 2px solid #000000; border-radius: 8px; }
        """)
        correlation_wrapper_layout = QVBoxLayout(correlation_wrapper)
        correlation_wrapper_layout.setContentsMargins(4, 4, 4, 4)
        correlation_wrapper_layout.addWidget(canvas)

        return correlation_wrapper

    def create_tyre_temp_line_chart(self, lap):
        lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap].copy()
        if len(lap_data) == 0:
            return None

        lap_data = lap_data.sort_values("SessionTick").reset_index(drop=True)

        lap_start_tick = lap_data["SessionTick"].iloc[0]
        time_seconds = (lap_data["SessionTick"] - lap_start_tick) / 60

        lf_avg = (lap_data['LFtempL'] + lap_data['LFtempM'] + lap_data['LFtempR']) / 3
        rf_avg = (lap_data['RFtempL'] + lap_data['RFtempM'] + lap_data['RFtempR']) / 3
        lr_avg = (lap_data['LRtempL'] + lap_data['LRtempM'] + lap_data['LRtempR']) / 3
        rr_avg = (lap_data['RRtempL'] + lap_data['RRtempM'] + lap_data['RRtempR']) / 3

        fig = Figure(figsize=(12, 4), facecolor='#f8f9fa')
        ax = fig.add_subplot(111)
        self.tyre_chart_ax = ax

        ax.plot(time_seconds, lf_avg, linewidth=2, label='LF', color='#3b82f6')
        ax.plot(time_seconds, rf_avg, linewidth=2, label='RF', color='#ef4444')
        ax.plot(time_seconds, lr_avg, linewidth=2, label='LR', color='#10b981')
        ax.plot(time_seconds, rr_avg, linewidth=2, label='RR', color='#f59e0b')

        # Optimal temp range - TODO: verify against real tyre spec sheet
        ax.axhspan(60, 80, alpha=0.1, color='green')

        self.tyre_sweep_line = ax.axvline(x=0, color='black', linewidth=2, linestyle='-', alpha=0.7, zorder=10)

        ax.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_ylabel('Temperature (°C)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_title(f'Lap {lap} - Tyre Temperature Progression', fontsize=13, fontweight='bold', color='#111827', pad=10)

        ax.set_facecolor('white')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.tick_params(colors='#111827', labelsize=int(10 * self.scale_factor))
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)

        for spine in ax.spines.values():
            spine.set_edgecolor('#d1d5db')
            spine.set_linewidth(1)

        fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.20)

        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(int(380 * self.scale_factor))
        self.tyre_chart_canvas = canvas

        chart_wrapper = QWidget()
        chart_wrapper.setStyleSheet("""
            QWidget { background-color: white; border: 2px solid #000000; border-radius: 8px; }
        """)
        chart_wrapper_layout = QVBoxLayout(chart_wrapper)
        chart_wrapper_layout.setContentsMargins(4, 4, 4, 4)
        chart_wrapper_layout.addWidget(canvas)

        return chart_wrapper

    def update_tyre_data_display(self):
        current_item = self.tyre_lap_list.currentItem()
        if not current_item:
            return

        selected_lap = current_item.data(Qt.UserRole)

        self.current_tyre_lap_data = self.telemetry_df[self.telemetry_df["Lap"] == selected_lap].copy()
        self.current_tyre_lap_data = self.current_tyre_lap_data.sort_values("SessionTick").reset_index(drop=True)

        self.tyre_playback_index = 0
        self.tyre_current_tick = 0
        self.tyre_playback_active = False

        if not hasattr(self, 'tyre_playback_timer'):
            self.tyre_playback_timer = QTimer()
            self.tyre_playback_timer.timeout.connect(self.tyre_playback_step)

        for layout_attr in (self.tyre_visual_layout, self.tyre_map_layout,
                             self.tyre_correlation_layout, self.tyre_chart_layout):
            while layout_attr.count():
                child = layout_attr.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        top_down = self.create_tyre_top_down_visual(selected_lap)
        if top_down:
            self.tyre_visual_layout.addWidget(top_down)

        track_map = self.create_tyre_temp_track_map(selected_lap)
        if track_map:
            map_with_colorbar = QWidget()
            map_colorbar_layout = QHBoxLayout(map_with_colorbar)
            map_colorbar_layout.setContentsMargins(0, 0, 0, 0)
            map_colorbar_layout.setSpacing(3)
            map_colorbar_layout.addWidget(track_map)

            colorbar = self.create_tyre_temp_colorbar()
            map_colorbar_layout.addWidget(colorbar)

            self.tyre_map_layout.addWidget(map_with_colorbar)

            controls = self.create_tyre_playback_controls()
            self.tyre_map_layout.addWidget(controls)

        correlation = self.create_tyre_temp_correlation()
        if correlation:
            self.tyre_correlation_layout.addWidget(correlation)

        line_chart = self.create_tyre_temp_line_chart(selected_lap)
        if line_chart:
            self.tyre_chart_layout.addWidget(line_chart)

        if len(self.current_tyre_lap_data) > 0:
            lap_start_tick = self.current_tyre_lap_data["SessionTick"].iloc[0]
            lap_end_tick = self.current_tyre_lap_data["SessionTick"].iloc[-1]
            total_time = (lap_end_tick - lap_start_tick) / 60
            self.tyre_playback_time_label.setText(f"0.000s / {total_time:.3f}s")

    def create_tyre_playback_controls(self):
        controls_widget = QWidget()
        controls_widget.setFixedHeight(int(50 * self.scale_factor))
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        controls_layout.setSpacing(int(10 * self.scale_factor))

        self.tyre_play_pause_btn = QPushButton("▶ Play")
        self.tyre_play_pause_btn.setFixedWidth(int(100 * self.scale_factor))
        self.tyre_play_pause_btn.setStyleSheet("""
            QPushButton { background-color: #2563eb; color: white; border-radius: 4px; font-size: 14px; font-weight: bold; padding: 5px; }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        self.tyre_play_pause_btn.clicked.connect(self.toggle_tyre_playback)

        self.tyre_reset_btn = QPushButton("↺ Reset")
        self.tyre_reset_btn.setFixedWidth(100)
        self.tyre_reset_btn.setStyleSheet("""
            QPushButton { background-color: #6b7280; color: white; border-radius: 4px; font-size: 14px; font-weight: bold; padding: 5px; }
            QPushButton:hover { background-color: #4b5563; }
        """)
        self.tyre_reset_btn.clicked.connect(self.reset_tyre_playback)

        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("font-size: 14px; font-weight: bold; color: black;")

        self.tyre_speed_selector = QComboBox()
        self.tyre_speed_selector.addItem("1x", 1)
        self.tyre_speed_selector.addItem("2x", 2)
        self.tyre_speed_selector.addItem("4x", 4)
        self.tyre_speed_selector.addItem("8x", 8)
        self.tyre_speed_selector.setFixedWidth(int(70 * self.scale_factor))
        self.tyre_speed_selector.setStyleSheet("QComboBox { color: black; padding: 3px; }")

        self.tyre_playback_time_label = QLabel("0.000s / 0.000s")
        self.tyre_playback_time_label.setStyleSheet("font-size: 14px; color: black; font-weight: bold;")

        controls_layout.addWidget(self.tyre_play_pause_btn)
        controls_layout.addWidget(self.tyre_reset_btn)
        controls_layout.addWidget(speed_label)
        controls_layout.addWidget(self.tyre_speed_selector)
        controls_layout.addWidget(self.tyre_playback_time_label)
        controls_layout.addStretch()

        return controls_widget

    def toggle_tyre_playback(self):
        if not hasattr(self, 'current_tyre_lap_data') or self.current_tyre_lap_data is None:
            return

        if self.tyre_playback_active:
            self.tyre_playback_timer.stop()
            self.tyre_playback_active = False
            self.tyre_play_pause_btn.setText("▶ Play")
        else:
            if self.tyre_playback_index >= len(self.current_tyre_lap_data) - 1:
                self.reset_tyre_playback()

            self.tyre_playback_active = True
            self.tyre_play_pause_btn.setText("⏸ Pause")
            self.tyre_playback_timer.start(50)

    def reset_tyre_playback(self):
        if hasattr(self, 'tyre_playback_timer'):
            self.tyre_playback_timer.stop()

        self.tyre_playback_active = False
        self.tyre_play_pause_btn.setText("▶ Play")
        self.tyre_playback_index = 0
        self.tyre_current_tick = 0

        if hasattr(self, 'current_tyre_lap_data') and self.current_tyre_lap_data is not None:
            if hasattr(self, 'tyre_driver_dot') and hasattr(self, 'tyre_map_canvas'):
                self.tyre_driver_dot.set_data(
                    [self.current_tyre_lap_data["Lon"].iloc[0]],
                    [self.current_tyre_lap_data["Lat"].iloc[0]]
                )
                self.tyre_map_canvas.draw()

            if hasattr(self, 'tyre_sweep_line'):
                self.tyre_sweep_line.set_xdata([0, 0])
                self.tyre_chart_canvas.draw_idle()

            lap_start_tick = self.current_tyre_lap_data["SessionTick"].iloc[0]
            lap_end_tick = self.current_tyre_lap_data["SessionTick"].iloc[-1]
            total_time = (lap_end_tick - lap_start_tick) / 60
            self.tyre_playback_time_label.setText(f"0.000s / {total_time:.3f}s")

            self.update_tyre_top_down_live(self.current_tyre_lap_data.iloc[0])

    def tyre_playback_step(self):
        if self.current_tyre_lap_data is None:
            return

        speed = self.tyre_speed_selector.currentData()
        ticks_per_second = 60
        tick_increment = int((0.05 * speed) * ticks_per_second)

        lap_start_tick = self.current_tyre_lap_data["SessionTick"].iloc[0]
        lap_end_tick = self.current_tyre_lap_data["SessionTick"].iloc[-1]
        total_lap_ticks = lap_end_tick - lap_start_tick

        if not hasattr(self, 'tyre_current_tick'):
            self.tyre_current_tick = 0

        self.tyre_current_tick += tick_increment

        if self.tyre_current_tick >= total_lap_ticks:
            self.tyre_playback_timer.stop()
            self.tyre_playback_active = False
            self.tyre_play_pause_btn.setText("▶ Play")
            self.tyre_current_tick = total_lap_ticks
            self.tyre_playback_index = len(self.current_tyre_lap_data) - 1
            current_row = self.current_tyre_lap_data.iloc[self.tyre_playback_index]
        else:
            target_tick = lap_start_tick + self.tyre_current_tick
            tick_diffs = (self.current_tyre_lap_data["SessionTick"] - target_tick).abs()
            self.tyre_playback_index = tick_diffs.idxmin()
            current_row = self.current_tyre_lap_data.loc[self.tyre_playback_index]

        if hasattr(self, 'tyre_driver_dot'):
            self.tyre_driver_dot.set_data([current_row["Lon"]], [current_row["Lat"]])
            self.tyre_map_canvas.draw_idle()

        if hasattr(self, 'tyre_sweep_line'):
            current_time_seconds = self.tyre_current_tick / ticks_per_second
            self.tyre_sweep_line.set_xdata([current_time_seconds, current_time_seconds])
            self.tyre_chart_canvas.draw_idle()

        self.update_tyre_top_down_live(current_row)

        current_time_seconds = self.tyre_current_tick / ticks_per_second
        total_lap_time = total_lap_ticks / ticks_per_second
        self.tyre_playback_time_label.setText(f"{current_time_seconds:.3f}s / {total_lap_time:.3f}s")

    def update_tyre_top_down_live(self, current_row):
        if not hasattr(self, 'tyre_top_down_ax'):
            return

        ax = self.tyre_top_down_ax

        while len(ax.patches) > 1:
            ax.patches[-1].remove()
        for text in list(ax.texts):
            text.remove()

        tyres = {
            'LF': {'L': current_row['LFtempL'], 'M': current_row['LFtempM'], 'R': current_row['LFtempR']},
            'RF': {'L': current_row['RFtempL'], 'M': current_row['RFtempM'], 'R': current_row['RFtempR']},
            'LR': {'L': current_row['LRtempL'], 'M': current_row['LRtempM'], 'R': current_row['LRtempR']},
            'RR': {'L': current_row['RRtempL'], 'M': current_row['RRtempM'], 'R': current_row['RRtempR']},
        }

        tyre_width = 1.6
        tyre_height = 2.1
        segment_width = tyre_width / 3

        tyre_positions = [
            (0.3, 5.5, 'LF', tyres['LF']),
            (5.7, 5.5, 'RF', tyres['RF']),
            (0.3, 0.2, 'LR', tyres['LR']),
            (5.7, 0.2, 'RR', tyres['RR']),
        ]

        for x, y, label, temps in tyre_positions:
            ax.text(x + tyre_width / 2, y + tyre_height + 0.3, label, ha='center', va='bottom',
                    fontsize=14, fontweight='bold', color='#000000')

            for i, (segment_label, temp) in enumerate([('L', temps['L']), ('M', temps['M']), ('R', temps['R'])]):
                color = get_tyre_temp_color(temp)
                segment = Rectangle((x + i * segment_width, y), segment_width, tyre_height,
                                     facecolor=color, edgecolor='#000000', linewidth=1.5)
                ax.add_patch(segment)

                text_x = x + i * segment_width + segment_width / 2
                text_y = y + tyre_height / 2
                ax.text(text_x, text_y, f'{temp:.0f}°', ha='center', va='center',
                        fontsize=10, fontweight='bold', color='white')

        self.tyre_top_down_canvas.draw_idle()

    # TODO: add overall session stats (highest recorded temp per tyre, per-lap max, etc.)
