import pandas as pd
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QSizePolicy, QFrame, QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from utils.resource_path import resource_path


class OverviewPageMixin:
    """Session Overview page: 
        -environmental conditions bar
        -session-type-specific summary (Qualifying / Practice / Race)
        -track map
    """

    def make_overview_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 2, 2, 5)
        layout.setSpacing(5)

        venue = self.session_info.get("Venue", "Unknown Venue")

        session_type = self.session_type if hasattr(self, "session_type") else "Practice"
        session_type_display = session_type.capitalize()
        title = QLabel(f"{session_type_display} Session Overview")
        title.setStyleSheet("""
            font-size: 38px;
            font-weight: bold;
            color: #000007;
        """)
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title)

        air_temp = self.telemetry_df["AirTemp"].dropna().iloc[0] if "AirTemp" in self.telemetry_df.columns else 0
        track_temp = self.telemetry_df["TrackTemp"].dropna().iloc[0] if "TrackTemp" in self.telemetry_df.columns else 0
        relative_humidity = self.telemetry_df["RelativeHumidity"].dropna().iloc[0] if "RelativeHumidity" in self.telemetry_df.columns else 0
        air_pressure = self.telemetry_df["AirPressure"].dropna().iloc[0] if "AirPressure" in self.telemetry_df.columns else 0
        air_density = self.telemetry_df["AirDensity"].dropna().iloc[0] if "AirDensity" in self.telemetry_df.columns else 0

        air_temp_str = f"{air_temp:.1f}°C"
        track_temp_str = f"{track_temp:.1f}°C"
        humidity_str = f"{relative_humidity:.0f}%"
        pressure_str = f"{air_pressure / 3386.39:.2f} Hg"
        density_str = f"{air_density:.3f} kg/m³"

        skies_value = int(self.telemetry_df["Skies"].dropna().iloc[0]) if "Skies" in self.telemetry_df.columns else 0
        weather_map = {
            0: ("Clear", "weather_clear"),
            1: ("Lightly Cloudy", "weather_L_Cloudy"),
            2: ("Moderately Cloudy", "weather_M_cloudy"),
            3: ("Overcast", "weather_overcast")
        }
        weather_text, weather_icon_name = weather_map.get(skies_value, ("Clear", "weather_clear"))

        env_bar = QWidget()
        env_bar.setFixedHeight(110)
        env_bar.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
        """)

        env_layout = QHBoxLayout(env_bar)
        env_layout.setContentsMargins(20, 10, 20, 10)
        env_layout.setSpacing(50)

        weather_widget = QWidget()
        weather_main_layout = QVBoxLayout(weather_widget)
        weather_main_layout.setSpacing(2)
        weather_main_layout.setContentsMargins(0, 0, 0, 0)

        weather_label = QLabel("Weather")
        weather_label.setStyleSheet("font-size: 16px; color: #6b7280; font-weight: 500;")

        weather_content = QWidget()
        weather_content_layout = QHBoxLayout(weather_content)
        weather_content_layout.setContentsMargins(0, 0, 0, 0)
        weather_content_layout.setSpacing(10)

        weather_icon = QLabel()
        weather_pixmap = QPixmap(resource_path(f"icons/{weather_icon_name}.png"))
        if not weather_pixmap.isNull():
            weather_icon.setPixmap(weather_pixmap.scaled(55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        weather_icon.setFixedSize(60, 60)
        weather_icon.setAlignment(Qt.AlignCenter)

        weather_value = QLabel(weather_text)
        weather_value.setStyleSheet("font-size: 24px; color: #111827; font-weight: bold;")

        weather_content_layout.addWidget(weather_icon)
        weather_content_layout.addWidget(weather_value)

        weather_main_layout.addWidget(weather_label)
        weather_main_layout.addWidget(weather_content)

        air_temp_widget = QWidget()
        air_temp_layout = QVBoxLayout(air_temp_widget)
        air_temp_layout.setSpacing(2)
        air_temp_layout.setContentsMargins(0, 0, 0, 0)

        air_temp_label = QLabel("Air Temperature")
        air_temp_label.setStyleSheet("font-size: 16px; color: #6b7280; font-weight: 500;")
        air_temp_value = QLabel(air_temp_str)
        air_temp_value.setStyleSheet("font-size: 24px; color: #111827; font-weight: bold;")

        air_temp_layout.addWidget(air_temp_label)
        air_temp_layout.addWidget(air_temp_value)

        track_temp_widget = QWidget()
        track_temp_layout = QVBoxLayout(track_temp_widget)
        track_temp_layout.setSpacing(2)
        track_temp_layout.setContentsMargins(0, 0, 0, 0)

        track_temp_label = QLabel("Track Temperature")
        track_temp_label.setStyleSheet("font-size: 16px; color: #6b7280; font-weight: 500;")
        track_temp_value = QLabel(track_temp_str)
        track_temp_value.setStyleSheet("font-size: 24px; color: #111827; font-weight: bold;")

        track_temp_layout.addWidget(track_temp_label)
        track_temp_layout.addWidget(track_temp_value)

        humidity_widget = QWidget()
        humidity_layout = QVBoxLayout(humidity_widget)
        humidity_layout.setSpacing(2)
        humidity_layout.setContentsMargins(0, 0, 0, 0)

        humidity_label = QLabel("Humidity")
        humidity_label.setStyleSheet("font-size: 16px; color: #6b7280; font-weight: 500;")
        humidity_value = QLabel(humidity_str)
        humidity_value.setStyleSheet("font-size: 24px; color: #111827; font-weight: bold;")

        humidity_layout.addWidget(humidity_label)
        humidity_layout.addWidget(humidity_value)

        pressure_widget = QWidget()
        pressure_layout = QVBoxLayout(pressure_widget)
        pressure_layout.setSpacing(2)
        pressure_layout.setContentsMargins(0, 0, 0, 0)

        pressure_label = QLabel("Air Pressure")
        pressure_label.setStyleSheet("font-size: 16px; color: #6b7280; font-weight: 500;")
        pressure_value = QLabel(pressure_str)
        pressure_value.setStyleSheet("font-size: 24px; color: #111827; font-weight: bold;")

        pressure_layout.addWidget(pressure_label)
        pressure_layout.addWidget(pressure_value)

        density_widget = QWidget()
        density_layout = QVBoxLayout(density_widget)
        density_layout.setSpacing(2)
        density_layout.setContentsMargins(0, 0, 0, 0)

        density_label = QLabel("Air Density")
        density_label.setStyleSheet("font-size: 16px; color: #6b7280; font-weight: 500;")
        density_value = QLabel(density_str)
        density_value.setStyleSheet("font-size: 24px; color: #111827; font-weight: bold;")

        density_layout.addWidget(density_label)
        density_layout.addWidget(density_value)

        env_layout.addWidget(weather_widget)
        env_layout.addWidget(air_temp_widget)
        env_layout.addWidget(track_temp_widget)
        env_layout.addWidget(humidity_widget)
        env_layout.addWidget(pressure_widget)
        env_layout.addWidget(density_widget)
        env_layout.addStretch()

        layout.addWidget(env_bar)
        layout.addSpacing(10)

        if session_type == "Qualifying":
            self._build_qualifying_overview(layout, venue)
        if session_type == "Practice":
            self._build_practice_overview(layout, venue)
        if session_type == "Race":
            self._build_race_overview(layout, venue)

        layout.addStretch()

        return page

    def _build_qualifying_overview(self, layout, venue):
        quali_content_layout = QHBoxLayout()
        quali_content_layout.setSpacing(int(24 * self.scale_factor))

        best_lap_card = QWidget()
        best_lap_card.setFixedWidth(int(691 * self.scale_factor))
        best_lap_card.setFixedHeight(int(276 * self.scale_factor))
        best_lap_card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 2px solid #000000;
            }
        """)

        best_lap_layout = QVBoxLayout(best_lap_card)
        best_lap_layout.setContentsMargins(int(24 * self.scale_factor), int(18 * self.scale_factor),
                                            int(24 * self.scale_factor), int(18 * self.scale_factor))
        best_lap_layout.setSpacing(int(12 * self.scale_factor))

        card_title = QLabel("🏆 Best Qualifying Lap")
        card_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #000000;")
        best_lap_layout.addWidget(card_title)

        best_lap_num = None
        if not hasattr(self, 'lap_timings') or len(self.lap_timings) == 0:
            self.calculate_lap_timings()

        valid_laps = {
            lap: data for lap, data in self.lap_timings.items()
            if data['is_valid']
            and not data.get('is_outlap', False)
            and not data.get('is_inlap', False)
        }
        if valid_laps:
            best_lap_num = min(valid_laps, key=lambda x: valid_laps[x]['time'])
            best_lap_data = valid_laps[best_lap_num]

            best_time_label = QLabel(f"Lap {best_lap_num}: {best_lap_data['time_str']}")
            best_time_label.setStyleSheet(f"font-size: {int(32 * self.scale_factor)}px; font-weight: bold; color: #111827;")
            best_lap_layout.addWidget(best_time_label)

            sector1_time = best_lap_data['sector1']
            sector2_time = best_lap_data['sector2']
            sector3_time = best_lap_data['sector3']

            s1_str = self._format_sector_time(sector1_time)
            s2_str = self._format_sector_time(sector2_time)
            s3_str = self._format_sector_time(sector3_time)

            sectors_label = QLabel(f"Sector 1: {s1_str}  |  Sector 2: {s2_str}  |  Sector 3: {s3_str}")
            sectors_label.setStyleSheet(f"font-size: {int(18 * self.scale_factor)}px; color: #374151;")
            best_lap_layout.addWidget(sectors_label)
        else:
            no_data_label = QLabel("No valid lap data available")
            no_data_label.setStyleSheet(f"font-size: {int(24 * self.scale_factor)}px; color: #6b7280;")
            best_lap_layout.addWidget(no_data_label)

        best_lap_layout.addStretch()

        quali_content_layout.addWidget(best_lap_card, alignment=Qt.AlignTop | Qt.AlignLeft)

        if best_lap_num is not None:
            track_map = self.make_track_map_widget(venue, self.scale_factor, lap_number=best_lap_num)
            track_map.setFixedSize(int(729 * self.scale_factor), int(671 * self.scale_factor))
            track_map.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            quali_content_layout.addWidget(track_map, alignment=Qt.AlignTop | Qt.AlignLeft)

        quali_content_layout.addStretch()
        layout.addLayout(quali_content_layout)

    @staticmethod
    def _format_sector_time(seconds):
        m = int(seconds // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{m:02}:{s:02}.{ms:03}"

    def _build_practice_overview(self, layout, venue):
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        df_valid = self.telemetry_df[
            (self.telemetry_df["Lap"] > 0) &
            (self.telemetry_df["LapLastLapTime"] > 0)
        ].copy()

        laps_completed = int(sorted(df_valid["Lap"].dropna().unique())[-1])
        fastest_lap_seconds = df_valid["LapLastLapTime"].min()
        fastest_lap_formatted = self._format_sector_time(fastest_lap_seconds)

        valid_non_pit_laps = {
            lap: data for lap, data in self.lap_timings.items()
            if data['is_valid']
            and not data.get('is_outlap', False)
            and not data.get('is_inlap', False)
        }
        if valid_non_pit_laps:
            fastest_lap_on = min(valid_non_pit_laps, key=lambda x: valid_non_pit_laps[x]['time'])
        else:
            fastest_lap_on = int(df_valid.loc[df_valid["LapLastLapTime"].idxmin()]["Lap"])

        overview_df = pd.DataFrame({
            "Metric": ["Laps Completed", "Fastest Lap", "Fastest Lap Set On"],
            "Value": [laps_completed, fastest_lap_formatted, fastest_lap_on]
        })

        table = QTableWidget(len(overview_df), len(overview_df.columns))
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setVisible(False)
        table.setFrameShape(QFrame.NoFrame)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)

        for row in range(len(overview_df)):
            for col in range(len(overview_df.columns)):
                item = QTableWidgetItem(str(overview_df.iat[row, col]))
                if col == 0:
                    item.setFlags(Qt.ItemIsEnabled)
                table.setItem(row, col, item)

        h_header = table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.Stretch)

        table.setFixedHeight(150)
        table.setFixedWidth(500)
        table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        table.setStyleSheet("""
            QTableWidget {
                background-color: #bfbec1;
                color: #111827;
                gridline-color: #27272b;
                font-size: 24px;
                border-top: 1px solid #27272b;
            }
            QTableWidget::item {
                background-color: white;
                padding: 10px;
            }
            QHeaderView::section {
                background-color: #bfbec1;
                color: black;
                font-weight: bold;
                font-size: 20px;
                border: none;
                padding: 6px;
            }
        """)

        track_map = self.make_track_map_widget(venue, self.scale_factor, lap_number=fastest_lap_on)
        track_map.setFixedSize(int(900 * self.scale_factor), int(750 * self.scale_factor))
        table.setContentsMargins(0, 0, 0, 0)
        table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        content_layout.addWidget(table, alignment=Qt.AlignTop | Qt.AlignLeft)
        content_layout.addWidget(track_map, alignment=Qt.AlignTop | Qt.AlignLeft)
        content_layout.addStretch()

        layout.addLayout(content_layout)

    def _build_race_overview(self, layout, venue):
        top_layout = QHBoxLayout()
        top_layout.setSpacing(int(24 * self.scale_factor))

        left_column = QVBoxLayout()
        left_column.setSpacing(int(24 * self.scale_factor))

        df_valid = self.telemetry_df[(self.telemetry_df["Lap"] > 0)].copy()

        lap_1_data = self.telemetry_df[self.telemetry_df["Lap"] == 1]
        starting_position = int(lap_1_data["PlayerCarClassPosition"].iloc[0]) if len(lap_1_data) > 0 else 0

        last_lap = df_valid["Lap"].max()
        last_lap_data = self.telemetry_df[self.telemetry_df["Lap"] == last_lap]
        finishing_position = int(last_lap_data["PlayerCarClassPosition"].iloc[-1]) if len(last_lap_data) > 0 else 0

        position_change = starting_position - finishing_position
        if position_change > 0:
            position_change_str = f"▲ {position_change}"
            position_color = "#22c55e"
        elif position_change < 0:
            position_change_str = f"▼ {abs(position_change)}"
            position_color = "#ef4444"
        else:
            position_change_str = "—"
            position_color = "#6b7280"

        total_laps = int(df_valid["Lap"].max())

        race_time_seconds = self.telemetry_df["SessionTime"].max()
        hours = int(race_time_seconds // 3600)
        minutes = int((race_time_seconds % 3600) // 60)
        seconds = int(race_time_seconds % 60)
        race_time_str = f"{hours:02}:{minutes:02}:{seconds:02}" if hours > 0 else f"{minutes:02}:{seconds:02}"

        race_df = pd.DataFrame({
            "Metric": ["Starting Position", "Finishing Position", "Position Change", "Race Length (Laps)", "Race Length (Time)"],
            "Value": [starting_position, finishing_position, position_change_str, total_laps, race_time_str]
        })

        summary_table = QTableWidget(len(race_df), len(race_df.columns))
        summary_table.horizontalHeader().setVisible(False)
        summary_table.verticalHeader().setVisible(False)
        summary_table.setFrameShape(QFrame.NoFrame)
        summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        summary_table.setSelectionMode(QTableWidget.NoSelection)

        for row in range(len(race_df)):
            for col in range(len(race_df.columns)):
                value = str(race_df.iat[row, col])
                item = QTableWidgetItem(value)

                if row == 2 and col == 1:
                    item.setForeground(QColor(position_color))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                if col == 0:
                    item.setFlags(Qt.ItemIsEnabled)

                summary_table.setItem(row, col, item)

        h_header = summary_table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.Stretch)

        actual_height = sum(summary_table.rowHeight(r) for r in range(summary_table.rowCount()))
        summary_table.setFixedHeight(actual_height + int(4 * self.scale_factor))
        summary_table.setFixedWidth(int(588 * self.scale_factor))
        summary_table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        summary_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        summary_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        summary_table.setFocusPolicy(Qt.NoFocus)

        summary_table.setStyleSheet("""
            QTableWidget {
                background-color: #bfbec1;
                color: #111827;
                gridline-color: #27272b;
                font-size: 24px;
                border: 2px solid #000000;
            }
            QTableWidget::item {
                background-color: white;
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: white;
                color: #111827;
            }
            QHeaderView::section {
                background-color: #bfbec1;
                color: black;
                font-weight: bold;
                font-size: 20px;
                border: none;
                padding: 6px;
            }
        """)

        left_column.addWidget(summary_table)

        lap_positions = []
        prev_position = None

        for lap in sorted(df_valid["Lap"].unique()):
            lap_start_data = self.telemetry_df[
                (self.telemetry_df["Lap"] == lap) &
                (self.telemetry_df["LapTimeline"] >= lap + 0.05) &
                (self.telemetry_df["LapTimeline"] <= lap + 0.15)
            ]

            if len(lap_start_data) > 0:
                position = int(lap_start_data["PlayerCarClassPosition"].iloc[0])

                if prev_position is not None:
                    change = prev_position - position
                    if change > 0:
                        change_str, change_color = f"▲ {change}", "#22c55e"
                    elif change < 0:
                        change_str, change_color = f"▼ {abs(change)}", "#ef4444"
                    else:
                        change_str, change_color = "—", "#6b7280"
                else:
                    change_str, change_color = "—", "#6b7280"

                lap_positions.append({'lap': int(lap), 'position': position, 'change_str': change_str, 'change_color': change_color})
                prev_position = position

        position_df = pd.DataFrame({
            "Lap": [p['lap'] for p in lap_positions],
            "Position": [p['position'] for p in lap_positions],
            "Change": [p['change_str'] for p in lap_positions]
        })

        position_table = QTableWidget(len(position_df), len(position_df.columns))
        position_table.setHorizontalHeaderLabels(["Lap", "Position", "Change"])
        position_table.verticalHeader().setVisible(False)
        position_table.setFrameShape(QFrame.NoFrame)
        position_table.setEditTriggers(QTableWidget.NoEditTriggers)
        position_table.setSelectionMode(QTableWidget.NoSelection)
        position_table.setFocusPolicy(Qt.NoFocus)

        for row in range(len(position_df)):
            for col in range(len(position_df.columns)):
                value = str(position_df.iat[row, col])
                item = QTableWidgetItem(value)

                if col == 2:
                    item.setForeground(QColor(lap_positions[row]['change_color']))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                item.setTextAlignment(Qt.AlignCenter)
                position_table.setItem(row, col, item)

        h_header = position_table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.Fixed)
        h_header.setSectionResizeMode(1, QHeaderView.Fixed)
        h_header.setSectionResizeMode(2, QHeaderView.Stretch)
        position_table.setColumnWidth(0, int(94 * self.scale_factor))
        position_table.setColumnWidth(1, int(118 * self.scale_factor))

        header_height = position_table.horizontalHeader().height()
        actual_height = header_height + sum(position_table.rowHeight(r) for r in range(position_table.rowCount()))

        position_table.setFixedWidth(int(588 * self.scale_factor))
        position_table.setFixedHeight(actual_height + int(32 * self.scale_factor))
        position_table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        position_table.setStyleSheet("""
            QTableWidget {
                background-color: #bfbec1;
                color: #111827;
                gridline-color: #27272b;
                font-size: 18px;
                border: 2px solid #000000;
            }
            QTableWidget::item {
                background-color: white;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: white;
                color: #111827;
            }
            QHeaderView::section {
                background-color: #6b7280;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border: none;
                padding: 8px;
            }
        """)

        left_column.addWidget(position_table)

        track_map_container = QWidget()
        track_map_layout = QVBoxLayout(track_map_container)
        track_map_layout.setContentsMargins(0, 0, 0, 0)
        track_map_layout.setSpacing(int(5 * self.scale_factor))

        track_title = QLabel(venue.upper())
        track_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000;")
        track_title.setAlignment(Qt.AlignCenter)
        track_map_layout.addWidget(track_title)

        self.race_track_map_widget = self.make_race_track_map_widget(venue, self.scale_factor)
        track_map_layout.addWidget(self.race_track_map_widget)

        track_map_container.setFixedSize(int(729 * self.scale_factor), int(671 * self.scale_factor))

        top_layout.addLayout(left_column)
        top_layout.addWidget(track_map_container)
        top_layout.addStretch()

        layout.addLayout(top_layout)

        fig_width = 12.94 * self.scale_factor
        fig_height = 3.53 * self.scale_factor
        fig = Figure(figsize=(fig_width, fig_height), facecolor='white')
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        laps = [p['lap'] for p in lap_positions]
        positions = [p['position'] for p in lap_positions]

        ax.plot(laps, positions, color='#3b82f6', linewidth=2, marker='o', markersize=6)
        ax.set_xlabel('Laps', fontsize=12, fontweight='bold')
        ax.set_ylabel('Position', fontsize=12, fontweight='bold')
        ax.set_title('Race Position by Lap', fontsize=14, fontweight='bold', pad=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.invert_yaxis()
        ax.set_xticks(laps)

        for spine in ax.spines.values():
            spine.set_color('black')
            spine.set_linewidth(2)

        fig.tight_layout()

        canvas.setFixedSize(int(1341 * self.scale_factor), int(353 * self.scale_factor))
        layout.addWidget(canvas)

    def make_race_track_map_widget(self, venue, scale_factor=1.0):
        fig = Figure(figsize=(6, 5.5), facecolor='white', dpi=100)
        canvas = FigureCanvas(fig)

        canvas.setMinimumSize(int(705 * scale_factor), int(588 * scale_factor))
        canvas.setMaximumSize(int(999 * scale_factor), int(882 * scale_factor))

        ax = fig.add_subplot(111)

        available_laps = sorted(self.telemetry_df["Lap"].unique())

        target_lap = None
        for lap in [3, 4, 2, 5]:
            if lap in available_laps:
                target_lap = lap
                break
        if target_lap is None and len(available_laps) > 0:
            target_lap = available_laps[0]

        lap_data = self.telemetry_df[self.telemetry_df["Lap"] == target_lap].sort_values("LapDistPct")

        if len(lap_data) > 0:
            lat = lap_data["Lat"].values
            lon = lap_data["Lon"].values

            ax.plot(lon, lat, color='black', linewidth=4, zorder=1)

            start_lat = lat[0]
            start_lon = lon[0]

            if len(lat) > 1:
                dx = lon[1] - lon[0]
                dy = lat[1] - lat[0]
                perp_dx = -dy
                perp_dy = dx
                length = (perp_dx**2 + perp_dy**2)**0.5
                if length > 0:
                    perp_dx /= length
                    perp_dy /= length
                    scale = 0.0002
                    perp_dx *= scale
                    perp_dy *= scale
                    ax.plot([start_lon - perp_dx, start_lon + perp_dx],
                            [start_lat - perp_dy, start_lat + perp_dy],
                            color='red', linewidth=3, zorder=4)

        if hasattr(self, 'race_overtakes'):
            for overtake in self.race_overtakes:
                if overtake['is_gain'] and self.show_overtakes:
                    ax.scatter(overtake['lon'], overtake['lat'], color='#22c55e', s=150, zorder=3)
                elif not overtake['is_gain'] and self.show_overtaken:
                    ax.scatter(overtake['lon'], overtake['lat'], color='#ef4444', s=150, zorder=3)

        ax.set_aspect('equal', adjustable='datalim')
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color('black')
            spine.set_linewidth(2)

        fig.tight_layout(pad=0.1)
        ax.autoscale()
        self.original_xlim = ax.get_xlim()
        self.original_ylim = ax.get_ylim()
        self.pan_start = None

        def on_scroll(event):
            if event.inaxes != ax:
                return
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()
            xdata = event.xdata
            ydata = event.ydata
            base_scale = 1.2
            if event.button == 'up':
                scale_factor = 1 / base_scale
            elif event.button == 'down':
                scale_factor = base_scale
            else:
                return
            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
            relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
            rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
            ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
            ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])
            canvas.draw_idle()

        def on_press(event):
            if event.inaxes != ax:
                return
            self.pan_start = (event.xdata, event.ydata)

        def on_release(event):
            self.pan_start = None

        def on_motion(event):
            if self.pan_start is None or event.inaxes != ax:
                return
            if event.xdata is None or event.ydata is None:
                return
            dx = self.pan_start[0] - event.xdata
            dy = self.pan_start[1] - event.ydata
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()
            ax.set_xlim([cur_xlim[0] + dx, cur_xlim[1] + dx])
            ax.set_ylim([cur_ylim[0] + dy, cur_ylim[1] + dy])
            canvas.draw_idle()

        canvas.mpl_connect('scroll_event', on_scroll)
        canvas.mpl_connect('button_press_event', on_press)
        canvas.mpl_connect('button_release_event', on_release)
        canvas.mpl_connect('motion_notify_event', on_motion)

        self.race_map_annotations = []

        def on_hover(event):
            if self.pan_start is not None:
                return
            if event.inaxes != ax or event.xdata is None or event.ydata is None:
                return
            for ann in self.race_map_annotations:
                ann.remove()
            self.race_map_annotations.clear()

            if hasattr(self, 'race_overtakes'):
                for overtake in self.race_overtakes:
                    if overtake['is_gain'] and not self.show_overtakes:
                        continue
                    if not overtake['is_gain'] and not self.show_overtaken:
                        continue
                    dx = event.xdata - overtake['lon']
                    dy = event.ydata - overtake['lat']
                    distance = (dx**2 + dy**2)**0.5
                    xlim = ax.get_xlim()
                    ylim = ax.get_ylim()
                    x_range = xlim[1] - xlim[0]
                    y_range = ylim[1] - ylim[0]
                    threshold = max(x_range, y_range) * 0.02
                    if distance < threshold:
                        tooltip_text = f"Lap {overtake['lap']}\n{overtake['old_pos']} → {overtake['new_pos']}"
                        ann = ax.annotate(tooltip_text, xy=(overtake['lon'], overtake['lat']),
                                           xytext=(10, 10), textcoords='offset points',
                                           bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.9),
                                           fontsize=10, fontweight='bold')
                        self.race_map_annotations.append(ann)
                        canvas.draw_idle()
                        break
            if len(self.race_map_annotations) == 0:
                canvas.draw_idle()

        canvas.mpl_connect('motion_notify_event', on_hover)

        return canvas

    def make_track_map_widget(self, venue, scale_factor, lap_number=None):
        """Simple, non-interactive track map for Practice/Qualifying."""
        fig = Figure(figsize=(6, 5.5), facecolor='#BFBEC1', dpi=100)
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet("background-color: #BFBEC1;")
        canvas.setMinimumSize(int(705 * scale_factor), int(588 * scale_factor))
        canvas.setMaximumSize(int(999 * scale_factor), int(882 * scale_factor))

        ax = fig.add_subplot(111)

        if lap_number is not None:
            target_lap = lap_number
        else:
            available_laps = sorted(self.telemetry_df["Lap"].unique())
            target_lap = None
            for lap in [3, 4, 2, 5]:
                if lap in available_laps:
                    target_lap = lap
                    break
            if target_lap is None and len(available_laps) > 0:
                target_lap = available_laps[0]

        lap_data = self.telemetry_df[self.telemetry_df["Lap"] == target_lap].sort_values("SessionTime")

        if len(lap_data) > 0:
            lat = lap_data["Lat"].values
            lon = lap_data["Lon"].values
            ax.plot(lon, lat, color='black', linewidth=4, zorder=1)

            start_lat = lat[0]
            start_lon = lon[0]

            if len(lat) > 1:
                dx = lon[1] - lon[0]
                dy = lat[1] - lat[0]
                perp_dx = -dy
                perp_dy = dx
                length = (perp_dx**2 + perp_dy**2)**0.5
                if length > 0:
                    perp_dx /= length
                    perp_dy /= length
                    scale = 0.0002
                    perp_dx *= scale
                    perp_dy *= scale
                    ax.plot([start_lon - perp_dx, start_lon + perp_dx],
                            [start_lat - perp_dy, start_lat + perp_dy],
                            color='red', linewidth=3, zorder=4)

        ax.set_title(venue.upper(), fontsize=18, fontweight='bold', color='#000000', pad=10)
        ax.set_aspect('equal', adjustable='datalim')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_facecolor('#f3f4f6')
        for spine in ax.spines.values():
            spine.set_color('black')
            spine.set_linewidth(2)

        fig.tight_layout(pad=0.3)
        return canvas

    def toggle_race_overtakes(self):
        self.show_overtakes = self.race_overtake_btn.isChecked()
        self.update_race_track_map()

    def toggle_race_overtaken(self):
        self.show_overtaken = self.race_overtaken_btn.isChecked()
        self.update_race_track_map()

    def update_race_track_map(self):
        if hasattr(self, 'race_track_map_widget'):
            parent_layout = self.race_track_map_widget.parent().layout()
            parent_layout.removeWidget(self.race_track_map_widget)
            self.race_track_map_widget.deleteLater()

            venue = self.session_info.get("Venue", "Unknown Venue")
            self.race_track_map_widget = self.make_race_track_map_widget(venue, self.scale_factor)
            parent_layout.addWidget(self.race_track_map_widget)

    def update_overview_lap_list(self):
        if not hasattr(self, 'overview_lap_list'):
            return

        self.overview_lap_list.clear()

        if not hasattr(self, 'lap_timings') or len(self.lap_timings) == 0:
            self.calculate_lap_timings()

        lap_times_list = [(lap, data['time']) for lap, data in self.lap_timings.items()]

        order = self.overview_lap_order.currentText()

        if order == "Fastest to Slowest":
            sorted_laps = sorted(lap_times_list, key=lambda x: x[1])
        elif order == "Slowest to Fastest":
            sorted_laps = sorted(lap_times_list, key=lambda x: x[1], reverse=True)
        else:
            sorted_laps = sorted(lap_times_list, key=lambda x: x[0])

        display_lap_counter = 1
        for lap_num, lap_time in sorted_laps:
            time_str = self._format_sector_time(lap_time)
            self.overview_lap_list.addItem(f"Lap {display_lap_counter}: {time_str}")
            display_lap_counter += 1

    def on_overview_lap_selected(self, item):
        lap_text = item.text()
        lap_num = int(lap_text.split(":")[0].replace("Lap ", ""))
