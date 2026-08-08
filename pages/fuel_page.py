from PySide6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap
import numpy as np

from utils.color_utils import interpolate_color, brighten_color

# future plans to create a more robust L t0 Kg conversion using a custom made vehicle_detection method which can more accurately provide a conversion value
# however at this current point in time I am using a general .75 conversion value as typical densities can range anywhere from 0.715 to 0.8 across disciplines/series
FUEL_DENSITY = 0.75  


class FuelPageMixin:
    """Fuel Data page: usage/level charts, lap-time correlation, and a per-lap fuel consumption-rate track map."""

    def make_fuel_page(self):
        page = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        title = QLabel("Fuel Data Analysis")
        title.setStyleSheet("font-size: 38px; font-weight: bold; color: #000007;")
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        stats_bar = self.create_fuel_stats_bar()
        layout.addWidget(stats_bar)

        top_row_container = QWidget()
        top_row_layout = QHBoxLayout(top_row_container)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(15)

        self.fuel_track_container = QWidget()
        self.fuel_track_layout = QVBoxLayout(self.fuel_track_container)
        self.fuel_track_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.addWidget(self.fuel_track_container)

        fuel_chart_container = QWidget()
        fuel_chart_layout = QVBoxLayout(fuel_chart_container)
        fuel_chart_layout.setContentsMargins(0, 0, 0, 0)
        fuel_chart_layout.setSpacing(5)

        toggle_container = QWidget()
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(int(10 * self.scale_factor))

        toggle_label = QLabel("View:")
        toggle_label.setStyleSheet("font-size: 12px; color: black; font-weight: bold;")
        toggle_layout.addWidget(toggle_label)

        self.fuel_bar_btn = QPushButton("Usage per Lap")
        self.fuel_line_btn = QPushButton("Fuel Level")
        self.fuel_bar_btn.setCheckable(True)
        self.fuel_line_btn.setCheckable(True)
        self.fuel_bar_btn.setChecked(True)
        self.fuel_bar_btn.setFixedSize(120, 30)
        self.fuel_line_btn.setFixedSize(100, 30)

        fuel_toggle_style = """
            QPushButton { background-color: #e5e7eb; color: #6b7280; border: 1px solid #d1d5db; border-radius: 4px; font-size: 11px; font-weight: bold; }
            QPushButton:checked { background-color: #2563eb; color: white; border: 1px solid #2563eb; }
            QPushButton:hover { background-color: #d1d5db; }
            QPushButton:checked:hover { background-color: #1d4ed8; }
        """
        self.fuel_bar_btn.setStyleSheet(fuel_toggle_style)
        self.fuel_line_btn.setStyleSheet(fuel_toggle_style)

        self.fuel_bar_btn.clicked.connect(lambda: self.toggle_fuel_chart("bar"))
        self.fuel_line_btn.clicked.connect(lambda: self.toggle_fuel_chart("line"))

        toggle_layout.addWidget(self.fuel_bar_btn)
        toggle_layout.addWidget(self.fuel_line_btn)
        toggle_layout.addStretch()

        fuel_chart_layout.addWidget(toggle_container)

        self.fuel_chart_container_widget = QWidget()
        self.fuel_chart_container_layout = QVBoxLayout(self.fuel_chart_container_widget)
        self.fuel_chart_container_layout.setContentsMargins(0, 0, 0, 0)
        fuel_chart_layout.addWidget(self.fuel_chart_container_widget)

        top_row_layout.addWidget(fuel_chart_container)
        layout.addWidget(top_row_container)
        layout.addSpacing(20)

        self.fuel_correlation_container = QWidget()
        self.fuel_correlation_layout = QVBoxLayout(self.fuel_correlation_container)
        self.fuel_correlation_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.fuel_correlation_container)

        layout.addStretch()

        scroll.setWidget(content_widget)

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        self.current_fuel_chart_mode = "bar"
        self.selected_fuel_lap = None
        self.update_fuel_displays()

        return page

    def create_fuel_stats_bar(self):
        initial_fuel_l = self.telemetry_df['FuelLevel'].max()
        total_used_l = initial_fuel_l - self.telemetry_df['FuelLevel'].min()

        lap_usage = {}
        for lap in sorted(self.lap_timings.keys()):
            lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap]
            if len(lap_data) > 0:
                usage = lap_data['FuelLevel'].iloc[0] - lap_data['FuelLevel'].iloc[-1]
                if usage > 0:
                    lap_usage[lap] = usage

        avg_per_lap_l = sum(lap_usage.values()) / len(lap_usage) if lap_usage else 0

        if lap_usage:
            most_used_lap = max(lap_usage, key=lap_usage.get)
            most_used_l = lap_usage[most_used_lap]
            least_used_lap = min(lap_usage, key=lap_usage.get)
            least_used_l = lap_usage[least_used_lap]
        else:
            most_used_lap = None
            most_used_l = 0
            least_used_lap = None
            least_used_l = 0

        initial_fuel_kg = initial_fuel_l * FUEL_DENSITY
        total_used_kg = total_used_l * FUEL_DENSITY
        avg_per_lap_kg = avg_per_lap_l * FUEL_DENSITY
        most_used_kg = most_used_l * FUEL_DENSITY
        least_used_kg = least_used_l * FUEL_DENSITY

        stats_container = QWidget()
        stats_container.setFixedHeight(int(120 * self.scale_factor))
        stats_container.setStyleSheet("""
            QWidget { background-color: white; border-radius: 8px; border: 1px solid #e5e7eb; }
        """)

        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(20, 10, 20, 10)
        stats_layout.setSpacing(30)

        stats = [
            ("Initial Fuel", f"{initial_fuel_l:.1f}L ({initial_fuel_kg:.1f}kg)"),
            ("Total Used", f"{total_used_l:.1f}L ({total_used_kg:.1f}kg)"),
            ("Avg per Lap", f"{avg_per_lap_l:.2f}L ({avg_per_lap_kg:.2f}kg)"),
            ("Most Used Lap", f"Lap {most_used_lap}: {most_used_l:.2f}L ({most_used_kg:.2f}kg)" if most_used_lap else "N/A"),
            ("Least Used Lap", f"Lap {least_used_lap}: {least_used_l:.2f}L ({least_used_kg:.2f}kg)" if least_used_lap else "N/A"),
        ]

        for label, value in stats:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(0, 0, 0, 0)
            stat_layout.setSpacing(2)

            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-size: 18px; color: #6b7280; font-weight: bold;")

            value_widget = QLabel(value)
            value_widget.setStyleSheet("font-size: 20px; color: #111827; font-weight: bold;")

            stat_layout.addWidget(label_widget)
            stat_layout.addWidget(value_widget)
            stats_layout.addWidget(stat_widget)

        stats_layout.addStretch()

        stats_wrapper = QWidget()
        stats_wrapper.setStyleSheet("""
            QWidget { background-color: white; border: 2px solid #000000; border-radius: 8px; }
        """)
        stats_wrapper_layout = QVBoxLayout(stats_wrapper)
        stats_wrapper_layout.setContentsMargins(2, 2, 2, 2)
        stats_wrapper_layout.addWidget(stats_container)

        return stats_wrapper

    def toggle_fuel_chart(self, mode):
        if mode == "line":
            self.fuel_line_btn.setChecked(True)
            self.fuel_bar_btn.setChecked(False)
            self.current_fuel_chart_mode = "line"
        else:
            self.fuel_line_btn.setChecked(False)
            self.fuel_bar_btn.setChecked(True)
            self.current_fuel_chart_mode = "bar"

        self.update_fuel_displays()

    def update_fuel_displays(self):
        for layout_attr in (self.fuel_chart_container_layout, self.fuel_correlation_layout, self.fuel_track_layout):
            while layout_attr.count():
                child = layout_attr.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        if self.current_fuel_chart_mode == "line":
            fuel_chart = self.create_fuel_level_line_chart()
        else:
            fuel_chart = self.create_fuel_usage_bar_chart()

        if fuel_chart:
            self.fuel_chart_container_layout.addWidget(fuel_chart)

        correlation = self.create_fuel_laptime_correlation()
        if correlation:
            self.fuel_correlation_layout.addWidget(correlation)

        track_map = self.create_fuel_track_map(self.selected_fuel_lap or sorted(self.lap_timings.keys())[0])
        if track_map:
            self.fuel_track_layout.addWidget(track_map)

    def create_fuel_level_line_chart(self):
        fig = Figure(figsize=(10, 5), facecolor='#f8f9fa')
        ax = fig.add_subplot(111)

        all_laps = sorted(self.lap_timings.keys())
        lap_distances, fuel_levels = [], []

        for lap in all_laps:
            lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap].copy()
            if len(lap_data) == 0:
                continue
            lap_data = lap_data.sort_values("LapDistPct")
            for _, row in lap_data.iterrows():
                lap_distances.append(lap + (row["LapDistPct"] / 100))
                fuel_levels.append(row["FuelLevel"])

        if len(lap_distances) == 0:
            return None

        ax.plot(lap_distances, fuel_levels, linewidth=2, color='#2563eb')
        ax.fill_between(lap_distances, 0, fuel_levels, alpha=0.2, color='#2563eb')

        for lap in all_laps:
            ax.axvline(x=lap, color='#9ca3af', linewidth=1, linestyle='-', alpha=0.5, zorder=1)

        ax.set_xlabel('Lap Progress', fontsize=11, fontweight='bold', color='#111827')
        ax.set_ylabel('Fuel Level (L)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_title('Fuel Level Over Session', fontsize=13, fontweight='bold', color='#111827', pad=10)

        ax.set_facecolor('white')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.tick_params(colors='#111827', labelsize=10)

        for spine in ax.spines.values():
            spine.set_edgecolor('#d1d5db')
            spine.set_linewidth(1)

        fig.subplots_adjust(left=0.10, right=0.98, top=0.90, bottom=0.15)

        canvas = self._make_fuel_canvas(fig, int(600 * self.scale_factor))

        wrapper = QWidget()
        wrapper.setStyleSheet("QWidget { background-color: white; border: 2px solid #000000; border-radius: 8px; }")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(3, 3, 3, 3)
        wrapper_layout.addWidget(canvas)
        return wrapper

    @staticmethod
    def _make_fuel_canvas(fig, fixed_height):
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(fixed_height)
        return canvas

    def create_fuel_usage_bar_chart(self):
        lap_usage = {}
        for lap in sorted(self.lap_timings.keys()):
            lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap]
            if len(lap_data) > 0:
                usage = lap_data['FuelLevel'].iloc[0] - lap_data['FuelLevel'].iloc[-1]
                if usage > 0:
                    lap_usage[lap] = usage

        if not lap_usage:
            return None

        laps = list(lap_usage.keys())
        usages = list(lap_usage.values())

        fig = Figure(figsize=(10, 9), facecolor='#f8f9fa')
        ax = fig.add_subplot(111)

        self.fuel_bar_ax = ax
        self.fuel_bar_laps = laps
        self.fuel_bar_usages = usages

        min_usage = min(usages)
        max_usage = max(usages)

        colors = []
        for usage in usages:
            ratio = (usage - min_usage) / (max_usage - min_usage) if max_usage > min_usage else 0
            if ratio < 0.5:
                color = interpolate_color('#22c55e', '#eab308', ratio * 2)
            else:
                color = interpolate_color('#eab308', '#ef4444', (ratio - 0.5) * 2)
            colors.append(color)

        self.fuel_bar_colors = colors.copy()

        bars = ax.bar(laps, usages, color=colors, edgecolor='#000000', linewidth=1)
        self.fuel_bars = bars

        if self.selected_fuel_lap and self.selected_fuel_lap in laps:
            idx = laps.index(self.selected_fuel_lap)
            bars[idx].set_color('#2563eb')

        y_range = max_usage - min_usage
        y_margin = y_range * 0.1 if y_range > 0 else 0.1
        y_min = min_usage - y_margin if min_usage - y_margin > 0 else 0

        ax.set_ylim(y_min, max_usage + y_margin)

        ax.set_xlabel('Lap Number', fontsize=11, fontweight='bold', color='#111827')
        ax.set_ylabel('Fuel Used (L)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_title('Fuel Usage per Lap (Click to select)', fontsize=13, fontweight='bold', color='#111827', pad=10)

        ax.set_facecolor('white')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
        ax.tick_params(colors='#111827', labelsize=10)
        ax.set_xticks(laps)

        for spine in ax.spines.values():
            spine.set_edgecolor('#d1d5db')
            spine.set_linewidth(1)

        fig.subplots_adjust(left=0.10, right=0.98, top=0.92, bottom=0.10)

        canvas = self._make_fuel_canvas(fig, int(600 * self.scale_factor))
        canvas.mpl_connect('motion_notify_event', self.on_fuel_bar_hover)
        canvas.mpl_connect('button_press_event', self.on_fuel_bar_click)
        self.fuel_bar_canvas = canvas

        wrapper = QWidget()
        wrapper.setStyleSheet("QWidget { background-color: white; border: 2px solid #000000; border-radius: 8px; }")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(3, 3, 3, 3)
        wrapper_layout.addWidget(canvas)
        return wrapper

    def on_fuel_bar_hover(self, event):
        if not hasattr(self, 'fuel_bars') or event.inaxes != self.fuel_bar_ax:
            return

        for i, bar in enumerate(self.fuel_bars):
            if self.selected_fuel_lap and self.fuel_bar_laps[i] == self.selected_fuel_lap:
                bar.set_color('#2563eb')
            else:
                bar.set_color(self.fuel_bar_colors[i])

        for i, (bar, lap) in enumerate(zip(self.fuel_bars, self.fuel_bar_laps)):
            if bar.contains(event)[0]:
                if not self.selected_fuel_lap or lap != self.selected_fuel_lap:
                    bar.set_color(brighten_color(self.fuel_bar_colors[i], 1.3))
                break

        self.fuel_bar_canvas.draw_idle()

    def on_fuel_bar_click(self, event):
        if not hasattr(self, 'fuel_bars') or event.inaxes != self.fuel_bar_ax:
            return

        for i, bar in enumerate(self.fuel_bars):
            if bar.contains(event)[0]:
                self.selected_fuel_lap = self.fuel_bar_laps[i]

                for j, b in enumerate(self.fuel_bars):
                    b.set_color('#2563eb' if j == i else self.fuel_bar_colors[j])

                self.fuel_bar_canvas.draw_idle()

                while self.fuel_track_layout.count():
                    child = self.fuel_track_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

                track_map = self.create_fuel_track_map(self.selected_fuel_lap)
                if track_map:
                    self.fuel_track_layout.addWidget(track_map)
                break

    def create_fuel_laptime_correlation(self):
        lap_numbers, lap_times, fuel_loads = [], [], []

        for lap in sorted(self.lap_timings.keys()):
            lap_timing_data = self.lap_timings[lap]
            if lap_timing_data.get('is_outlap', False) or lap_timing_data.get('is_inlap', False):
                continue

            lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap]
            if len(lap_data) == 0:
                continue

            avg_fuel = lap_data['FuelLevel'].mean()
            lap_time = lap_timing_data['time']

            if lap_time != float('inf'):
                lap_numbers.append(lap)
                lap_times.append(lap_time)
                fuel_loads.append(avg_fuel)

        if len(lap_times) == 0:
            return None

        fig = Figure(figsize=(10, 5), facecolor='#f8f9fa')
        ax = fig.add_subplot(111)

        pastel_colors = ['#FFB3BA', '#FFDFBA', '#FFFFBA', '#BAFFC9', '#BAE1FF',
                         '#E0BBE4', '#FFDFD3', '#C9E4DE', '#FEC8D8', '#D4F0F0']
        pastel_cmap = ListedColormap(pastel_colors)

        ax.scatter(fuel_loads, lap_times, s=150, c=lap_numbers, cmap=pastel_cmap,
                   edgecolors='black', linewidths=2, zorder=3)

        for lap_num, fuel, time in zip(lap_numbers, fuel_loads, lap_times):
            ax.annotate(f'{lap_num}', (fuel, time), fontsize=10, fontweight='bold', ha='center', va='center', color='black')

        if len(fuel_loads) > 1:
            z = np.polyfit(fuel_loads, lap_times, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(min(fuel_loads), max(fuel_loads), 100)
            ax.plot(x_trend, p(x_trend), '--', color='#ef4444', linewidth=2, alpha=0.7, label='Trend', zorder=2)

            correlation = np.corrcoef(fuel_loads, lap_times)[0, 1]
            ax.text(0.98, 0.98, f'Correlation: {correlation:.3f}', transform=ax.transAxes,
                    ha='right', va='top', fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax.set_xlabel('Average Fuel Load (L)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_ylabel('Lap Time (s)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_title('Lap Time vs Fuel Load Correlation', fontsize=13, fontweight='bold', color='#111827', pad=10)

        ax.set_facecolor('white')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.tick_params(colors='#111827', labelsize=10)

        for spine in ax.spines.values():
            spine.set_edgecolor('#d1d5db')
            spine.set_linewidth(1)

        if len(fuel_loads) > 1:
            ax.legend(loc='upper left', fontsize=9)

        fig.subplots_adjust(left=0.10, right=0.98, top=0.90, bottom=0.15)

        canvas = self._make_fuel_canvas(fig, int(450 * self.scale_factor))

        wrapper = QWidget()
        wrapper.setStyleSheet("QWidget { background-color: white; border: 2px solid #000000; border-radius: 8px; }")
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(3, 3, 3, 3)
        wrapper_layout.addWidget(canvas)
        return wrapper

    def create_fuel_track_map(self, lap):
        lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap].copy()
        if len(lap_data) == 0:
            return None

        lap_data = lap_data.sort_values("SessionTick").reset_index(drop=True)

        start_fuel = lap_data['FuelLevel'].iloc[0]
        end_fuel = lap_data['FuelLevel'].iloc[-1]
        total_fuel_used = start_fuel - end_fuel

        fuel_rate = []
        for i in range(len(lap_data) - 1):
            fuel_diff = lap_data['FuelLevel'].iloc[i] - lap_data['FuelLevel'].iloc[i + 1]
            time_diff = (lap_data['SessionTick'].iloc[i + 1] - lap_data['SessionTick'].iloc[i]) / 60
            fuel_rate.append(max(0, fuel_diff / time_diff) if time_diff > 0 else 0)
        fuel_rate.append(fuel_rate[-1] if fuel_rate else 0)

        fig = Figure(figsize=(8, 8), facecolor='#BFBEC1')
        ax = fig.add_subplot(111)

        points = np.array([lap_data["Lon"].values, lap_data["Lat"].values]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        max_rate = max(fuel_rate) if fuel_rate else 1
        min_rate = min(fuel_rate) if fuel_rate else 0

        colors = []
        for rate in fuel_rate[:-1]:
            ratio = (rate - min_rate) / (max_rate - min_rate) if max_rate > min_rate else 0
            colors.append(interpolate_color('#22c55e', '#ef4444', ratio))

        from matplotlib.collections import LineCollection
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

        ax.set_title(f'Lap {lap} - Fuel Consumption Rate', fontsize=14, fontweight='bold', pad=10)
        ax.set_aspect('equal')
        ax.set_facecolor('white')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(lap_data["Lon"].min() - 0.0005, lap_data["Lon"].max() + 0.0005)
        ax.set_ylim(lap_data["Lat"].min() - 0.0005, lap_data["Lat"].max() + 0.0005)

        fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.001)

        fuel_used_kg = total_fuel_used * FUEL_DENSITY
        ax.text(0.02, 0.98, f'Fuel Used: {total_fuel_used:.2f}L ({fuel_used_kg:.2f}kg)',
                transform=ax.transAxes, ha='left', va='top', fontsize=12, fontweight='bold', color='#111827')

        canvas = self._make_fuel_canvas(fig, int(800 * self.scale_factor))
        canvas.setFixedSize(int(800 * self.scale_factor), int(800 * self.scale_factor))
        return canvas
