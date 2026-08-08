from PySide6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QSizePolicy
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import Normalize
from matplotlib import cm
import numpy as np

G_CONVERSION = 9.81  # m/s^2 per g - iRacing's Lateral Accel and Longitudinal Accell are in m/s^2


class GForcePageMixin:
    """G-Force Data page:
            -G-G / Friction Diagram
            -Steering Angle / Lateral G-force Line Chart
            -Lap selector
        """

    def make_gforce_page(self):
        page = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("G-Force Analysis")
        title.setStyleSheet("font-size: 38px; font-weight: bold; color: #000007;")
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        main_content = QHBoxLayout()
        main_content.setSpacing(int(15 * self.scale_factor))

        lap_selector_container = QWidget()
        lap_selector_container.setFixedWidth(int(280 * self.scale_factor))
        lap_selector_container.setStyleSheet("""
            QWidget { background-color: white; border-radius: 0px; border: none; }
        """)
        lap_selector_layout = QVBoxLayout(lap_selector_container)
        lap_selector_layout.setContentsMargins(0, 0, 0, 0)
        lap_selector_layout.setSpacing(0)

        lap_selector_title = QLabel("Select Lap")
        lap_selector_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000; padding: 8px 8px 4px 8px;")
        lap_selector_layout.addWidget(lap_selector_title)

        self.gforce_lap_list = QListWidget()
        self.gforce_lap_list.setStyleSheet("""
            QListWidget { background-color: white; border: 1px solid #e5e7eb; border-radius: 4px; font-size: 18px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #f3f4f6; color: #000000; }
            QListWidget::item:selected { background-color: #2563eb; color: white; }
            QListWidget::item:hover { background-color: #eff6ff; color: #000000; }
        """)
        self.gforce_lap_list.itemClicked.connect(self.update_gforce_data_display)
        lap_selector_layout.addWidget(self.gforce_lap_list)

        for lap in sorted(self.lap_timings.keys()):
            lap_info = self.lap_timings[lap]
            item = QListWidgetItem(f"Lap {lap} - {lap_info['time_str']}")
            item.setData(Qt.UserRole, lap)
            self.gforce_lap_list.addItem(item)

        lap_selector_wrapper = QWidget()
        lap_selector_wrapper.setFixedWidth(int(284 * self.scale_factor))
        lap_selector_wrapper.setStyleSheet("""
            QWidget { background-color: white; border: 2px solid #000000; border-radius: 8px; }
        """)
        lap_selector_wrapper_layout = QVBoxLayout(lap_selector_wrapper)
        lap_selector_wrapper_layout.setContentsMargins(2, 2, 2, 2)
        lap_selector_wrapper_layout.setAlignment(Qt.AlignTop)
        lap_selector_wrapper_layout.addWidget(lap_selector_container)

        main_content.addWidget(lap_selector_wrapper)

        self.gforce_combined_wrapper = QWidget()
        self.gforce_combined_wrapper.setStyleSheet("""
            QWidget { background-color: #bfbec1; border: 2px solid #000000; border-radius: 8px; }
        """)
        self.gforce_combined_layout = QVBoxLayout(self.gforce_combined_wrapper)
        self.gforce_combined_layout.setContentsMargins(12, 12, 12, 12)
        self.gforce_combined_layout.setSpacing(10)
        self.gforce_combined_layout.setAlignment(Qt.AlignTop)

        main_content.addWidget(self.gforce_combined_wrapper)

        layout.addLayout(main_content)
        layout.addStretch()

        scroll.setWidget(content_widget)

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        if self.gforce_lap_list.count() > 0:
            self.gforce_lap_list.setCurrentRow(0)
            self.update_gforce_data_display()

        return page

    def update_gforce_data_display(self):
        current_item = self.gforce_lap_list.currentItem()
        if not current_item:
            return
        selected_lap = current_item.data(Qt.UserRole)

        while self.gforce_combined_layout.count():
            child = self.gforce_combined_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        combined_canvas = self.create_combined_gforce_chart(selected_lap)
        if combined_canvas:
            self.gforce_combined_layout.addWidget(combined_canvas)
        else:
            missing_label = QLabel("LatAccel / LongAccel / SteeringWheelAngle columns not found in this session's data")
            missing_label.setStyleSheet("font-size: 14px; color: #6b7280;")
            self.gforce_combined_layout.addWidget(missing_label, alignment=Qt.AlignHCenter)

    def _draw_gg_plot(self, fig, gg_cell, lap_data, lap):
        sub_gs = gg_cell.subgridspec(1, 3, width_ratios=[1, 20, 1], wspace=0.15)
        ax = fig.add_subplot(sub_gs[1])
        cax = fig.add_subplot(sub_gs[2])

        lat_g = lap_data["LatAccel"].values / G_CONVERSION
        long_g = lap_data["LongAccel"].values / G_CONVERSION

        
        progress = np.linspace(0, 1, len(lat_g))

        
        data_max = max(np.abs(lat_g).max(), np.abs(long_g).max())
        if data_max <= 0:
            data_max = 0.1
        max_range = data_max * 1.15

        
        circle_step = max_range / 3
        #TODO Doublwe check sizing consistency across aspect ratios + check centering bug is fixed
        for i in (1, 2, 3):
            radius = circle_step * i
            theta = np.linspace(0, 2 * np.pi, 200)
            ax.plot(radius * np.cos(theta), radius * np.sin(theta),
                    linestyle='--', linewidth=1, color='#9ca3af', alpha=0.3, zorder=1)
            ax.annotate(f"{radius:.2f}g", (radius * 0.72, radius * 0.72),
                        fontsize=8, color='#6b7280')

        norm = Normalize(vmin=0, vmax=1)
        ax.scatter(lat_g, long_g, c=progress, cmap='viridis', s=14, zorder=4, alpha=0.5)

        ax.axhline(0, color='#374151', linewidth=1, zorder=2)
        ax.axvline(0, color='#374151', linewidth=1, zorder=2)

        ax.set_xlim(-max_range, max_range)
        ax.set_ylim(-max_range, max_range)
        ax.set_aspect('equal')

        ax.set_xlabel("Lateral G", fontsize=11, fontweight='bold', color='#111827')
        ax.set_ylabel("Longitudinal G", fontsize=11, fontweight='bold', color='#111827')
        ax.set_title(f"Lap {lap} - G-G Diagram", fontsize=14, fontweight='bold', pad=10)
        ax.set_facecolor('white')
        ax.grid(True, alpha=0.2, linestyle='--')

        sm = cm.ScalarMappable(norm=norm, cmap=cm.get_cmap('viridis'))
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cax)
        cbar.set_label("Lap progress", fontsize=9)
        cbar.set_ticks([0, 1])
        cbar.set_ticklabels(["Start", "Finish"])

    def _get_lap_x_axis(self, lap_data):
        if "LapDist" in lap_data.columns:
            return lap_data["LapDist"].values, "Lap Distance (m)"
        lap_start_tick = lap_data["SessionTick"].iloc[0]
        return ((lap_data["SessionTick"] - lap_start_tick) / 60).values, "Time (seconds)"

    def _draw_steering_and_lateral_g(self, ax1, lap_data, lap, has_steering, has_lat_g):
        x_values, x_label = self._get_lap_x_axis(lap_data)
        ax1.set_facecolor('white')

        lines, labels = [], []
        ax2 = None

        if has_steering:
            angle_deg = np.degrees(lap_data["SteeringWheelAngle"].values)
            line, = ax1.plot(x_values, angle_deg, linewidth=1.4, color='#1d4ed8')
            lines.append(line)
            labels.append('Steering Angle (°)')

            max_abs_angle = max(abs(angle_deg.min()), abs(angle_deg.max()), 10)
            ax1.set_ylim(-max_abs_angle * 1.1, max_abs_angle * 1.1)
            ax1.set_ylabel('Steering Angle (°)', fontsize=11, fontweight='bold', color='#1d4ed8')
            ax1.tick_params(axis='y', labelcolor='#1d4ed8')

        if has_lat_g:
            lat_g = lap_data["LatAccel"].values / G_CONVERSION
            target_ax = ax1
            if has_steering:
                ax2 = ax1.twinx()
                ax2.set_facecolor('none') 
                target_ax = ax2

            line, = target_ax.plot(x_values, lat_g, linewidth=1.4, color='#ea580c')
            lines.append(line)
            labels.append('Lateral G')

            max_abs_g = max(abs(lat_g.min()), abs(lat_g.max()), 0.1)
            target_ax.set_ylim(-max_abs_g * 1.1, max_abs_g * 1.1)
            target_ax.set_ylabel('Lateral G', fontsize=11, fontweight='bold', color='#ea580c')
            target_ax.tick_params(axis='y', labelcolor='#ea580c')

        ax1.axhline(0, color='#374151', linewidth=1.2, zorder=1)
        ax1.set_xlim(x_values.min(), x_values.max())

        ax1.set_xlabel(x_label, fontsize=11, fontweight='bold', color='#111827')
        ax1.set_title(f'Lap {lap} - Steering & Lateral G', fontsize=13, fontweight='bold', color='#111827', pad=10)

        ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax1.tick_params(axis='x', labelsize=10, colors='#111827')

        for spine in ax1.spines.values():
            spine.set_edgecolor('#d1d5db')
            spine.set_linewidth(1)
        if ax2 is not None:
            for spine in ax2.spines.values():
                spine.set_edgecolor('#d1d5db')
                spine.set_linewidth(1)

        if lines:
            ax1.legend(lines, labels, loc='upper right', fontsize=9, framealpha=0.9)

    def create_combined_gforce_chart(self, lap):
        lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap].copy()
        if len(lap_data) == 0:
            return None

        has_gg = "LatAccel" in lap_data.columns and "LongAccel" in lap_data.columns
        has_steering = "SteeringWheelAngle" in lap_data.columns
        has_lat_g = "LatAccel" in lap_data.columns
        has_line_chart = has_steering or has_lat_g

        if not has_gg and not has_line_chart:
            return None

        lap_data = lap_data.sort_values("SessionTick").reset_index(drop=True)

        n_rows = int(has_gg) + int(has_line_chart)

        if has_gg and has_line_chart:
            fig_height = 13.0
            height_ratios = [2.6, 1]
        elif has_gg:
            fig_height = 11.5
            height_ratios = [1]
        else:
            fig_height = 4.6
            height_ratios = [1]

        fig = Figure(figsize=(11.5, fig_height), facecolor='#bfbec1')
        gs = fig.add_gridspec(n_rows, 1, height_ratios=height_ratios, hspace=0.25)

        row = 0
        if has_gg:
            self._draw_gg_plot(fig, gs[row], lap_data, lap)
            row += 1

        if has_line_chart:
            ax_line = fig.add_subplot(gs[row])
            self._draw_steering_and_lateral_g(ax_line, lap_data, lap, has_steering, has_lat_g)

        fig.subplots_adjust(left=0.18, right=0.88, top=0.95, bottom=0.06)

        canvas_width = int(1050 * self.scale_factor)
        canvas_height = int(canvas_width * (fig_height / 11.5))

        canvas = FigureCanvas(fig)
    
        canvas.setMinimumWidth(canvas_width)
        canvas.setFixedHeight(canvas_height)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return canvas