import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QButtonGroup,
    QMessageBox,
    QStackedWidget,
    QToolTip,
    QFrame,
    QAbstractScrollArea,
    QLayout,
    QScrollArea,
    QComboBox,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt
from PySide6.QtCore import QSize
from PySide6.QtCore import QTimer
from PySide6.QtCore import QPoint

from PySide6.QtGui import QIcon
from PySide6.QtGui import QPixmap
from PySide6.QtGui import QIcon
from PySide6.QtGui import QFont
from PySide6.QtGui import QColor
from PySide6.QtGui import QPalette
from PySide6.QtGui import QCursor


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np

from scipy.ndimage import median_filter

from csv_cleaner import clean_csv



class ZoomableCanvas(FigureCanvas):
    def __init__(self, fig):
        super().__init__(fig)
        self._pressing = False
        self._last_x = None
        self._last_y = None

    def wheelEvent(self, event):
        ax = self.figure.axes[0]
        
        # Get current axis limits
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Get mouse position in data coordinates
        x_data = (xlim[0] + xlim[1]) / 2
        y_data = (ylim[0] + ylim[1]) / 2
        
        # Zoom factor
        zoom_factor = 0.85  # Adjust for faster/slower zoom
        
        if event.angleDelta().y() > 0:
            # Scroll up = zoom in
            scale = zoom_factor
        else:
            # Scroll down = zoom out
            scale = 1 / zoom_factor
        
        # Calculate new limits centered on mouse position
        new_xlim = [
            x_data + (xlim[0] - x_data) * scale,
            x_data + (xlim[1] - x_data) * scale
        ]
        new_ylim = [
            y_data + (ylim[0] - y_data) * scale,
            y_data + (ylim[1] - y_data) * scale
        ]
        
        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)
        self.draw()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressing = True
            self._last_x = event.position().x()
            self._last_y = event.position().y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressing = False
            self._last_x = None
            self._last_y = None

    def mouseMoveEvent(self, event):
        if self._pressing and self._last_x is not None:
            ax = self.figure.axes[0]
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()

            # Calculate how much to pan based on mouse movement
            dx = event.position().x() - self._last_x
            dy = event.position().y() - self._last_y

            # Convert pixel movement to data coordinates
            x_scale = (xlim[1] - xlim[0]) / self.width()
            y_scale = (ylim[1] - ylim[0]) / self.height()

            ax.set_xlim(xlim[0] - dx * x_scale, xlim[1] - dx * x_scale)
            ax.set_ylim(ylim[0] + dy * y_scale, ylim[1] + dy * y_scale)

            self._last_x = event.position().x()
            self._last_y = event.position().y()

            self.draw()

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# ----------------------
# Full-screen window after CSV load
# ----------------------
class TelemetryWindow(QWidget):
    def __init__(self, session_info, telemetry_df, session_type):
        super().__init__()

        self.scale_factor = 1.0

        self.session_info = session_info
        self.telemetry_df = telemetry_df
        self.session_type = session_type
        self.setWindowIcon(QIcon("icons/c2k.png"))

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

        # -=Main Layout=-
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(1, 0, 0, 0)
        self.setLayout(main_layout)

        # -=Header Ribbon=-
        header = QWidget()
        header.setFixedHeight(100)
        header.setStyleSheet("background-color: #c7c9c8;")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(1, 0, 1, 0)
        header.setLayout(header_layout)
        header_layout.setSpacing(8)

        logo_label = QLabel()
        logo_pixmap = QPixmap("icons/c2k.png")
        logo_pixmap = logo_pixmap.scaled(
            125, 125,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        logo_label.setFixedSize(logo_pixmap.size())
        logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        header_layout.addWidget(logo_label)

        driver = session_info.get("Driver", "Unknown Driver")
        vehicle = session_info.get("Vehicle", "Unknown Vehicle")
        venue = session_info.get("Venue", "Unknown Venue")

        header_label = QLabel(f"{driver} | {vehicle} | {venue}")
        header_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        header_label.setStyleSheet("""
            color: black;
            font-size: 42px;
            font-weight: bold;
        """)
        header_layout.addWidget(header_label, alignment=Qt.AlignLeft)

        main_layout.addWidget(header)


        # -=Body=-
        body = QWidget()
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body.setLayout(body_layout)
        main_layout.addWidget(body)

        # -=LEFT PANEL (SIDEBAR)=-
        left_panel = QWidget()
        left_panel.setFixedWidth(int(280 * self.scale_factor))
        left_panel.setStyleSheet("background-color: #e7bdc0;")

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 20, 0, 20)
        left_layout.setSpacing(5)

        # -=STACKED VIEW=-
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #bfbec1;")

        # -=PAGES=-
        self.page_overview = self.make_overview_page()
        self.page_timings = self.make_timings_page()
        self.page_pedals = self.make_pedals_page()
        self.page_brakes = self.make_braking_page() 
        self.page_tyres = self.make_tyres_page()
        self.page_fuel = self.make_fuel_page()
        self.page_data = self.make_page("Data Viewer")

        self.stack.addWidget(self.page_overview)  # 0
        self.stack.addWidget(self.page_timings)   # 1
        self.stack.addWidget(self.page_pedals)    # 2
        self.stack.addWidget(self.page_brakes)    # 3 
        self.stack.addWidget(self.page_tyres)     # 4
        self.stack.addWidget(self.page_fuel)      # 5
        self.stack.addWidget(self.page_data)      # 6

        # -=NAVIGATION ITEMS WITH SHELF STRUCTURE=-
        nav_items = [
            ("Session Overview", "icons/icon_Overview.png", 0),
            ("Timing Data", "icons/icon_Timings.png", 1),
            ("Pedal Usage Data", "icons/icon_Pedals.png", 2),
            ("Lock-up Data", "icons/icon_Brakes.png", 3), 
            ("Tyre Data", "icons/icon_Tyre.png", 4),
            ("Fuel Usage Data", "icons/icon_Fuel.png", 5),
            ("Data Previewer", "icons/icon_Data.png", 6),
        ]
 
        for label, icon_path, page_index in nav_items:
            # Container for icon + text (shelf structure)
            item_container = QWidget()
            item_container.setFixedHeight(60)
            item_layout = QHBoxLayout(item_container)
            item_layout.setContentsMargins(15, 10, 15, 10)
            item_layout.setSpacing(8)
            item_layout.setAlignment(Qt.AlignVCenter)
            
            # Icon button
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(50, 50))
            btn.setFixedSize(50, 50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #374151;
                }
                QPushButton:pressed {
                    background-color: #4b5563;
                }
            """)
            btn.clicked.connect(lambda checked, idx=page_index: self.stack.setCurrentIndex(idx))
            
            # Label text
            text_label = QLabel(label)
            text_label.setStyleSheet("""
                QLabel {
                    color: #000000;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            
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

    def showEvent(self, event):
        """Called when window is first shown - NOW we can detect the correct screen"""
        super().showEvent(event)
            
        # Only set scale factor once
        if not hasattr(self, '_scale_factor_set'):
            screen = self.screen()
            if screen is None:
                screen = QApplication.primaryScreen()
                
            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
                
            if screen_width <= 1920:
                self.scale_factor = 0.7  
            elif screen_width <= 2560:
                self.scale_factor = 0.85  
            else:
                self.scale_factor = 1.0
                
            print(f"Screen detected: {screen_width}px, Scale factor: {self.scale_factor}")
            self._scale_factor_set = True
                
            # Trigger rebuild of pages with correct scale factor
            self.rebuild_pages()
        
    def rebuild_pages(self):
        """Rebuild pages with correct scale factor"""
        self.stack.removeWidget(self.page_overview)
        self.stack.removeWidget(self.page_timings)
        self.stack.removeWidget(self.page_pedals)
        self.stack.removeWidget(self.page_brakes)
        self.stack.removeWidget(self.page_tyres)
        self.stack.removeWidget(self.page_fuel)
        self.stack.removeWidget(self.page_data)
            
        self.page_overview = self.make_overview_page()
        self.page_timings = self.make_timings_page()
        self.page_pedals = self.make_pedals_page()
        self.page_brakes = self.make_braking_page()
        self.page_tyres = self.make_tyres_page()
        self.page_fuel = self.make_fuel_page()
        self.page_data = self.make_page("Data Viewer")
            
        self.stack.addWidget(self.page_overview)
        self.stack.addWidget(self.page_timings)
        self.stack.addWidget(self.page_pedals)
        self.stack.addWidget(self.page_brakes)
        self.stack.addWidget(self.page_tyres)
        self.stack.addWidget(self.page_fuel)
        self.stack.addWidget(self.page_data)

        # Load CSV head
        self.load_table_preview()

    # ===============================
    # CSV Preview Loader
    # ===============================
    def load_table_preview(self):
        self.preview_rows = 75 
        df = self.telemetry_df.iloc[:self.preview_rows]

        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns.tolist())

        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iat[row, col]
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)

        
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        
        self.table.setAlternatingRowColors(True)
        self.table.resizeColumnsToContents()

    def make_race_track_map_widget(self, venue):
        """Create track map with overtake markers for race overview"""
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        
        fig = Figure(figsize=(6, 5), facecolor='white')
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Get track outline by sampling points evenly across lap distance percentage
        # This ensures we get the full track shape
        df_sorted = self.telemetry_df.sort_values("LapDistPct")
        
        # Get one point per percentage increment (0-100%)
        track_points = []
        for pct in range(101):
            closest = df_sorted.iloc[(df_sorted["LapDistPct"] - pct).abs().argsort()[:1]]
            if len(closest) > 0:
                track_points.append({
                    'lat': closest["Lat"].iloc[0],
                    'lon': closest["Lon"].iloc[0]
                })
        
        if len(track_points) > 0:
            lats = [p['lat'] for p in track_points]
            lons = [p['lon'] for p in track_points]
            ax.plot(lons, lats, color='black', linewidth=2, zorder=1)
        
        # Debug: print track coordinates to verify
        print(f"Track points: {len(track_points)}")
        if len(track_points) > 0:
            print(f"Lat range: {min(lats)} to {max(lats)}")
            print(f"Lon range: {min(lons)} to {max(lons)}")
        
        # Plot overtake markers
        if hasattr(self, 'race_overtakes'):
            print(f"Total overtakes: {len(self.race_overtakes)}")
            for overtake in self.race_overtakes:
                if overtake['is_gain'] and self.show_overtakes:
                    # Green dot for overtake
                    ax.scatter(overtake['lon'], overtake['lat'], 
                            color='#22c55e', s=150, zorder=3, 
                            edgecolors='white', linewidths=2)
                elif not overtake['is_gain'] and self.show_overtaken:
                    # Red dot for being overtaken
                    ax.scatter(overtake['lon'], overtake['lat'], 
                            color='#ef4444', s=150, zorder=3,
                            edgecolors='white', linewidths=2)
        
        # Styling
        ax.set_title(f"{venue}", fontsize=14, fontweight='bold', pad=10)
        ax.set_aspect('equal')
        ax.axis('off')
        fig.tight_layout()
        
        # Add hover tooltips
        self.race_map_annotations = []
        
        def on_hover(event):
            if event.inaxes != ax or event.xdata is None or event.ydata is None:
                return
            
            # Clear previous annotations
            for ann in self.race_map_annotations:
                ann.remove()
            self.race_map_annotations.clear()
            
            # Check if hovering over an overtake point
            if hasattr(self, 'race_overtakes'):
                for overtake in self.race_overtakes:
                    # Check if we should show this overtake
                    if overtake['is_gain'] and not self.show_overtakes:
                        continue
                    if not overtake['is_gain'] and not self.show_overtaken:
                        continue
                        
                    # Calculate distance to mouse (in data coordinates)
                    dx = event.xdata - overtake['lon']
                    dy = event.ydata - overtake['lat']
                    distance = (dx**2 + dy**2)**0.5
                    
                    # Get axis limits to calculate relative threshold
                    xlim = ax.get_xlim()
                    ylim = ax.get_ylim()
                    x_range = xlim[1] - xlim[0]
                    y_range = ylim[1] - ylim[0]
                    threshold = max(x_range, y_range) * 0.02  # 2% of axis range
                    
                    # If close enough, show tooltip
                    if distance < threshold:
                        tooltip_text = f"Lap {overtake['lap']}\n{overtake['old_pos']} → {overtake['new_pos']}"
                        ann = ax.annotate(tooltip_text,
                                        xy=(overtake['lon'], overtake['lat']),
                                        xytext=(10, 10), textcoords='offset points',
                                        bbox=dict(boxstyle='round,pad=0.5', 
                                                fc='yellow', alpha=0.9),
                                        fontsize=10, fontweight='bold')
                        self.race_map_annotations.append(ann)
                        canvas.draw_idle()
                        break
            
            # If no annotation added, redraw to clear
            if len(self.race_map_annotations) == 0:
                canvas.draw_idle()
        
        canvas.mpl_connect('motion_notify_event', on_hover)
        
        return canvas
    


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # -----------------------
    # Overview Page
    # -----------------------
    def make_overview_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 2, 2, 5)
        layout.setSpacing(5)

        # Get venue from session_info
        venue = self.session_info.get("Venue", "Unknown Venue")

        # -=Title=-
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

        # Get Environmental Data from csv
        air_temp = self.telemetry_df["AirTemp"].dropna().iloc[0] if "AirTemp" in self.telemetry_df.columns else 0
        track_temp = self.telemetry_df["TrackTemp"].dropna().iloc[0] if "TrackTemp" in self.telemetry_df.columns else 0
        relative_humidity = self.telemetry_df["RelativeHumidity"].dropna().iloc[0] if "RelativeHumidity" in self.telemetry_df.columns else 0
        air_pressure = self.telemetry_df["AirPressure"].dropna().iloc[0] if "AirPressure" in self.telemetry_df.columns else 0
        air_density = self.telemetry_df["AirDensity"].dropna().iloc[0] if "AirDensity" in self.telemetry_df.columns else 0

        # Format metrics
        air_temp_str = f"{air_temp:.1f}°C"
        track_temp_str = f"{track_temp:.1f}°C"
        humidity_str = f"{relative_humidity:.0f}%"
        pressure_str = f"{air_pressure / 3386.39:.2f} Hg"
        density_str = f"{air_density:.3f} kg/m³"

        # Get weather condition
        skies_value = int(self.telemetry_df["Skies"].dropna().iloc[0]) if "Skies" in self.telemetry_df.columns else 0
        weather_map = {
            0: ("Clear", "weather_clear"),
            1: ("Lightly Cloudy", "weather_L_Cloudy"),
            2: ("Moderately Cloudy", "weather_M_cloudy"),
            3: ("Overcast", "weather_overcast")
        }
        weather_text, weather_icon_name = weather_map.get(skies_value, ("Clear", "weather_clear"))

        #-=Environmental Conditions Bar=-
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

        # Weather Section 
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
        weather_pixmap = QPixmap(f"icons/{weather_icon_name}.png")
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

        # Air Temperature Section
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

        # Track Temperature Section
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

        # Humidity Section
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

        # Air Pressure Section
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

        # Air Density Section
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

        # Add sections to environmental bar
        env_layout.addWidget(weather_widget)
        env_layout.addWidget(air_temp_widget)
        env_layout.addWidget(track_temp_widget)
        env_layout.addWidget(humidity_widget)
        env_layout.addWidget(pressure_widget)
        env_layout.addWidget(density_widget)
        env_layout.addStretch()

        layout.addWidget(env_bar)
        layout.addSpacing(10)

        # -=QUALIFYING SPECIFIC: Best Lap Card + Track Map=-
        if session_type == "Qualifying":
            quali_content_layout = QHBoxLayout()
            quali_content_layout.setSpacing(20)
            
            best_lap_card = QWidget()
            best_lap_card.setFixedWidth(500)
            best_lap_card.setFixedHeight(200)
            best_lap_card.setStyleSheet("""
                QWidget {
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    border: 2px solid #000000;
                }
            """)
            
            best_lap_layout = QVBoxLayout(best_lap_card)
            best_lap_layout.setContentsMargins(20, 15, 20, 15)
            best_lap_layout.setSpacing(10)
            
            card_title = QLabel("🏆 Best Qualifying Lap")
            card_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #000000;")
            best_lap_layout.addWidget(card_title)
            
            if hasattr(self, 'lap_timings') and len(self.lap_timings) > 0:
                valid_laps = {lap: data for lap, data in self.lap_timings.items() if data['is_valid']}
                if valid_laps:
                    best_lap_num = min(valid_laps, key=lambda x: valid_laps[x]['time'])
                    best_lap_data = valid_laps[best_lap_num]
                    
                    # Best lap time
                    best_time_label = QLabel(f"Lap {best_lap_num}: {best_lap_data['time_str']}")
                    best_time_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #111827;")
                    best_lap_layout.addWidget(best_time_label)
                    
                    # Sector times
                    sector1_time = best_lap_data['sector1']
                    sector2_time = best_lap_data['sector2']
                    sector3_time = best_lap_data['sector3']
                    
                    s1_min = int(sector1_time // 60)
                    s1_sec = int(sector1_time % 60)
                    s1_ms = int((sector1_time - int(sector1_time)) * 1000)
                    s1_str = f"{s1_min:02}:{s1_sec:02}.{s1_ms:03}"
                    
                    s2_min = int(sector2_time // 60)
                    s2_sec = int(sector2_time % 60)
                    s2_ms = int((sector2_time - int(sector2_time)) * 1000)
                    s2_str = f"{s2_min:02}:{s2_sec:02}.{s2_ms:03}"
                    
                    s3_min = int(sector3_time // 60)
                    s3_sec = int(sector3_time % 60)
                    s3_ms = int((sector3_time - int(sector3_time)) * 1000)
                    s3_str = f"{s3_min:02}:{s3_sec:02}.{s3_ms:03}"
                    
                    sectors_label = QLabel(f"Sector 1: {s1_str}  |  Sector 2: {s2_str}  |  Sector 3: {s3_str}")
                    sectors_label.setStyleSheet("font-size: 14px; color: #374151;")
                    best_lap_layout.addWidget(sectors_label)
            else:
                self.calculate_lap_timings()
                valid_laps = {lap: data for lap, data in self.lap_timings.items() if data['is_valid']}
                if valid_laps:
                    best_lap_num = min(valid_laps, key=lambda x: valid_laps[x]['time'])
                    best_lap_data = valid_laps[best_lap_num]
                    
                    best_time_label = QLabel(f"Lap {best_lap_num}: {best_lap_data['time_str']}")
                    best_time_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #111827;")
                    best_lap_layout.addWidget(best_time_label)
                    
                    sector1_time = best_lap_data['sector1']
                    sector2_time = best_lap_data['sector2']
                    sector3_time = best_lap_data['sector3']
                    
                    s1_min = int(sector1_time // 60)
                    s1_sec = int(sector1_time % 60)
                    s1_ms = int((sector1_time - int(sector1_time)) * 1000)
                    s1_str = f"{s1_min:02}:{s1_sec:02}.{s1_ms:03}"
                    
                    s2_min = int(sector2_time // 60)
                    s2_sec = int(sector2_time % 60)
                    s2_ms = int((sector2_time - int(sector2_time)) * 1000)
                    s2_str = f"{s2_min:02}:{s2_sec:02}.{s2_ms:03}"
                    
                    s3_min = int(sector3_time // 60)
                    s3_sec = int(sector3_time % 60)
                    s3_ms = int((sector3_time - int(sector3_time)) * 1000)
                    s3_str = f"{s3_min:02}:{s3_sec:02}.{s3_ms:03}"
                    
                    sectors_label = QLabel(f"Sector 1: {s1_str}  |  Sector 2: {s2_str}  |  Sector 3: {s3_str}")
                    sectors_label.setStyleSheet("font-size: 14px; color: #374151;")
                    best_lap_layout.addWidget(sectors_label)
                else:
                    no_data_label = QLabel("No valid lap data available")
                    no_data_label.setStyleSheet("font-size: 16px; color: #6b7280;")
                    best_lap_layout.addWidget(no_data_label)
            
            best_lap_layout.addStretch()
            
            # -=Track Map=-
            track_map = self.make_track_map_widget(venue)
            track_map.setFixedSize(900, 750) 
            track_map.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            
            quali_content_layout.addWidget(best_lap_card, alignment=Qt.AlignTop | Qt.AlignLeft)
            quali_content_layout.addWidget(track_map, alignment=Qt.AlignTop | Qt.AlignLeft)
            quali_content_layout.addStretch()
            
            layout.addLayout(quali_content_layout)

        # -=PRACTICE SPECIFIC: Table and Track Map=-
        if session_type == "Practice":
            # -=Horizontal layout for table and track map=-
            content_layout = QHBoxLayout()
            content_layout.setSpacing(20)

            # -=Table Data=-
            df_valid = self.telemetry_df[
                (self.telemetry_df["Lap"] > 0) &
                (self.telemetry_df["LapLastLapTime"] > 0)
            ].copy()

            laps_completed = int(sorted(df_valid["Lap"].dropna().unique())[-1])
            fastest_lap_seconds = df_valid["LapLastLapTime"].min()
            minutes = int(fastest_lap_seconds // 60)
            seconds = int(fastest_lap_seconds % 60)
            millis = int((fastest_lap_seconds - int(fastest_lap_seconds)) * 1000)
            fastest_lap_formatted = f"{minutes:02}:{seconds:02}.{millis:03}"
            fastest_lap_on = int(df_valid.loc[df_valid["LapLastLapTime"].idxmin()]["Lap"])

            overview_df = pd.DataFrame({
                "Metric": ["Laps Completed", "Fastest Lap", "Fastest Lap Set On"],
                "Value": [laps_completed, fastest_lap_formatted, fastest_lap_on]
            })

            # -=Table Widget=-
            table = QTableWidget(len(overview_df), len(overview_df.columns))
            table.horizontalHeader().setVisible(False)
            table.verticalHeader().setVisible(False)
            table.setFrameShape(QFrame.NoFrame)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionMode(QTableWidget.NoSelection)

            # Fill table
            for row in range(len(overview_df)):
                for col in range(len(overview_df.columns)):
                    item = QTableWidgetItem(str(overview_df.iat[row, col]))
                    if col == 0:
                        item.setFlags(Qt.ItemIsEnabled)
                    table.setItem(row, col, item)

            # Column sizing
            h_header = table.horizontalHeader()
            h_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            h_header.setSectionResizeMode(1, QHeaderView.Stretch)

            # Set fixed table size
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

            # -=Track Map=-
            track_map = self.make_track_map_widget(venue)
            track_map.setFixedSize(600, 500) 
            table.setContentsMargins(0, 0, 0, 0)
            table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            content_layout.addWidget(table, alignment=Qt.AlignTop | Qt.AlignLeft)
            content_layout.addWidget(track_map, alignment=Qt.AlignTop | Qt.AlignLeft)
            content_layout.addStretch()  

            layout.addLayout(content_layout)

        # -=RACE SPECIFIC: Race Summary Table + Position Tracking=-
        if session_type == "Race":
            top_layout = QHBoxLayout()
            top_layout.setSpacing(int(24 * self.scale_factor))

            left_column = QVBoxLayout()
            left_column.setSpacing(int(24 * self.scale_factor))

            df_valid = self.telemetry_df[
                (self.telemetry_df["Lap"] > 0)
            ].copy()

            lap_1_data = self.telemetry_df[self.telemetry_df["Lap"] == 1]
            if len(lap_1_data) > 0:
                starting_position = int(lap_1_data["PlayerCarClassPosition"].iloc[0])
            else:
                starting_position = 0

            last_lap = df_valid["Lap"].max()
            last_lap_data = self.telemetry_df[self.telemetry_df["Lap"] == last_lap]
            if len(last_lap_data) > 0:
                finishing_position = int(last_lap_data["PlayerCarClassPosition"].iloc[-1])
            else:
                finishing_position = 0

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
            if hours > 0:
                race_time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            else:
                race_time_str = f"{minutes:02}:{seconds:02}"

            race_df = pd.DataFrame({
                "Metric": [
                    "Starting Position",
                    "Finishing Position", 
                    "Position Change",
                    "Race Length (Laps)",
                    "Race Length (Time)"
                ],
                "Value": [
                    starting_position,
                    finishing_position,
                    position_change_str,
                    total_laps,
                    race_time_str
                ]
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

            actual_height = 0
            for row in range(summary_table.rowCount()):
                actual_height += summary_table.rowHeight(row)

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
                            change_str = f"▲ {change}"
                            change_color = "#22c55e"
                        elif change < 0:
                            change_str = f"▼ {abs(change)}"
                            change_color = "#ef4444"
                        else:
                            change_str = "—"
                            change_color = "#6b7280"
                    else:
                        change_str = "—"
                        change_color = "#6b7280"
                    
                    lap_positions.append({
                        'lap': int(lap),
                        'position': position,
                        'change_str': change_str,
                        'change_color': change_color
                    })
                    
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
            actual_height = header_height
            for row in range(position_table.rowCount()):
                actual_height += position_table.rowHeight(row)

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

            from matplotlib.backends.backend_qt5agg import FigureCanvas
            from matplotlib.figure import Figure
            
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
            
            ax.spines['top'].set_color('black')
            ax.spines['bottom'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.spines['right'].set_color('black')
            ax.spines['top'].set_linewidth(2)
            ax.spines['bottom'].set_linewidth(2)
            ax.spines['left'].set_linewidth(2)
            ax.spines['right'].set_linewidth(2)

            fig.tight_layout()

            canvas.setFixedSize(int(1341 * self.scale_factor), int(353 * self.scale_factor))
            layout.addWidget(canvas)


        layout.addStretch()

        return page

    def make_race_track_map_widget(self, venue, scale_factor=1.0):
        """Create track map with overtake markers for race overview"""
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        
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
        
        print(f"Using lap {target_lap} for track outline")
        print(f"Lap data points: {len(lap_data)}")

        if len(lap_data) > 0:
            lat = lap_data["Lat"].values
            lon = lap_data["Lon"].values
            
            print(f"Lat range: {lat.min()} to {lat.max()}")
            print(f"Lon range: {lon.min()} to {lon.max()}")
            
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
        else:
            print("ERROR: No lap data found for track outline!")

        if hasattr(self, 'race_overtakes'):
            print(f"Total overtakes: {len(self.race_overtakes)}")
            for i, overtake in enumerate(self.race_overtakes):
                
                if overtake['is_gain'] and self.show_overtakes:
                    ax.scatter(overtake['lon'], overtake['lat'], 
                            color='#22c55e', s=150, zorder=3)
                elif not overtake['is_gain'] and self.show_overtaken:
                    ax.scatter(overtake['lon'], overtake['lat'], 
                            color='#ef4444', s=150, zorder=3)

        ax.set_aspect('equal', adjustable='datalim')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_color('black')
        ax.spines['bottom'].set_color('black')
        ax.spines['left'].set_color('black')
        ax.spines['right'].set_color('black')
        ax.spines['top'].set_linewidth(2)
        ax.spines['bottom'].set_linewidth(2)
        ax.spines['left'].set_linewidth(2)
        ax.spines['right'].set_linewidth(2)
    
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
                        ann = ax.annotate(tooltip_text,
                                        xy=(overtake['lon'], overtake['lat']),
                                        xytext=(10, 10), textcoords='offset points',
                                        bbox=dict(boxstyle='round,pad=0.5', 
                                                fc='yellow', alpha=0.9),
                                        fontsize=10, fontweight='bold')
                        self.race_map_annotations.append(ann)
                        canvas.draw_idle()
                        break
            
            if len(self.race_map_annotations) == 0:
                canvas.draw_idle()
        
        canvas.mpl_connect('motion_notify_event', on_hover)
        
        return canvas

    def toggle_race_overtakes(self):
        """Toggle visibility of overtake markers (green dots)"""
        self.show_overtakes = self.race_overtake_btn.isChecked()
        self.update_race_track_map()

    def toggle_race_overtaken(self):
        """Toggle visibility of overtaken markers (red dots)"""
        self.show_overtaken = self.race_overtaken_btn.isChecked()
        self.update_race_track_map()

    def update_race_track_map(self):
        """Redraw the race track map with updated overtake visibility"""
        if hasattr(self, 'race_track_map_widget'):
            parent_layout = self.race_track_map_widget.parent().layout()

            parent_layout.removeWidget(self.race_track_map_widget)
            self.race_track_map_widget.deleteLater()

            venue = self.session_info.get("Venue", "Unknown Venue")
            self.race_track_map_widget = self.make_race_track_map_widget(venue, self.scale_factor)
            parent_layout.addWidget(self.race_track_map_widget)
            
    def update_overview_lap_list(self):
        """Update lap list based on selected order - uses same calculation as timing screen"""
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
            minutes = int(lap_time // 60)
            seconds = int(lap_time % 60)
            millis = int((lap_time - int(lap_time)) * 1000)
            time_str = f"{minutes:02}:{seconds:02}.{millis:03}"
            
            self.overview_lap_list.addItem(f"Lap {display_lap_counter}: {time_str}")
            display_lap_counter += 1
                
    def on_overview_lap_selected(self, item):
        """Handle lap selection from overview page"""
        lap_text = item.text()
        lap_num = int(lap_text.split(":")[0].replace("Lap ", ""))
        print(f"Selected lap {lap_num} from overview")
   
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # -----------------------
    # Make a page for the stacked widget
    # -----------------------
    def make_page(self, title):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #1f2937;
        """)

        
        layout.addWidget(label)
        

        
        if title == "Data Viewer":
            self.table = QTableWidget()
            self.table.setStyleSheet("""
                QTableWidget {
                    background-color: #f2f2f2;
                    color: #000000;
                    gridline-color: #cccccc;
                    font-size: 12px;
                }
                QHeaderView::section {
                    background-color: #2c3e50;
                    color: white;
                    font-weight: bold;
                    border: none;
                    padding: 4px;
                }
                QTableWidget::item:selected {
                    background-color: #3498db;
                    color: white;
                }
            """)

            # Make table scrollable
            self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

            layout.addWidget(self.table) 

        return page
    

    #================
    # Timings Page
    #================
    def make_timings_page(self):
        page = QWidget()
    
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title = QLabel("Session Timings")
        title.setStyleSheet("""
            font-size: 38px;
            font-weight: bold;
            color: #000007;
        """)
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        self.speed_map_unit = 'kmh'

        # Calculate all lap data for the session
        self.calculate_lap_timings()

        # Session Statistics Bar
        stats_bar = self.create_session_stats_bar()
        layout.addWidget(stats_bar)

        # Main content area - Table and Map side by side
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # lap timings TabLE
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(5)

        table_title = QLabel("Lap Times & Sectors")
        table_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000;")
        table_layout.addWidget(table_title)

        self.timing_table = self.create_timing_table()
        table_layout.addWidget(self.timing_table)

        table_container.setFixedWidth(int(850 * self.scale_factor))
        content_layout.addWidget(table_container)

        # Track Map
        map_container = QWidget()
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.setSpacing(2)

        # Map toggle
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
                background-color: #e5e7eb;
                color: #6b7280;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #2563eb;
                color: white;
                border: 1px solid #2563eb;
            }
            QPushButton:hover {
                background-color: #d1d5db;
            }
            QPushButton:checked:hover {
                background-color: #1d4ed8;
            }
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


        
        # Lap time chart (now it won't overlap)
        lap_chart = self.create_lap_time_chart()
        if lap_chart:
            layout.addWidget(lap_chart)

        # Set content to scroll area
        scroll.setWidget(content_widget)
        
        # Page layout
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        # Initialize map
        self.draw_timing_map()

        return page
    
    #TODO sectors not adding up properly
    def calculate_lap_timings(self):
        self.lap_timings = {}
        
        valid_laps = sorted(self.telemetry_df[self.telemetry_df["Lap"] > 0]["Lap"].unique())

        for lap in valid_laps:  
            lap_data = self.telemetry_df[
                (self.telemetry_df["Lap"] == lap)
            ].copy()

            if len(lap_data) == 0:
                continue

            # iRacing does not report lap time of last lap in session due to cooldown lap not being fully completed, 
            # therefore i use session ticks (60 per second) to calculate the time (usually off by +- .006s)
            lap_time_rows = self.telemetry_df[
                (self.telemetry_df["Lap"] == lap + 1) &
                (self.telemetry_df["LapLastLapTime"] > 0)
            ]["LapLastLapTime"]

            if len(lap_time_rows) > 0:
                lap_time = lap_time_rows.iloc[-1]  
            else:
                if len(lap_data) > 1:
                    lap_time = (lap_data["SessionTick"].iloc[-1] - lap_data["SessionTick"].iloc[0]) / 60
                else:
                    continue

            if lap_time <= 0:
                continue

            is_on_track = (lap_data["IsOnTrack"] == 1).all()

            # Check for distance anomalies (going backwards or off track)
            lap_data_sorted_by_time = lap_data.sort_values("SessionTime")
            dist_pct = lap_data_sorted_by_time["LapDistPct"].values
            is_monotonic = True
            if len(dist_pct) > 1:
                for i in range(1, len(dist_pct)):
                    if dist_pct[i] < dist_pct[i-1] - 5:
                        is_monotonic = False
                        break

            # check for if car has gone off track or not to count a valid lap
            speeds = lap_data_sorted_by_time["Speed"].values * 3.6 
            has_speed_anomaly = False
            if len(speeds) > 10:
                slow_count = (speeds < 20).sum()
                if slow_count > 60:  
                    has_speed_anomaly = True

            is_valid = is_on_track and is_monotonic and not has_speed_anomaly
           
            print(f"\n=== Lap {lap} Validity Check ===")
            print(f"is_on_track: {is_on_track}")
            print(f"is_monotonic: {is_monotonic}")
            print(f"IsOnTrackCar values: {lap_data['IsOnTrackCar'].value_counts().to_dict()}")
            print(f"LapDistPct range: {dist_pct.min():.2f} to {dist_pct.max():.2f}")
            print(f"Final is_valid: {is_valid}")

            # Calculate sector times based on LapDistPct
            lap_data_sorted = lap_data.sort_values("SessionTime").reset_index(drop=True)

            if len(lap_data_sorted) > 0:
                lap_start_time = lap_data_sorted["SessionTime"].iloc[0]
                lap_end_time = lap_data_sorted["SessionTime"].iloc[-1]
                
                # Find times at sector boundaries by finding closest LapDistPct
                # Sector 1 ends at 33.33%
                sector1_rows = lap_data_sorted[lap_data_sorted["LapDistPct"] <= 33.33]
                if len(sector1_rows) > 0:
                    sector1_end_time = sector1_rows["SessionTime"].iloc[-1]
                else:
                    sector1_end_time = lap_start_time
                
                # Sector 2 ends at 66.66%
                sector2_rows = lap_data_sorted[lap_data_sorted["LapDistPct"] <= 66.66]
                if len(sector2_rows) > 0:
                    sector2_end_time = sector2_rows["SessionTime"].iloc[-1]
                else:
                    sector2_end_time = sector1_end_time
                
                # Calculate sector times
                sector1_time = sector1_end_time - lap_start_time
                sector2_time = sector2_end_time - sector1_end_time
                sector3_time = lap_end_time - sector2_end_time
            else:
                sector1_time = 0
                sector2_time = 0
                sector3_time = 0

            # Format lap time
            minutes = int(lap_time // 60)
            seconds = int(lap_time % 60)
            millis = int((lap_time - int(lap_time)) * 1000)
            lap_time_str = f"{minutes:02}:{seconds:02}.{millis:03}"

            self.lap_timings[int(lap)] = {
                'time': lap_time,
                'time_str': lap_time_str,
                'sector1': sector1_time,
                'sector2': sector2_time,
                'sector3': sector3_time,
                'is_valid': is_valid
            }

        # Remove the last lap (incomplete cooldown lap) BEFORE finding best lap
        if len(self.lap_timings) > 0:
            last_lap = max(self.lap_timings.keys())
            if last_lap in self.lap_timings:
                del self.lap_timings[last_lap]

        # Find best lap (OUTSIDE the loop)
        valid_lap_times = {lap: data['time'] for lap, data in self.lap_timings.items() 
                        if data['is_valid'] and data['time'] != float('inf')}
        
        if valid_lap_times:
            self.best_lap = min(valid_lap_times, key=valid_lap_times.get)
            self.best_lap_time = valid_lap_times[self.best_lap]
        else:
            self.best_lap = None
            self.best_lap_time = None

        # Calculate deltas to best lap (OUTSIDE the loop)
        if self.best_lap is not None:
            for lap in self.lap_timings:
                delta = self.lap_timings[lap]['time'] - self.best_lap_time
                self.lap_timings[lap]['delta'] = delta
                if abs(delta) < 0.001:
                    self.lap_timings[lap]['delta_str'] = "—"
                elif delta > 0:
                    self.lap_timings[lap]['delta_str'] = f"+{delta:.3f}s"
                else:
                    self.lap_timings[lap]['delta_str'] = f"{delta:.3f}s"

    def create_map_legend(self, items, title):
        legend_widget = QWidget()
        legend_widget.setFixedWidth(int(150 * self.scale_factor))
        legend_widget.setFixedHeight(int(350 * self.scale_factor)) 
        legend_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
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
            color_box.setStyleSheet(f"""
                background-color: {color};
                border: 1px solid #d1d5db;
                border-radius: 3px;
            """)
            
            text_label = QLabel(label)
            text_label.setStyleSheet("font-size: 11px; color: #111827;")
            
            item_layout.addWidget(color_box)
            item_layout.addWidget(text_label)
            item_layout.addStretch()
            
            legend_layout.addLayout(item_layout)

        legend_layout.addStretch()
        return legend_widget

    def create_speed_colourbar(self, min_speed, max_speed, unit='kmh'):
        from matplotlib.figure import Figure
        from matplotlib import cm
        from matplotlib.colors import Normalize
        import numpy as np

        # MPH Conversion
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
        
        # mph kph toggler
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
                background-color: #e5e7eb;
                color: #6b7280;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #2563eb;
                color: white;
                border: 1px solid #2563eb;
            }
            QPushButton:hover {
                background-color: #d1d5db;
            }
            QPushButton:checked:hover {
                background-color: #1d4ed8;
            }
        """
        self.speed_map_unit_kmh.setStyleSheet(unit_toggle_style)
        self.speed_map_unit_mph.setStyleSheet(unit_toggle_style)
        
        self.speed_map_unit_kmh.clicked.connect(lambda: self.toggle_speed_map_unit("kmh"))
        self.speed_map_unit_mph.clicked.connect(lambda: self.toggle_speed_map_unit("mph"))
        
        unit_toggle_layout.addWidget(self.speed_map_unit_kmh)
        unit_toggle_layout.addWidget(self.speed_map_unit_mph)
        unit_toggle_layout.addStretch()
        
        container_layout.addLayout(unit_toggle_layout)

        # Colourbar figure TODO: ENSURE WIDE ENOUGH FIG's ARE VISIBLE (esp 3digit)
        colourbar_widget = QWidget()
        colourbar_widget.setFixedWidth(int(300 * self.scale_factor))
        colourbar_widget.setFixedHeight(int(390 * self.scale_factor))
        
        fig = Figure(figsize=(2, 4), facecolor='#bfbec1')
        ax = fig.add_subplot(111)

        # Create colourbar
        norm = Normalize(vmin=min_speed, vmax=max_speed)
        cmap = cm.get_cmap('RdYlGn')
        
        gradient = np.linspace(0, 1, 256).reshape(256, 1)
        ax.imshow(gradient, aspect='auto', cmap=cmap, origin='lower')
        
        ax.set_xticks([])
        ax.set_yticks([0, 64, 128, 192, 255])
        ax.set_yticklabels([f'{min_speed:.0f}', f'{max_speed*0.25:.0f}', 
                            f'{max_speed*0.5:.0f}', f'{max_speed*0.75:.0f}', 
                            f'{max_speed:.0f}'])
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
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
        """)

        layout = QHBoxLayout(stats_bar)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(40)

        #POTENTIAL TODO: check for variable of penalty points accrued over session could be added to score (only in RACE scenario)
        # SESSION statistics calculations
        valid_times = [data['time'] for data in self.lap_timings.values() 
                    if data['is_valid'] and data['time'] != float('inf')]
        
        if len(valid_times) == 0:
            # case of no valid laps being set
            no_data_label = QLabel("No valid laps recorded")
            no_data_label.setStyleSheet("font-size: 16px; color: #6b7280;")
            layout.addWidget(no_data_label)
            return stats_bar

        import numpy as np
        
        fastest_time = min(valid_times)
        average_time = np.mean(valid_times)
        median_time = np.median(valid_times)
        std_dev = np.std(valid_times)
        
        total_laps = len(self.lap_timings)
        valid_laps = len(valid_times)
        valid_percentage = (valid_laps / total_laps * 100) if total_laps > 0 else 0

        # Format times
        def format_time(seconds):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            millis = int((seconds - int(seconds)) * 1000)
            return f"{minutes:02}:{secs:02}.{millis:03}"

        # consistency score calculation
        consistency_grade, grade_color = self.calculate_consistency_grade(std_dev, valid_percentage)

        # Fastest Lap
        fastest_widget = self.create_stat_widget("Fastest Lap", 
                                                f"{format_time(fastest_time)}\n(Lap {self.best_lap})")
        layout.addWidget(fastest_widget)

        # Average Lap
        average_widget = self.create_stat_widget("Average Lap", format_time(average_time))
        layout.addWidget(average_widget)

        # Median Lap
        median_widget = self.create_stat_widget("Median Lap", format_time(median_time))
        layout.addWidget(median_widget)

        # Standard Deviation
        std_dev_widget = self.create_stat_widget("Std Deviation", f"±{std_dev:.3f}s")
        layout.addWidget(std_dev_widget)

        # Valid Laps (x/y) 
        valid_widget = self.create_stat_widget("Valid Laps", f"{valid_laps} / {total_laps}\n({valid_percentage:.0f}%)")
        layout.addWidget(valid_widget)

        # Consistency Grade awarded
        grade_widget = QWidget()
        grade_layout = QVBoxLayout(grade_widget)
        grade_layout.setSpacing(3)
        grade_layout.setContentsMargins(15, 5, 15, 5)
        
        grade_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {grade_color};
                border-radius: 6px;
                border: 2px solid #d1d5db;
            }}
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
    
    # CONSITENCY SCORE MATRIX FUNCTION (potential tweaking necessary in case of unrealistic goals/expectations potential add an SS+ grade r sth)
    def calculate_consistency_grade(self, std_dev, valid_percentage):
        # Lap time consistency score
        if std_dev < 0.1:
            time_score = 100
        elif std_dev < 0.2:
            time_score = 95
        elif std_dev < 0.3:
            time_score = 90
        elif std_dev < 0.5:
            time_score = 85
        elif std_dev < 0.8:
            time_score = 75
        elif std_dev < 1.2:
            time_score = 65
        else:
            time_score = 50

        # Valid lap percentage score
        if valid_percentage >= 100:
            valid_score = 100
        elif valid_percentage >= 90:
            valid_score = 95
        elif valid_percentage >= 80:
            valid_score = 85
        elif valid_percentage >= 70:
            valid_score = 75
        elif valid_percentage >= 60:
            valid_score = 65
        elif valid_percentage >= 50:
            valid_score = 55
        else:
            valid_score = 45

        # Combined score (60% time, 40% valid)
        final_score = (time_score * 0.6) + (valid_score * 0.4)

        # Assign grade
        if final_score >= 95:
            grade = "S+"
            color = "#ffd700"  # Gold
        elif final_score >= 90:
            grade = "S"
            color = "#c0c0c0"  # Silver
        elif final_score >= 85:
            grade = "A+"
            color = "#90EE90"  # Light green
        elif final_score >= 80:
            grade = "A"
            color = "#98FB98"  # Pale green
        elif final_score >= 70:
            grade = "B"
            color = "#87CEEB"  # Sky blue
        elif final_score >= 60:
            grade = "C"
            color = "#FFD580"  # Light orange
        else:
            grade = "D"
            color = "#FFB6C1"  # Light pink

        return grade, color

    def create_timing_table(self):
        table = QTableWidget()
        
        # Set up table
        headers = ["Lap", "Lap Time", "Sector 1", "Sector 2", "Sector 3", "Delta", "Valid"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(self.lap_timings))

        # Enable sorting
        table.setSortingEnabled(False)  

        # Style table
        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #e5e7eb;
                font-size: 16px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                color: #111827;
                font-weight: bold;
                font-size: 15px;
                border: none;
                border-right: 1px solid #d1d5db;
                border-bottom: 2px solid #9ca3af;
                padding: 8px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f3f4f6;
                color: #000000;
            }
            QTableWidget::item:selected {
                background-color: #dbeafe;
                color: #111827;
            }
        """)

        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)

        table.setColumnWidth(0, int(70 * self.scale_factor))
        table.setColumnWidth(6, int(70 * self.scale_factor))

        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Populate table
        for row, (lap, data) in enumerate(sorted(self.lap_timings.items())):
            # Lap number
            lap_item = QTableWidgetItem()
            lap_item.setData(Qt.DisplayRole, lap) 
            lap_item.setTextAlignment(Qt.AlignCenter)
            
            # Lap time
            time_item = QTableWidgetItem(data['time_str'])
            time_item.setTextAlignment(Qt.AlignCenter)
            
            # Sector times
            def format_sector(seconds):
                if seconds == 0:
                    return "—"
                return f"{seconds:.3f}s"
            
            s1_item = QTableWidgetItem(format_sector(data['sector1']))
            s1_item.setTextAlignment(Qt.AlignCenter)
            
            s2_item = QTableWidgetItem(format_sector(data['sector2']))
            s2_item.setTextAlignment(Qt.AlignCenter)
            
            s3_item = QTableWidgetItem(format_sector(data['sector3']))
            s3_item.setTextAlignment(Qt.AlignCenter)
            
            # Delta
            delta_item = QTableWidgetItem(data.get('delta_str', '—'))
            delta_item.setTextAlignment(Qt.AlignCenter)
            
            # Valid
            valid_item = QTableWidgetItem("✓" if data['is_valid'] else "✗")
            valid_item.setTextAlignment(Qt.AlignCenter)
            
            # Highlight best lap
            if self.best_lap is not None and lap == self.best_lap:
                for item in [lap_item, time_item, s1_item, s2_item, s3_item, delta_item, valid_item]:
                    item.setBackground(QColor("#d4edda")) 
            
            # Gray out invalid laps
            if not data['is_valid']:
                for item in [lap_item, time_item, s1_item, s2_item, s3_item, delta_item, valid_item]:
                    item.setForeground(QColor("#9ca3af"))
            
            table.setItem(row, 0, lap_item)
            table.setItem(row, 1, time_item)
            table.setItem(row, 2, s1_item)
            table.setItem(row, 3, s2_item)
            table.setItem(row, 4, s3_item)
            table.setItem(row, 5, delta_item)
            table.setItem(row, 6, valid_item)

        # Enable sorting after populating
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
        
        #redraw map after user selects a lap in lap selector
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
        
        # Store the preference
        self.speed_map_unit = unit
        
        # Redraw map with current lap selection
        selected_items = self.timing_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            lap_item = self.timing_table.item(row, 0)
            selected_lap = int(lap_item.text())
            self.draw_timing_map(selected_lap)
        else:
            self.draw_timing_map()

    def draw_timing_map(self, selected_lap=None):
        from matplotlib.figure import Figure
        from matplotlib.collections import LineCollection
        import numpy as np

        # clear map
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

        # Use selected lap or default to best lap
        if selected_lap is None:
            selected_lap = self.best_lap

        # Check if selected lap exists in lap_timings (might have been deleted if it was incomplete)
        if selected_lap not in self.lap_timings:
            # Fall back to best lap
            if self.best_lap and self.best_lap in self.lap_timings:
                selected_lap = self.best_lap
            else:
                # Just use any valid lap
                if len(self.lap_timings) > 0:
                    selected_lap = min(self.lap_timings.keys())
                else:
                    error_label = QLabel("No valid laps to display")
                    error_label.setAlignment(Qt.AlignCenter)
                    error_label.setStyleSheet("font-size: 14px; color: #6b7280;")
                    self.timing_map_layout.addWidget(error_label)
                    return

        # Get Selected Lap data
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

        # Create figure
        fig = Figure(figsize=(8, 8), facecolor='#bfbec1')
        ax = fig.add_subplot(111)

        points = np.array([lap_data["Lon"].values, lap_data["Lat"].values]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        if self.timing_map_delta.isChecked():
            # Delta mode - compare to best lap
            if selected_lap == self.best_lap:
                colors = ['#22c55e'] * len(segments)
            else:
                # compare selected lap to best lap
                best_lap_data = self.telemetry_df[
                    (self.telemetry_df["Lap"] == self.best_lap) &
                    (self.telemetry_df["IsOnTrackCar"] == 1)
                ].copy().sort_values("LapDistPct").reset_index(drop=True)
                
                colors = []
                for i in range(len(lap_data) - 1):
                    current_dist = lap_data["LapDistPct"].iloc[i]
                    current_time = lap_data["SessionTime"].iloc[i] - lap_data["SessionTime"].iloc[0]
                    
                    # find corresponding point in best lap
                    best_idx = (best_lap_data["LapDistPct"] - current_dist).abs().idxmin()
                    best_time = best_lap_data["SessionTime"].iloc[best_idx] - best_lap_data["SessionTime"].iloc[0]
                    #delta colour scheme
                    if current_time < best_time:
                        colors.append('#22c55e') 
                    else:
                        colors.append('#ef4444') 
            
            legend_title = "Delta to Best Lap"
            legend_items = [
                ('#22c55e', 'Faster'),
                ('#ef4444', 'Slower')
            ]
        else:
            from matplotlib.colors import Normalize
            from matplotlib import cm
            
            speeds_kmh = lap_data["Speed"].values * 3.6 
            
            # Get max speed across all laps for consistent scale
            all_speeds = self.telemetry_df["Speed"].values * 3.6
            max_speed = all_speeds.max()
            min_speed = 0
            
            # Normalize speeds
            norm = Normalize(vmin=min_speed, vmax=max_speed)
            ## COLOUR SCHEME for legend green->red
            cmap = cm.get_cmap('RdYlGn') 
            
            colors = [cmap(norm(speed)) for speed in speeds_kmh[:-1]]
            
            legend_title = "Speed (km/h)"
            legend_items = None  

        lc = LineCollection(segments, colors=colors, linewidths=4)
        ax.add_collection(lc)

        # Start/finish line black
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
        
        ax.set_title(f"Lap {selected_lap} - {legend_title}{title_suffix}",
                    fontsize=14, fontweight='bold', pad=10)
        ax.set_aspect('equal')
        ax.set_facecolor('white')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(lap_data["Lon"].min() - 0.0005, lap_data["Lon"].max() + 0.0005)
        ax.set_ylim(lap_data["Lat"].min() - 0.0005, lap_data["Lat"].max() + 0.0005)
        fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02)

        # Create canvas
        canvas = FigureCanvas(fig)
        canvas.setMinimumSize(int(450 * self.scale_factor), int(450 * self.scale_factor))
        canvas.setMaximumSize(int(900 * self.scale_factor), int(900 * self.scale_factor))
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create horizontal layout for map + legend
        map_legend_container = QWidget()
        map_legend_layout = QHBoxLayout(map_legend_container)
        map_legend_layout.setContentsMargins(0, 0, 0, 0)
        map_legend_layout.setSpacing(10)

        map_legend_layout.addWidget(canvas)

        # Add legend
        if legend_items is not None:
            legend_widget = self.create_map_legend(legend_items, legend_title)
            # Add some top spacing
            spacer = QWidget()
            spacer.setFixedHeight(int(50 * self.scale_factor))
            map_legend_layout.addWidget(spacer)
            map_legend_layout.addWidget(legend_widget, alignment=Qt.AlignTop)
        else:
            # Continuous legend for speed mode
            colourbar_widget = self.create_speed_colourbar(min_speed, max_speed, self.speed_map_unit)
            map_legend_layout.addWidget(colourbar_widget, alignment=Qt.AlignTop)

        self.timing_map_layout.addWidget(map_legend_container)

    def draw_timing_map_for_lap(self, lap):
        self.draw_timing_map(selected_lap=lap)

    def create_map_legend(self, items, title):

        legend_widget = QWidget()
        legend_widget.setFixedWidth(int(150 * self.scale_factor))
        legend_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
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
            color_box.setStyleSheet(f"""
                background-color: {color};
                border: 1px solid #d1d5db;
                border-radius: 3px;
            """)
                
            text_label = QLabel(label)
            text_label.setStyleSheet("font-size: 11px; color: #111827;")
                
            item_layout.addWidget(color_box)
            item_layout.addWidget(text_label)
            item_layout.addStretch()
                
            legend_layout.addLayout(item_layout)

        legend_layout.addStretch()
        return legend_widget
    
    def create_lap_time_chart(self):
        from matplotlib.figure import Figure
        import matplotlib.pyplot as plt
        from matplotlib.ticker import FuncFormatter
        import numpy as np
        
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
       
        ax.plot(lap_numbers, lap_times, color='#2563eb', linewidth=2, marker='o', 
                markersize=8, markerfacecolor='#2563eb', markeredgecolor='white', 
                markeredgewidth=2, zorder=3)
     
        best_lap_idx = lap_numbers.index(self.best_lap)
        ax.plot(self.best_lap, lap_times[best_lap_idx], 'o', markersize=14, 
                markerfacecolor='#22c55e', markeredgecolor='white', 
                markeredgewidth=2, zorder=4)
        
        # Highlight slowest lap (red)
        slowest_lap = max(self.lap_timings.keys(), key=lambda x: self.lap_timings[x]['time'])
        slowest_lap_idx = lap_numbers.index(slowest_lap)
        ax.plot(slowest_lap, lap_times[slowest_lap_idx], 'o', markersize=14, 
                markerfacecolor='#ef4444', markeredgecolor='white', 
                markeredgewidth=2, zorder=4)

        # y axis limits with 2s padding
        min_time = min(lap_times)
        max_time = max(lap_times)
        ax.set_ylim(min_time - 2, max_time + 2)
        
        # Format Y axis as mm:ss.ms
        def format_time(seconds, pos):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            millis = int((seconds - int(seconds)) * 1000)
            return f"{minutes:02}:{secs:02}.{millis:03}"
        
        ax.yaxis.set_major_formatter(FuncFormatter(format_time))
        
       
        ax.set_xlabel("Lap Number", fontsize=11, fontweight='bold', color='#111827')
        ax.set_ylabel("Lap Time", fontsize=11, fontweight='bold', color='#111827')
        ax.set_title("Lap Time Progression", fontsize=13, fontweight='bold', 
                    color='#111827', pad=10)
        
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
        
        # hover tooltip with lap info
        def on_hover(event):
            if event.inaxes == ax:
                for i, (lap_num, lap_time) in enumerate(zip(lap_numbers, lap_times)):
                    if abs(event.xdata - lap_num) < 0.3 and abs(event.ydata - lap_time) < 0.5:
                        minutes = int(lap_time // 60)
                        secs = int(lap_time % 60)
                        millis = int((lap_time - int(lap_time)) * 1000)
                        tooltip_text = f"Lap {lap_num}: {minutes:02}:{secs:02}.{millis:03}"
                        QToolTip.showText(canvas.mapToGlobal(event.guiEvent.pos()), tooltip_text)
                        return
                QToolTip.hideText()
        
        
        return canvas
    

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    #================
    # Tyre Data Page
    #================
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
        title.setStyleSheet("""
            font-size: 38px;
            font-weight: bold;
            color: #000007;
        """)
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        main_content = QHBoxLayout()
        main_content.setSpacing(15)

        left_column = QVBoxLayout()
        left_column.setSpacing(10)

        # Lap selector
        lap_selector_container = QWidget()
        lap_selector_container.setFixedWidth(int(280 * self.scale_factor))
        lap_selector_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 0px;
                border: none;
            }
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
            QListWidget {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                font-size: 18px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f3f4f6;
                color: #000000;
            }
            QListWidget::item:selected {
                background-color: #2563eb;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #eff6ff;
                color: #000000;
            }
        """)
        self.tyre_lap_list.itemClicked.connect(self.update_tyre_data_display)
        lap_selector_layout.addWidget(self.tyre_lap_list)

        for lap in sorted(self.lap_timings.keys()):
            lap_info = self.lap_timings[lap]
            item_text = f"Lap {lap} - {lap_info['time_str']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, lap)
            self.tyre_lap_list.addItem(item)

        lap_selector_wrapper = QWidget()
        lap_selector_wrapper.setFixedWidth(int(284 * self.scale_factor))
        lap_selector_wrapper.setFixedHeight(int(900 * self.scale_factor))
        lap_selector_wrapper.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #000000;
                border-radius: 8px;
            }
        """)
        lap_selector_wrapper_layout = QVBoxLayout(lap_selector_wrapper)
        lap_selector_wrapper_layout.setContentsMargins(2, 2, 2, 2)
        lap_selector_wrapper_layout.addWidget(lap_selector_container)

        left_column.addWidget(lap_selector_wrapper)


        right_column = QVBoxLayout()
        right_column.setSpacing(10)

        # top down tyreview + track map
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
    
    # getting tyre temps and assigning colour grom blue-teal-green-yellow-orange-red colour spectrum in relation to tyre temps
    # i've used a wide range here as optimal tyre temps can vary heavily across different car classes
    def get_tyre_temp_color(self, temp):
        if temp < 50:
            return '#0ea5e9' 
        elif temp < 65:
            #cold
            ratio = (temp - 50) / 15
            return self.interpolate_color('#0ea5e9', '#14b8a6', ratio)
        elif temp < 80:
            #low optimal
            ratio = (temp - 65) / 15
            return self.interpolate_color('#14b8a6', '#22c55e', ratio)
        elif temp < 90:
            # high optimal
            ratio = (temp - 80) / 10
            return self.interpolate_color('#22c55e', '#eab308', ratio)
        elif temp < 100:
            #slightly hot
            ratio = (temp - 90) / 10
            return self.interpolate_color('#eab308', '#f97316', ratio)
        elif temp < 110:
            #very hot
            ratio = (temp - 100) / 10
            return self.interpolate_color('#f97316', '#ef4444', ratio)
        else:
            return '#ef4444'

    def interpolate_color(self, color1, color2, ratio):
        c1 = [int(color1[i:i+2], 16) for i in (1, 3, 5)]
        c2 = [int(color2[i:i+2], 16) for i in (1, 3, 5)]
        
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        
        return f'#{r:02x}{g:02x}{b:02x}'
    
    # top down view of car to display tyre temp data, each tyre is split into the three parts to reflect the inner, centre, and outer tyre temps similar to the display in Assetto Corsa Competizione
    def create_tyre_top_down_visual(self, lap):
        from matplotlib.figure import Figure
        from matplotlib.patches import Rectangle
        import numpy as np
        
        lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap].copy()
        if len(lap_data) == 0:
            return None

        tyres = {
            'LF': {
                'L': lap_data['LFtempL'].mean(), 
                'M': lap_data['LFtempM'].mean(), 
                'R': lap_data['LFtempR'].mean(),
            },
            'RF': {
                'L': lap_data['RFtempL'].mean(), 
                'M': lap_data['RFtempM'].mean(), 
                'R': lap_data['RFtempR'].mean(),
            },
            'LR': {
                'L': lap_data['LRtempL'].mean(), 
                'M': lap_data['LRtempM'].mean(), 
                'R': lap_data['LRtempR'].mean(),
            },
            'RR': {
                'L': lap_data['RRtempL'].mean(), 
                'M': lap_data['RRtempM'].mean(), 
                'R': lap_data['RRtempR'].mean(),
            },
        }
                
        fig = Figure(figsize=(10, 8), facecolor="#ffffff")
        ax = fig.add_subplot(111)
        
        self.tyre_top_down_ax = ax
        
        # "body" of car
        car_body = Rectangle((2.05, 0.8), 3.5, 6.5, facecolor='#9ca3af', edgecolor='#000000', linewidth=2)
        ax.add_patch(car_body)
        
        # wheel sizes
        tyre_width = 1.6
        tyre_height = 2.1
        segment_width = tyre_width / 3
        
        # positions
        tyre_positions = [
            (0.3, 5.5, 'LF', tyres['LF']),
            (5.7, 5.5, 'RF', tyres['RF']),
            (0.3, 0.2, 'LR', tyres['LR']),
            (5.7, 0.2, 'RR', tyres['RR']),
        ]
        
        for x, y, label, temps in tyre_positions:

            ax.text(x + tyre_width/2, y + tyre_height + 0.3, label, 
                ha='center', va='bottom', fontsize=14, fontweight='bold', color='#000000')

        

            for i, (segment_label, temp) in enumerate([('L', temps['L']), ('M', temps['M']), ('R', temps['R'])]):
                color = self.get_tyre_temp_color(temp)
                segment = Rectangle((x + i * segment_width, y), segment_width, tyre_height, 
                                facecolor=color, edgecolor='#000000', linewidth=1.5)
                ax.add_patch(segment)
                
                text_x = x + i * segment_width + segment_width/2
                text_y = y + tyre_height/2
                ax.text(text_x, text_y, f'{temp:.0f}°', 
                    ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        
        ax.set_xlim(-0.5, 8.5)
        ax.set_ylim(-1.0, 9.5)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_aspect('auto')
        ax.set_title(f'Lap {lap} - Tyre Temperatures (Live)', 
            fontsize=19, fontweight='bold', pad=1)
        
        fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.01)
        
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(int(800 * self.scale_factor), int(850 * self.scale_factor)) 

        top_down_wrapper = QWidget()
        top_down_wrapper.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #000000;
                border-radius: 8px;
            }
        """)
        top_down_wrapper_layout = QVBoxLayout(top_down_wrapper)
        top_down_wrapper_layout.setContentsMargins(2, 2, 2, 2)
        top_down_wrapper_layout.addWidget(canvas)

        self.tyre_top_down_canvas = canvas

        return top_down_wrapper

    def create_tyre_temp_track_map(self, lap):
        from matplotlib.figure import Figure
        from matplotlib.collections import LineCollection
        import numpy as np
        
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
        
        colors = [self.get_tyre_temp_color(temp) for temp in avg_temps[:-1]]
        
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
        
        ax.set_title(f'Lap {lap} - Tyre Temperature Track Map',
            fontsize=14, fontweight='bold', pad=10)
        ax.set_aspect('equal')
        ax.set_facecolor('white')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(lap_data["Lon"].min() - 0.0005, lap_data["Lon"].max() + 0.0005)
        ax.set_ylim(lap_data["Lat"].min() - 0.0005, lap_data["Lat"].max() + 0.0005)
        
        fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02)
        
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(850, 850)

        self.tyre_driver_dot, = ax.plot(
            lap_data["Lon"].iloc[0],
            lap_data["Lat"].iloc[0],
            'o', color='black', markersize=10, zorder=20
        )

        self.tyre_map_ax = ax

        canvas = FigureCanvas(fig)
        canvas.setFixedSize(int(850 * self.scale_factor), int(850 * self.scale_factor)) 


        self.tyre_map_canvas = canvas

        return canvas
    
    def create_tyre_temp_colorbar(self):
        from matplotlib.figure import Figure
        from matplotlib import cm
        from matplotlib.colors import LinearSegmentedColormap
        import numpy as np
        
        colorbar_container = QWidget()
        colorbar_container.setFixedWidth(int(155 * self.scale_factor))
        
        container_layout = QVBoxLayout(colorbar_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)
        
        title = QLabel("Temperature")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: #111827;")
        title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title)
        
        fig = Figure(figsize=(1.5, 6), facecolor='none')
        ax = fig.add_subplot(111)
        
        colors_list = []
        temps = np.linspace(50, 110, 100)
        for temp in temps:
            colors_list.append(self.get_tyre_temp_color(temp))
        
        gradient = np.linspace(0, 1, 256).reshape(256, 1)
        
        color_array = np.zeros((256, 3))
        for i in range(256):
            temp = 50 + (110 - 50) * (i / 255)
            hex_color = self.get_tyre_temp_color(temp)
            rgb = [int(hex_color[j:j+2], 16)/255 for j in (1, 3, 5)]
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

    # LAP time | Tyre temp - correlation graph
    def create_tyre_temp_correlation(self):
        from matplotlib.figure import Figure
        import numpy as np
        
        lap_numbers = []
        lap_times = []
        avg_temps = []
        
        for lap in sorted(self.lap_timings.keys()):
            lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap].copy()
            if len(lap_data) == 0:
                continue
            
            avg_temp = (
                lap_data['LFtempL'].mean() + lap_data['LFtempM'].mean() + lap_data['LFtempR'].mean() +
                lap_data['RFtempL'].mean() + lap_data['RFtempM'].mean() + lap_data['RFtempR'].mean() +
                lap_data['LRtempL'].mean() + lap_data['LRtempM'].mean() + lap_data['LRtempR'].mean() +
                lap_data['RRtempL'].mean() + lap_data['RRtempM'].mean() + lap_data['RRtempR'].mean()
            ) / 12
            
            lap_time = self.lap_timings[lap]['time']
            
            if lap_time != float('inf'):
                lap_numbers.append(lap)
                lap_times.append(lap_time)
                avg_temps.append(avg_temp)
        
        if len(lap_times) == 0:
            return None
        
        fig = Figure(figsize=(10, 4), facecolor='#f8f9fa')
        ax = fig.add_subplot(111)
        
        scatter = ax.scatter(avg_temps, lap_times, s=int(150 * self.scale_factor), c=lap_numbers, 
                        cmap='Pastel1', edgecolors='black', linewidths=1.3, zorder=3)
        
        for lap_num, temp, time in zip(lap_numbers, avg_temps, lap_times):
            ax.annotate(f'{lap_num}', (temp, time), 
                fontsize=8, fontweight='bold', ha='center', va='center')
        
        if len(avg_temps) > 1:
            z = np.polyfit(avg_temps, lap_times, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(min(avg_temps), max(avg_temps), 100)
            ax.plot(x_trend, p(x_trend), '--', color='#ef4444', linewidth=2, 
                alpha=0.7, label='Trend', zorder=2)
            
            correlation = np.corrcoef(avg_temps, lap_times)[0, 1]
            ax.text(0.98, 0.98, f'Correlation: {correlation:.3f}',
                transform=ax.transAxes, ha='right', va='top',
                fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_xlabel('Average Tyre Temperature (°C)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_ylabel('Lap Time (s)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_title('Lap Time vs Tyre Temperature Correlation', 
                    fontsize=13, fontweight='bold', color='#111827', pad=10)
        
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
            QWidget {
                background-color: white;
                border: 2px solid #000000;
                border-radius: 8px;
            }
        """)
        correlation_wrapper_layout = QVBoxLayout(correlation_wrapper)
        correlation_wrapper_layout.setContentsMargins(4, 4, 4, 4)
        correlation_wrapper_layout.addWidget(canvas)

        return correlation_wrapper
    
    #Avg tyre temp through lap line chart
    def create_tyre_temp_line_chart(self, lap):
        from matplotlib.figure import Figure
        import numpy as np
        
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
        
        #Optimal temp range TODO: verify
        ax.axhspan(60, 80, alpha=0.1, color='green')
        
        # sweepeing line in tandem with playback positioning
        self.tyre_sweep_line = ax.axvline(x=0, color='black', linewidth=2, linestyle='-', alpha=0.7, zorder=10)
        
        ax.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_ylabel('Temperature (°C)', fontsize=11, fontweight='bold', color='#111827')
        ax.set_title(f'Lap {lap} - Tyre Temperature Progression', 
                    fontsize=13, fontweight='bold', color='#111827', pad=10)
        
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
            QWidget {
                background-color: white;
                border: 2px solid #000000;
                border-radius: 8px;
            }
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
        
        self.current_tyre_lap_data = self.telemetry_df[
            self.telemetry_df["Lap"] == selected_lap
        ].copy()
        self.current_tyre_lap_data = self.current_tyre_lap_data.sort_values("SessionTick").reset_index(drop=True)
        
        self.tyre_playback_index = 0
        self.tyre_current_tick = 0
        self.tyre_playback_active = False
        
        if not hasattr(self, 'tyre_playback_timer'):
            self.tyre_playback_timer = QTimer()
            self.tyre_playback_timer.timeout.connect(self.tyre_playback_step)
        
        while self.tyre_visual_layout.count():
            child = self.tyre_visual_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        while self.tyre_map_layout.count():
            child = self.tyre_map_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        while self.tyre_correlation_layout.count():
            child = self.tyre_correlation_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        while self.tyre_chart_layout.count():
            child = self.tyre_chart_layout.takeAt(0)
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
            QPushButton {
                background-color: #2563eb;
                color: white;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.tyre_play_pause_btn.clicked.connect(self.toggle_tyre_playback)

        self.tyre_reset_btn = QPushButton("↺ Reset")
        self.tyre_reset_btn.setFixedWidth(100)
        self.tyre_reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.tyre_reset_btn.clicked.connect(self.reset_tyre_playback)

        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: black;")

        self.tyre_speed_selector = QComboBox()
        self.tyre_speed_selector.addItem("1x", 1)
        self.tyre_speed_selector.addItem("2x", 2)
        self.tyre_speed_selector.addItem("4x", 4)
        self.tyre_speed_selector.addItem("8x", 8)
        self.tyre_speed_selector.setFixedWidth(int(70 * self.scale_factor))
        self.tyre_speed_selector.setStyleSheet("""
            QComboBox {
                font-size: {int(14 * self.scale_factor)}px;
                color: black;
                padding: 3px;
            }
        """)

        self.tyre_playback_time_label = QLabel("0.000s / 0.000s")
        self.tyre_playback_time_label.setStyleSheet(f"font-size: 14px; color: black; font-weight: bold;")


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
        from matplotlib.patches import Rectangle
        
        if not hasattr(self, 'tyre_top_down_ax'):
            return
        
        ax = self.tyre_top_down_ax
        
        while len(ax.patches) > 1:  
            ax.patches[-1].remove()
        
        for text in list(ax.texts):
            text.remove()
        
        tyres = {
            'LF': {
                'L': current_row['LFtempL'], 
                'M': current_row['LFtempM'], 
                'R': current_row['LFtempR'],
            },
            'RF': {
                'L': current_row['RFtempL'], 
                'M': current_row['RFtempM'], 
                'R': current_row['RFtempR'],
            },
            'LR': {
                'L': current_row['LRtempL'], 
                'M': current_row['LRtempM'], 
                'R': current_row['LRtempR'],
            },
            'RR': {
                'L': current_row['RRtempL'], 
                'M': current_row['RRtempM'], 
                'R': current_row['RRtempR'],
            },
        }

        #reminder: ensure that tyre sizes and positioning align with non update method above
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
            ax.text(x + tyre_width/2, y + tyre_height + 0.3, label, 
                ha='center', va='bottom', fontsize=14, fontweight='bold', color='#000000')

            
            for i, (segment_label, temp) in enumerate([('L', temps['L']), ('M', temps['M']), ('R', temps['R'])]):
                color = self.get_tyre_temp_color(temp)
                segment = Rectangle((x + i * segment_width, y), segment_width, tyre_height, 
                                facecolor=color, edgecolor='#000000', linewidth=1.5)
                ax.add_patch(segment)
                
                text_x = x + i * segment_width + segment_width/2
                text_y = y + tyre_height/2
                ax.text(text_x, text_y, f'{temp:.0f}°', 
                    ha='center', va='center', fontsize=10, fontweight='bold', color='white')

        
        self.tyre_top_down_canvas.draw_idle()
#TODO: for tyre page, add overall data such as highest recorded temp for each tyre, per lap highest temp, highest averages etc etc 
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    #================
    # Pedal Data Page
    #================
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
        title.setStyleSheet("""
            font-size: 38px;
            font-weight: bold;
            color: #000007;
        """)
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        main_row = QHBoxLayout()
        main_row.setSpacing(int(15 * self.scale_factor))

        lap_selector_container = QWidget()
        lap_selector_container.setFixedWidth(int(280 * self.scale_factor))
        lap_selector_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 0px;
                border: none;
            }
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
            QComboBox {
                font-size: 16px;
                color: black;
                background-color: white;
                padding: 5px;
                border: 1px solid #d1d5db; 
                border-radius: 4px;
            }
            QComboBox QAbstractItemView {
                color: black;
                background-color: white;
                selection-background-color: #2563eb;
                selection-color: white;
            }
        """)
        self.lap_order_selector.currentIndexChanged.connect(self.update_lap_list)

        order_layout.addWidget(order_label)
        order_layout.addWidget(self.lap_order_selector)
        lap_selector_layout.addLayout(order_layout)

        self.lap_list = QListWidget()
        self.lap_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                font-size: 18px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f3f4f6;
                color: #000000;
            }
            QListWidget::item:selected {
                background-color: #2563eb;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #eff6ff;
                color: #000000;
            }
        """)
        self.lap_list.itemClicked.connect(self.update_pedal_track_map_from_list)
        lap_selector_layout.addWidget(self.lap_list)

        lap_selector_wrapper = QWidget()
        lap_selector_wrapper.setFixedWidth(int(284 * self.scale_factor))
        lap_selector_wrapper.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #000000;
                border-radius: 8px;
            }
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
            QPushButton {
                background-color: #e5e7eb;
                color: #6b7280;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #2563eb;
                color: white;
                border: 1px solid #2563eb;
            }
            QPushButton:hover {
                background-color: #d1d5db;
            }
            QPushButton:checked:hover {
                background-color: #1d4ed8;
            }
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
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
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
            QPushButton {
                background-color: #e5e7eb;
                color: #6b7280;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #2563eb;
                color: white;
                border: 1px solid #2563eb;
            }
            QPushButton:hover {
                background-color: #d1d5db;
            }
            QPushButton:checked:hover {
                background-color: #1d4ed8;
            }
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
            QPushButton {
                background-color: #2563eb;
                color: white;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.play_pause_btn.clicked.connect(self.toggle_playback)

        self.reset_btn = QPushButton("↺ Reset")
        self.reset_btn.setFixedWidth(int(100 * self.scale_factor))
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
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
        self.speed_selector.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                color: black;
                padding: 3px;
            }
        """)

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
                lap_time_str = f"{minutes:02}:{seconds:02}.{millis:03}"
                
                self.lap_data_dict[int(lap)] = {
                    'time': lap_time,
                    'time_str': lap_time_str
                }
            else:
                self.lap_data_dict[int(lap)] = {
                    'time': float('inf'),
                    'time_str': 'N/A'
                }

        # remove the last lap (incomplete cooldown lap) from display
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
            sorted_laps = sorted(self.lap_data_dict.keys(),
                                key=lambda x: self.lap_data_dict[x]['time'])
        else:
            sorted_laps = sorted(self.lap_data_dict.keys(),
                                key=lambda x: self.lap_data_dict[x]['time'],
                                reverse=True)

        for lap in sorted_laps:
            lap_info = self.lap_data_dict[lap]
            item_text = f"Lap {lap} - {lap_info['time_str']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, lap)
            self.lap_list.addItem(item)

            
    def update_pedal_track_map_from_list(self):
        current_item = self.lap_list.currentItem()
        if current_item:
            selected_lap = current_item.data(Qt.UserRole)
            self.reset_playback()
            self.update_pedal_track_map(selected_lap)

    def update_pedal_track_map(self, selected_lap):
        from matplotlib.figure import Figure
        import numpy as np
        from matplotlib.collections import LineCollection

        # Stop 
        self.playback_timer.stop()
        self.playback_active = False
        self.play_pause_btn.setText("▶ Play")

        # Clear map
        while self.pedal_map_layout.count():
            child = self.pedal_map_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Clear pedal graph
        while self.pedal_graph_layout.count():
            child = self.pedal_graph_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Clear gear graph
        while self.gear_graph_layout.count():
            child = self.gear_graph_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if selected_lap is None:
            return

        venue = self.session_info.get("Venue", "Unknown Venue")

        lap_data = self.telemetry_df[
            (self.telemetry_df["Lap"] == selected_lap)
        ].copy()

        if len(lap_data) == 0:
            error_label = QLabel("No data available for this lap")
            error_label.setAlignment(Qt.AlignCenter)
            self.pedal_map_layout.addWidget(error_label)
            return

        lap_data = lap_data.sort_values("SessionTick").reset_index(drop=True)

        print(f"\n=== Lap {selected_lap} Data Analysis ===")
        print(f"Total rows: {len(lap_data)}")
        print(f"SessionTick range: {lap_data['SessionTick'].min()} to {lap_data['SessionTick'].max()}")
        tick_diff = lap_data["SessionTick"].diff()
        large_gaps = tick_diff[tick_diff > 10]
        if len(large_gaps) > 0:
            print(f"Found {len(large_gaps)} large gaps in SessionTick:")
            for idx, gap in large_gaps.items():
                print(f"  Row {idx}: gap of {gap} ticks")
        print(f"IsOnTrackCar values: {lap_data['IsOnTrackCar'].value_counts().to_dict()}")

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
            # Throttle/Brake colouring
            for i in range(len(throttle) - 1):
                if throttle[i] < COAST_THRESHOLD and brake[i] < COAST_THRESHOLD:
                    # Coasting - yellow
                    colors.append('#ffcd03')  
                elif throttle[i] > brake[i]:
                     # Throttle - green
                    colors.append('#079902') 
                else:
                    # Brake - red
                    colors.append('#ff0318')  
        else:
            # Gear colouring
            gear_color_map = {
                -1: '#002aff',
                0: '#00aaff', 
                1: '#00ff91', 
                2: '#48a82a', 
                3: '#d8f51d', 
                4: '#faac0f',  
                5: '#fa750f',  
                6: '#fa0f0f',  
                7: '#aa44ff',  
                8: '#f308ff',  
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

        self.driver_dot, = ax_map.plot(
            lap_data["Lon"].iloc[0],
            lap_data["Lat"].iloc[0],
            'o', color='black', markersize=10, zorder=20
        )

        def capitalize_venue(v):
            return " ".join(
                "GP" if w.lower() == "gp" else w.capitalize()
                for w in v.split()
            )

        if self.map_mode_throttle.isChecked():
            map_title = f"Lap {selected_lap} - Throttle/Brake Usage"
        else:
            map_title = f"Lap {selected_lap} - Gear Usage"

        ax_map.set_title(map_title, fontsize=14, fontweight='bold', pad=10, loc='left')
        ax_map.text(0.98, 0.98, f"Lap Time: {lap_time_str}",
                    transform=ax_map.transAxes, fontsize=12,
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

        # ===== MAP LEGEND =====
        legend_widget = QWidget()
        legend_widget.setFixedWidth(int(150 * self.scale_factor))
        legend_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
        """)
        legend_layout = QVBoxLayout(legend_widget)
        legend_layout.setContentsMargins(10, 10, 10, 10)
        legend_layout.setSpacing(5)

        legend_title = QLabel("Legend")
        legend_title.setStyleSheet("font-size: 13px; color: #111827; font-weight: bold;")
        legend_layout.addWidget(legend_title)

        if self.map_mode_throttle.isChecked():
            # Throttle/Brake legend
            legend_items = [
                ("#079902", "Throttle"),
                ("#ff0318", "Brake"),
                ("#ffcd03", "Coasting"),
            ]
        else:
            # Gear legend
            gear_color_map = {
                -1: '#002aff',
                0: '#00aaff', 
                1: '#00ff91', 
                2: '#48a82a', 
                3: '#d8f51d', 
                4: '#faac0f',  
                5: '#fa750f',  
                6: '#fa0f0f',  
                7: '#aa44ff',  
                8: '#f308ff',  
            }
            min_gear = int(lap_data["Gear"].min())
            max_gear = int(lap_data["Gear"].max())
            gear_range = range(min_gear if min_gear < 0 else 0, max_gear + 1)
            
            legend_items = []
            for g in gear_range:
                gear_label = 'R' if g == -1 else 'N' if g == 0 else f"Gear {g}"
                legend_items.append((gear_color_map.get(g, '#ffffff'), gear_label))

        # Create legend items
        for color, label in legend_items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(8)
            
            # Color box
            color_box = QLabel()
            color_box.setFixedSize(20, 20)
            color_box.setStyleSheet(f"""
                background-color: {color};
                border: 1px solid #d1d5db;
                border-radius: 3px;
            """)
            
            # Label
            text_label = QLabel(label)
            text_label.setStyleSheet("font-size: 11px; color: #111827;")
            
            item_layout.addWidget(color_box)
            item_layout.addWidget(text_label)
            item_layout.addStretch()
            
            legend_layout.addLayout(item_layout)

        legend_layout.addStretch()

        # Clear legend placeholder
        while self.legend_placeholder_layout.count():
            child = self.legend_placeholder_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add the legend widget to the placeholder
        self.legend_placeholder_layout.addWidget(legend_widget, alignment=Qt.AlignTop)
      

        # Add the container to the pedal_map_layout
        self.pedal_map_layout.addWidget(self.map_canvas)


        # ===== PEDAL GRAPH =====
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
            self.pedal_ax.axhline(
                y=y_val, color='#adadad', linewidth=1,
                linestyle='--', alpha=0.3, zorder=1
            )
            
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#079902', label='Throttle'),
            Patch(facecolor='#ff0318', label='Brake'),
        ]
        self.pedal_ax.legend(
            handles=legend_elements, loc='upper left',
            bbox_to_anchor=(0, -.20), ncol=2,                      
            facecolor='#bfbec1', labelcolor='black',
            fontsize=9, framealpha=1, edgecolor='#444444'
        )

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

        # ===== GEAR GRAPH =====
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
            self.gear_ax.axhline(
                y=g, color='#adadad', linewidth=1,
                linestyle='--', alpha=0.3, zorder=1
            )

        self.gear_line, = self.gear_ax.plot([], [], color='#05f7ef', linewidth=1)

        fig_gear.subplots_adjust(left=0.065, right=0.98, top=0.90, bottom=0.19)

        self.gear_canvas = FigureCanvas(fig_gear)
        self.gear_canvas.setFixedSize(int(1100* self.scale_factor), int(300 * self.scale_factor))
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
        
        # Advance current tick
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
            speed_display = current_speed_ms * 3.6
            self.speed_value_label.setText(f"{speed_display:.0f}")
        else:
            speed_display = current_speed_ms * 2.23694
            self.speed_value_label.setText(f"{speed_display:.0f}")

        last_plotted_index = getattr(self, '_last_plotted_index', 0)

    
        if self.playback_index > last_plotted_index:
   
            for idx in range(last_plotted_index + 1, self.playback_index + 1):
                if idx < len(self.current_lap_data):
                    row = self.current_lap_data.iloc[idx]

                    row_tick = row["SessionTick"] - lap_start_tick
                    row_time = row_tick / ticks_per_second
                    
    
                    if len(self.playback_time_data) == 0 or row_time > self.playback_time_data[-1]:
                        self.playback_time_data.append(row_time)
                        self.playback_throttle_data.append(float(row["Throttle"]))
                        self.playback_brake_data.append(float(row["Brake"]))
                        self.playback_gear_data.append(float(row["Gear"]))
                    
                    # removing outlier issues due to iRacing sometimes struggling to record sharp changes 
                    if len(self.playback_time_data) == 0 or row_time > self.playback_time_data[-1]:
                        throttle_val = float(row["Throttle"])
                        brake_val = float(row["Brake"])
                        
                        # Spike filter: if braking >20% and throttle spike detected, filter it out
                        if len(self.playback_throttle_data) > 0:
                            last_throttle = self.playback_throttle_data[-1]
                            
                            # If braking and sudden throttle spike (>30% jump), cap it
                            if brake_val > 20 and throttle_val > last_throttle + 30:
                                throttle_val = last_throttle  # Keep previous value instead
                        
                        self.playback_time_data.append(row_time)
                        self.playback_throttle_data.append(throttle_val)
                        self.playback_brake_data.append(brake_val)
                        self.playback_gear_data.append(float(row["Gear"]))

        elif self.playback_index == last_plotted_index:
            pass

     
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

        # Spike removel, data cleaning to remove anomalies and abnormalities which can be present in iracing data
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

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------      
    #================
    # Brake Analysis Page
    #================

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
        title.setStyleSheet("""
            font-size: 45px;
            font-weight: bold;
            color: #000007;
        """)
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        
        wheel_filter_container = QWidget()
        wheel_filter_layout = QHBoxLayout(wheel_filter_container)
        wheel_filter_layout.setContentsMargins(0, 0, 0, 0)
        wheel_filter_layout.setSpacing(10)

        filter_label = QLabel("Show Wheels:")
        filter_label.setStyleSheet(f"font-size: 15px;")
        wheel_filter_layout.addWidget(filter_label)

        self.lockup_wheel_toggles = {}
        wheel_names = ['LF', 'RF', 'LR', 'RR']
        
        for wheel_name in wheel_names:
            btn = QPushButton(wheel_name)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedSize(int(50 * self.scale_factor), int(30 * self.scale_factor))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e5e7eb;
                    color: #6b7280;
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #2563eb;
                    color: white;
                    border: 1px solid #2563eb;
                }
                QPushButton:hover {
                    background-color: #d1d5db;
                }
                QPushButton:checked:hover {
                    background-color: #1d4ed8;
                }
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
            QWidget {
                background-color: white;
                border-radius: 0px;
                border: none;
            }
        """)
        lap_selector_layout = QVBoxLayout(lap_selector_container)
        lap_selector_layout.setContentsMargins(10, 10, 10, 10)
        lap_selector_layout.setSpacing(10)

        selector_title = QLabel("Select Laps")
        selector_title.setStyleSheet(f"font-size: 17px;")
        lap_selector_layout.addWidget(selector_title)

      
        self.lockup_all_laps_cb = QCheckBox("All Laps")
        self.lockup_all_laps_cb.setChecked(True)
        self.lockup_all_laps_cb.setStyleSheet("""
            QCheckBox {
                font-size: 18px;
                color: #111827;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: {int(18 * self.scale_factor)}px;
                height: {int(18 * self.scale_factor)}px;
                border: 2px solid #9ca3af;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #2563eb;
                border-color: #2563eb;
            }
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
            QWidget#lap_wrapper {
                background-color: white;
                border: 2px solid #000000;
                border-radius: 8px;
            }
        """)
        lap_selector_wrapper.setObjectName("lap_wrapper")
        lap_selector_wrapper_layout = QVBoxLayout(lap_selector_wrapper)
        lap_selector_wrapper_layout.setContentsMargins(2, 2, 2, 2)  
        lap_selector_wrapper_layout.addWidget(lap_selector_container)

        # Add wrapper instead of container
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

    def detect_all_lockups(self):
        #current definition of lockup for lockup detection
        MIN_WHEEL_SPEED = 2  # m/s
        MIN_GPS_SPEED = 10   # m/s
        GAP_THRESHOLD = 5    # ticks
        
        self.all_lockups = {'LF': [], 'RF': [], 'LR': [], 'RR': []}
        
        for _, row in self.telemetry_df.iterrows():
            lap_num = row['Lap']
            if lap_num <= 0:
                continue
            
            speed = row['Speed']
            if speed < MIN_GPS_SPEED:
                continue
            
            idx = row.name
            
            wheels = {
                'LF': row['LFspeed'],
                'RF': row['RFspeed'],
                'LR': row['LRspeed'],
                'RR': row['RRspeed']
            }
            
            temp_cols_surface = {
                'LF': ['LFtempCL', 'LFtempCM', 'LFtempCR'],
                'RF': ['RFtempCL', 'RFtempCM', 'RFtempCR'],
                'LR': ['LRtempCL', 'LRtempCM', 'LRtempCR'],
                'RR': ['RRtempCL', 'RRtempCM', 'RRtempCR']
            }
            
            for wheel_name, wheel_speed in wheels.items():
                if wheel_speed < MIN_WHEEL_SPEED:
                    start_idx = max(0, idx - 5)
                    end_idx = min(len(self.telemetry_df), idx + 5)
                    window = self.telemetry_df.iloc[start_idx:end_idx]
                    
                    temp_cols_surface = {
                        'LF': ['LFtempL', 'LFtempM', 'LFtempR'], 
                        'RF': ['RFtempL', 'RFtempM', 'RFtempR'],
                        'LR': ['LRtempL', 'LRtempM', 'LRtempR'],
                        'RR': ['RRtempL', 'RRtempM', 'RRtempR']
                    }
                    
                    for wheel_name, wheel_speed in wheels.items():
                        if wheel_speed < MIN_WHEEL_SPEED:
                            start_idx = max(0, idx - 5)
                            end_idx = min(len(self.telemetry_df), idx + 5)
                            window = self.telemetry_df.iloc[start_idx:end_idx]
                            
                            max_temp = window[temp_cols_surface[wheel_name]].max().max()
                            
                            lockup_data = {
                                'idx': idx,
                                'lap': int(lap_num),
                                'wheel': wheel_name,
                                'lon': row['Lon'],
                                'lat': row['Lat'],
                                'speed': speed * 3.6,
                                'brake': row['Brake'],
                                'max_temp': max_temp
                            }
                            self.all_lockups[wheel_name].append(lockup_data)
        
        for wheel_name in self.all_lockups:
            if not self.all_lockups[wheel_name]:
                continue
            
            grouped = []
            current_group = [self.all_lockups[wheel_name][0]]
            
            for i in range(1, len(self.all_lockups[wheel_name])):
                if self.all_lockups[wheel_name][i]['idx'] - current_group[-1]['idx'] <= GAP_THRESHOLD:
                    current_group.append(self.all_lockups[wheel_name][i])
                else:
                    first_tick = self.telemetry_df.iloc[current_group[0]['idx']]['SessionTick']
                    last_tick = self.telemetry_df.iloc[current_group[-1]['idx']]['SessionTick']
                    duration = (last_tick - first_tick) / 60 
                    
                    mid_idx = len(current_group) // 2
                    middle_event = current_group[mid_idx].copy()
                    middle_event['duration'] = duration
                    grouped.append(middle_event)
                    
                    current_group = [self.all_lockups[wheel_name][i]]
            
            if current_group:
                first_tick = self.telemetry_df.iloc[current_group[0]['idx']]['SessionTick']
                last_tick = self.telemetry_df.iloc[current_group[-1]['idx']]['SessionTick']
                duration = (last_tick - first_tick) / 60
                
                mid_idx = len(current_group) // 2
                middle_event = current_group[mid_idx].copy()
                middle_event['duration'] = duration
                grouped.append(middle_event)
            
            self.all_lockups[wheel_name] = grouped
    
    # table to display lockup info such as lap of occurance, max temp recorded, tyre(s) locked, and duration(seconds) of lockp
    def create_lockup_table(self):
        all_events = []
        for wheel_name, lockups in self.all_lockups.items():
            for lockup in lockups:
                all_events.append(lockup)
        
        all_events.sort(key=lambda x: x['lap'])
        
        from collections import defaultdict
        lap_groups = defaultdict(list)
        for event in all_events:
            lap_groups[event['lap']].append(event)
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['Lap', 'Tyres', 'Max Temp (°C)', 'Brake (%)', 'Length (s)'])
        table.setRowCount(len(lap_groups))
        
        table.verticalHeader().setDefaultSectionSize(int(35 * self.scale_factor))

        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #9ca3af;
                font-size: 19px;
                border: none;
                border-radius: 0px;
                outline: none;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                color: #111827;
                font-weight: bold;
                font-size: {int(22 * self.scale_factor)}px;
                border: none;
                border-right: 1px solid #9ca3af;
                border-bottom: 2px solid #9ca3af;
                border-left: 1px solid #9ca3af;           
                padding: {int(15 * self.scale_factor)}px;
            }
            QHeaderView::section:first {
                border-left: 1px solid #d1d5db;
            }
            QTableWidget::item {
                padding: {int(19 * self.scale_factor)}px;
                border-bottom: 1px solid #9ca3af;
                border-right: 1px solid #9ca3af;
                border-left: 1px solid #9ca3af;
                color: #000000;
                outline: none;
            }
            QTableWidget::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            QTableWidget::item:focus {
                outline: none; 
            }
        """)
        
        row = 0
        for lap_num in sorted(lap_groups.keys()):
            events = lap_groups[lap_num]
            
            #lap #
            lap_item = QTableWidgetItem(str(lap_num))
            lap_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            table.setItem(row, 0, lap_item)
            
            #tyre 
            tyres = ', '.join(sorted(set(e['wheel'] for e in events)))
            tyre_item = QTableWidgetItem(tyres)
            tyre_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            table.setItem(row, 1, tyre_item)
            
            #max temp *C
            max_temp = max(e['max_temp'] for e in events)
            temp_item = QTableWidgetItem(f"{max_temp:.1f}")
            temp_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            table.setItem(row, 2, temp_item)
            
            # brake pressure (% raw input)
            avg_brake = sum(e['brake'] for e in events) / len(events)
            brake_item = QTableWidgetItem(f"{avg_brake:.1f}")
            brake_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            table.setItem(row, 3, brake_item)
            
            # duration s
            max_duration = max(e['duration'] for e in events)
            duration_item = QTableWidgetItem(f"{max_duration:.3f}")
            duration_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            table.setItem(row, 4, duration_item)
            
            row += 1
        

        table.setMaximumWidth(int(715 * self.scale_factor))
        table.setMinimumWidth(int(715 * self.scale_factor)) 
        table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        table_container = QWidget()
        table_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #000000;
                border-radius: 8px;
            }
        """)
        table_container_layout = QVBoxLayout(table_container)
        table_container_layout.setContentsMargins(int(10 * self.scale_factor), int(10 * self.scale_factor), int(10 * self.scale_factor), int(10 * self.scale_factor))
        table_container_layout.addWidget(table)

        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnWidth(0, int(80 * self.scale_factor))
        table.setColumnWidth(1, int(150 * self.scale_factor))
        table.setColumnWidth(2, int(160 * self.scale_factor))
        table.setColumnWidth(3, int(110 * self.scale_factor))
        table.setColumnWidth(4, int(120 * self.scale_factor))
        
        table.setSortingEnabled(True)


        for row_idx in range(table.rowCount()):
            lap_item = table.item(row_idx, 0)
            lap_item.setData(Qt.UserRole, int(lap_item.text()))
            temp_item = table.item(row_idx, 2)
            temp_item.setData(Qt.UserRole, float(temp_item.text()))
            
            brake_item = table.item(row_idx, 3)
            brake_item.setData(Qt.UserRole, float(brake_item.text()))

            duration_item = table.item(row_idx, 4)
            duration_item.setData(Qt.UserRole, float(duration_item.text()))

        table.verticalHeader().setVisible(False)

        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.lockup_lap_groups = lap_groups

        table.itemSelectionChanged.connect(lambda: self.highlight_selected_lockup(table))

        self.lockup_table_widget = table 

        return table_container
    

    def highlight_selected_lockup(self, table):

        selected_rows = table.selectionModel().selectedRows()
        
        if not selected_rows or not hasattr(self, 'lockup_scatter'):
            return
        
        # Get selected lap
        selected_row = selected_rows[0].row()
        sorted_laps = sorted(self.lockup_lap_groups.keys())
        selected_lap = sorted_laps[selected_row]
        
        # Separate lockups into highlighted and non-highlighted
        highlight_lons = []
        highlight_lats = []
        normal_lons = []
        normal_lats = []
        
        for lockup in self.lockup_metadata:
            if lockup['lap'] == selected_lap:
                highlight_lons.append(lockup['lon'])
                highlight_lats.append(lockup['lat'])
            else:
                normal_lons.append(lockup['lon'])
                normal_lats.append(lockup['lat'])
        
        self.lockup_scatter.remove()
        if hasattr(self, 'lockup_scatter_normal'):
            self.lockup_scatter_normal.remove()
        
        
        if normal_lons:
            self.lockup_scatter_normal = self.lockup_map_ax.scatter(normal_lons, normal_lats,
                                    color='#ef4444',
                                    s=150,
                                    alpha=0.6,
                                    zorder=5,
                                    picker=True,
                                    pickradius=15)
        
        if highlight_lons:
            self.lockup_scatter = self.lockup_map_ax.scatter(highlight_lons, highlight_lats,
                                                            color='#3b82f6',
                                                            s=150,
                                                            alpha=0.9,
                                                            zorder=10,
                                                            picker=True,
                                                            pickradius=15)
        
        self.lockup_map_canvas.draw_idle()
        
    def populate_lockup_lap_selector(self):
    
        while self.lockup_lap_cb_layout.count():
            child = self.lockup_lap_cb_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.lockup_lap_checkboxes = {}
        
     
        for lap in sorted(self.lap_timings.keys()):

            has_lockup = any(
                any(l['lap'] == lap for l in lockups) 
                for lockups in self.all_lockups.values()
            )
            
       
            cb_text = f"Lap {lap}"
            if has_lockup:
                cb_text += " ⚠️"  
            
            cb = QCheckBox(cb_text)
            cb.setChecked(True)
            cb.setStyleSheet("""
                QCheckBox {
                    font-size: 17px; 
                    font-weight: bold;
                    color: #374151;
                }
                QCheckBox::indicator {
                    width: {int(18 * self.scale_factor)}px;
                    height: {int(18 * self.scale_factor)}px;
                    border: 2px solid #9ca3af;
                    border-radius: 3px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #2563eb;
                    border-color: #2563eb;
                    image: url(none);
                }
                QCheckBox::indicator:checked:after {
                    content: "✓";
                    color: white;
                }
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
        
        while self.lockup_map_layout.count():
            child = self.lockup_map_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        while self.lockup_stats_layout.count():
            child = self.lockup_stats_layout.takeAt(0)
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
        
        ax.plot(lap_data["Lon"], lap_data["Lat"], 
            linewidth=8, color='#d1d5db', zorder=1, alpha=0.8)

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
        
        all_lons = []
        all_lats = []
        self.lockup_metadata = []  
        
        for wheel_name in selected_wheels:
            lockups = self.all_lockups[wheel_name]
            wheel_lockups = [l for l in lockups if l['lap'] in selected_laps]
            
            if wheel_lockups:
                all_lons.extend([l['lon'] for l in wheel_lockups])
                all_lats.extend([l['lat'] for l in wheel_lockups])
                self.lockup_metadata.extend(wheel_lockups)  
        
        if all_lons:
            print(f"\n=== PLOTTING {len(all_lons)} LOCKUPS ===")
            for i in range(min(5, len(all_lons))): 
                print(f"Plot point {i}: lon={all_lons[i]:.6f}, lat={all_lats[i]:.6f}")
            
            print(f"\n=== METADATA {len(self.lockup_metadata)} LOCKUPS ===")
            for i in range(min(5, len(self.lockup_metadata))):  
                print(f"Metadata {i}: lon={self.lockup_metadata[i]['lon']:.6f}, lat={self.lockup_metadata[i]['lat']:.6f}")
            
            self.lockup_scatter = ax.scatter(all_lons, all_lats, 
                    color='#ef4444', 
                    s=150,
                    alpha=0.6,
                    zorder=5,
                    label='Lockups',
                    picker=True,
                    pickradius=15)
            ax.legend(loc='upper right', fontsize=11, framealpha=0.9)
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

        class ClickableLockupCanvas(ZoomableCanvas):
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
                
                for lockup in self.parent_window.lockup_metadata:
                    if abs(lockup['lon'] - clicked_lon) < 0.000001 and abs(lockup['lat'] - clicked_lat) < 0.000001:
                        clicked_lap = lockup['lap']
                        self.parent_window.select_table_row_by_lap(clicked_lap)
                        break

        self.lockup_map_canvas = ClickableLockupCanvas(fig, self)
        self.lockup_map_canvas.setFixedSize(int(880 * self.scale_factor), int(870 * self.scale_factor))

        return self.lockup_map_canvas
    
    def select_table_row_by_lap(self, lap_num):
        if not hasattr(self, 'lockup_table_widget'):
            return

        sorted_laps = sorted(self.lockup_lap_groups.keys())
        try:
            row_index = sorted_laps.index(lap_num)
            self.lockup_table_widget.selectRow(row_index)
        except (ValueError, AttributeError):
            pass

    def get_selected_lockup_wheels(self):
        if not hasattr(self, 'lockup_wheel_toggles'):
            return ['LF', 'RF', 'LR', 'RR']  
        
        selected = []
        for wheel_name, toggle in self.lockup_wheel_toggles.items():
            if toggle.isChecked():
                selected.append(wheel_name)
        
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
            QWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
        """)
        
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(20, 10, 20, 10)
        stats_layout.setSpacing(30)

        total_widget = self.create_stat_box("Total Lockups", f"{total_lockups}")
        stats_layout.addWidget(total_widget)

        avg_widget = self.create_stat_box("Avg per Lap", f"{avg_per_lap:.1f}")
        stats_layout.addWidget(avg_widget)

        for wheel_name, count in wheel_counts.items():
            wheel_widget = self.create_stat_box(f"{wheel_name} Lockups", f"{count}")
            stats_layout.addWidget(wheel_widget)
        
        stats_layout.addStretch()
        
        stats_wrapper = QWidget()
        stats_wrapper.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 3px solid #000000;
                border-radius: 8px;
            }
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



# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------      

    #================
    # Fuel Data Page
    #================
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
        title.setStyleSheet("""
            font-size: 38px;
            font-weight: bold;
            color: #000007;
        """)
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
            QPushButton {
                background-color: #e5e7eb;
                color: #6b7280;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #2563eb;
                color: white;
                border: 1px solid #2563eb;
            }
            QPushButton:hover {
                background-color: #d1d5db;
            }
            QPushButton:checked:hover {
                background-color: #1d4ed8;
            }
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
                start_fuel = lap_data['FuelLevel'].iloc[0]
                end_fuel = lap_data['FuelLevel'].iloc[-1]
                usage = start_fuel - end_fuel
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

        FUEL_DENSITY = 0.75
        initial_fuel_kg = initial_fuel_l * FUEL_DENSITY
        total_used_kg = total_used_l * FUEL_DENSITY
        avg_per_lap_kg = avg_per_lap_l * FUEL_DENSITY
        most_used_kg = most_used_l * FUEL_DENSITY
        least_used_kg = least_used_l * FUEL_DENSITY
        
        stats_container = QWidget()
        stats_container.setFixedHeight(int(120 * self.scale_factor))
        stats_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
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
            QWidget {
                background-color: white;
                border: 2px solid #000000;
                border-radius: 8px;
            }
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
        while self.fuel_chart_container_layout.count():
            child = self.fuel_chart_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        while self.fuel_correlation_layout.count():
            child = self.fuel_correlation_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        while self.fuel_track_layout.count():
            child = self.fuel_track_layout.takeAt(0)
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
        from matplotlib.figure import Figure
        import numpy as np
        
        fig = Figure(figsize=(10, 5), facecolor='#f8f9fa')
        ax = fig.add_subplot(111)
        
        all_laps = sorted(self.lap_timings.keys())
        lap_distances = []
        fuel_levels = []
        
        for lap in all_laps:
            lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap].copy()
            if len(lap_data) == 0:
                continue
            
            lap_data = lap_data.sort_values("LapDistPct")
            
            for _, row in lap_data.iterrows():
                lap_distance = lap + (row["LapDistPct"] / 100)
                lap_distances.append(lap_distance)
                fuel_levels.append(row["FuelLevel"])
        
        if len(lap_distances) == 0:
            return None
        
        ax.plot(lap_distances, fuel_levels, linewidth=2, color='#2563eb')
        ax.fill_between(lap_distances, 0, fuel_levels, alpha=0.2, color='#2563eb')
        
        all_laps = sorted(self.lap_timings.keys())
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
        
        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(int(600 * self.scale_factor))

        line_chart_wrapper = QWidget()
        line_chart_wrapper.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #000000;
                border-radius: 8px;
            }
        """)
        line_chart_wrapper_layout = QVBoxLayout(line_chart_wrapper)
        line_chart_wrapper_layout.setContentsMargins(3, 3, 3, 3)
        line_chart_wrapper_layout.addWidget(canvas)

        return line_chart_wrapper

    def create_fuel_usage_bar_chart(self):
        from matplotlib.figure import Figure
        import numpy as np

        lap_usage = {}
        for lap in sorted(self.lap_timings.keys()):
            lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap]
            if len(lap_data) > 0:
                start_fuel = lap_data['FuelLevel'].iloc[0]
                end_fuel = lap_data['FuelLevel'].iloc[-1]
                usage = start_fuel - end_fuel
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
                color = self.interpolate_color('#22c55e', '#eab308', ratio * 2)
            else:
                color = self.interpolate_color('#eab308', '#ef4444', (ratio - 0.5) * 2)
            
            colors.append(color)
        
        self.fuel_bar_colors = colors.copy() 
        
        bars = ax.bar(laps, usages, color=colors, edgecolor='#000000', linewidth=1)
        self.fuel_bars = bars
        
        if self.selected_fuel_lap and self.selected_fuel_lap in laps:
            idx = laps.index(self.selected_fuel_lap)
            bars[idx].set_color('#2563eb')

        y_margin = (max_usage - min_usage) * 0.1
        ax.set_ylim(min_usage - y_margin, max_usage + y_margin)
        
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
        
        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(int(600 * self.scale_factor))
        
        canvas.mpl_connect('motion_notify_event', self.on_fuel_bar_hover)
        canvas.mpl_connect('button_press_event', self.on_fuel_bar_click)

        self.fuel_bar_canvas = canvas

        bar_chart_wrapper = QWidget()
        bar_chart_wrapper.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #000000;
                border-radius: 8px;
            }
        """)
        bar_chart_wrapper_layout = QVBoxLayout(bar_chart_wrapper)
        bar_chart_wrapper_layout.setContentsMargins(3, 3, 3, 3)
        bar_chart_wrapper_layout.addWidget(canvas)

        return bar_chart_wrapper 
    
    #on hover of bar lighten colour
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
                    brightened = self.brighten_color(self.fuel_bar_colors[i], 1.3)
                    bar.set_color(brightened)
                break
        
        self.fuel_bar_canvas.draw_idle()

    #update track map on lap click selection
    def on_fuel_bar_click(self, event):
        if not hasattr(self, 'fuel_bars') or event.inaxes != self.fuel_bar_ax:
            return
        
        for i, bar in enumerate(self.fuel_bars):
            if bar.contains(event)[0]:
                self.selected_fuel_lap = self.fuel_bar_laps[i]
                
                for j, b in enumerate(self.fuel_bars):
                    if j == i:
                        b.set_color('#2563eb')
                    else:
                        b.set_color(self.fuel_bar_colors[j])
                
                self.fuel_bar_canvas.draw_idle()
                
                while self.fuel_track_layout.count():
                    child = self.fuel_track_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                
                track_map = self.create_fuel_track_map(self.selected_fuel_lap)
                if track_map:
                    self.fuel_track_layout.addWidget(track_map)
                
                break

    def brighten_color(self, hex_color, factor):
        rgb = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
        rgb = [min(255, int(c * factor)) for c in rgb]
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

    def create_fuel_laptime_correlation(self):
        from matplotlib.figure import Figure
        import numpy as np

        lap_numbers = []
        lap_times = []
        fuel_loads = []
        
        for lap in sorted(self.lap_timings.keys()):
            lap_data = self.telemetry_df[self.telemetry_df["Lap"] == lap]
            if len(lap_data) == 0:
                continue
            
            avg_fuel = lap_data['FuelLevel'].mean()
            lap_time = self.lap_timings[lap]['time']
            
            if lap_time != float('inf'):
                lap_numbers.append(lap)
                lap_times.append(lap_time)
                fuel_loads.append(avg_fuel)
        
        if len(lap_times) == 0:
            return None
        
        fig = Figure(figsize=(10, 5), facecolor='#f8f9fa')
        ax = fig.add_subplot(111)
        
        scatter = ax.scatter(fuel_loads, lap_times, s=100, c=lap_numbers, 
                            cmap='viridis', edgecolors='black', linewidths=1.5, zorder=3)

        for lap_num, fuel, time in zip(lap_numbers, fuel_loads, lap_times):
            ax.annotate(f'{lap_num}', (fuel, time), 
                    fontsize=9, fontweight='bold', ha='center', va='center')
        
        if len(fuel_loads) > 1:
            z = np.polyfit(fuel_loads, lap_times, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(min(fuel_loads), max(fuel_loads), 100)
            ax.plot(x_trend, p(x_trend), '--', color='#ef4444', linewidth=2, 
                alpha=0.7, label='Trend', zorder=2)
            
            correlation = np.corrcoef(fuel_loads, lap_times)[0, 1]
            ax.text(0.98, 0.98, f'Correlation: {correlation:.3f}',
                transform=ax.transAxes, ha='right', va='top',
                fontsize=11, fontweight='bold',
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
        
        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(int(450 * self.scale_factor))

        # Wrap in border
        correlation_wrapper = QWidget()
        correlation_wrapper.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #000000;
                border-radius: 8px;
            }
        """)
        correlation_wrapper_layout = QVBoxLayout(correlation_wrapper)
        correlation_wrapper_layout.setContentsMargins(3, 3, 3, 3)
        correlation_wrapper_layout.addWidget(canvas)

        return correlation_wrapper

    def create_fuel_track_map(self, lap):
        from matplotlib.figure import Figure
        from matplotlib.collections import LineCollection
        import numpy as np
        
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
            if time_diff > 0:
                rate = fuel_diff / time_diff
                fuel_rate.append(max(0, rate))
            else:
                fuel_rate.append(0)
        
        fuel_rate.append(fuel_rate[-1] if fuel_rate else 0) 
        
        fig = Figure(figsize=(8, 8), facecolor='#BFBEC1')
        ax = fig.add_subplot(111)
        
        points = np.array([lap_data["Lon"].values, lap_data["Lat"].values]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        max_rate = max(fuel_rate) if fuel_rate else 1
        min_rate = min(fuel_rate) if fuel_rate else 0
        
        colors = []
        for rate in fuel_rate[:-1]:
            if max_rate > min_rate:
                ratio = (rate - min_rate) / (max_rate - min_rate)
            else:
                ratio = 0
            color = self.interpolate_color('#22c55e', '#ef4444', ratio)
            colors.append(color)
        
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
        
        ax.set_title(f'Lap {lap} - Fuel Consumption Rate',
                    fontsize=14, fontweight='bold', pad=10)
        ax.set_aspect('equal')
        ax.set_facecolor('white')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(lap_data["Lon"].min() - 0.0005, lap_data["Lon"].max() + 0.0005)
        ax.set_ylim(lap_data["Lat"].min() - 0.0005, lap_data["Lat"].max() + 0.0005)
        
        fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.001)
        
        FUEL_DENSITY = 0.75
        fuel_used_kg = total_fuel_used * FUEL_DENSITY

        ax.text(0.02, 0.98, f'Fuel Used: {total_fuel_used:.2f}L ({fuel_used_kg:.2f}kg)',
            transform=ax.transAxes, ha='left', va='top',
            fontsize=12, fontweight='bold', color='#111827')
        
        canvas = FigureCanvas(fig)
        canvas.setFixedSize(int(800 * self.scale_factor), int(800 * self.scale_factor))

        return canvas

# ----------------------
# Initial CSV loader window
# ----------------------
class CSVLoader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("iRacing CSV Analyzer")
        self.setGeometry(200, 200, 400, 350)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Drag & Drop your CSV here\nor click 'Browse'")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("border: 2px dashed #aaa; padding: 40px;")
        self.layout.addWidget(self.label)

        self.button = QPushButton("Browse")
        self.button.clicked.connect(self.browse_file)
        self.layout.addWidget(self.button)

        self.checkbox_group = QWidget()
        self.checkbox_layout = QVBoxLayout()
        self.checkbox_group.setLayout(self.checkbox_layout)
        self.checkbox_group.setVisible(False)
        self.layout.addWidget(self.checkbox_group)

        self.practice_cb = QCheckBox("Practice")
        self.qualifying_cb = QCheckBox("Qualifying")
        self.race_cb = QCheckBox("Race")

        self.session_group = QButtonGroup()
        self.session_group.setExclusive(True)
        self.session_group.addButton(self.practice_cb)
        self.session_group.addButton(self.qualifying_cb)
        self.session_group.addButton(self.race_cb)

        self.checkbox_layout.addWidget(self.practice_cb)
        self.checkbox_layout.addWidget(self.qualifying_cb)
        self.checkbox_layout.addWidget(self.race_cb)

        self.continue_button = QPushButton("Continue")
        self.continue_button.setVisible(False)
        self.continue_button.clicked.connect(self.on_continue)
        self.layout.addWidget(self.continue_button)

        self.csv_data = None
        self.csv_path = None

        self.setAcceptDrops(True)

        self.practice_cb.toggled.connect(self.show_continue)
        self.qualifying_cb.toggled.connect(self.show_continue)
        self.race_cb.toggled.connect(self.show_continue)

    # Drag & drop events
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith(".csv"):
                self.load_csv(file_path)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.load_csv(file_path)

    def load_csv(self, file_path):
        try:
            # simple check file exists and is valid
            self.csv_path = file_path
            self.label.setText(f"Loaded CSV:\n{file_path}")
            self.checkbox_group.setVisible(True)
            print(f"CSV loaded: {file_path}")
        except Exception as e:
            self.label.setText(f"Error loading CSV:\n{e}")
            print(f"Error loading CSV: {e}")

    def show_continue(self):
        if self.practice_cb.isChecked() or self.qualifying_cb.isChecked() or self.race_cb.isChecked():
            self.continue_button.setVisible(True)
        else:
            self.continue_button.setVisible(False)

    def on_continue(self):
        # show popup first - "wait" message TODO: loading bar
        msg = QMessageBox()
        msg.setWindowTitle("Please Wait")
        msg.setText("Reading Data: This may take a few seconds")
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.NoButton)
        msg.show()
        session_type = (
            "Practice" if self.practice_cb.isChecked() else
            "Qualifying" if self.qualifying_cb.isChecked() else
            "Race"
        )
        # force update to ensure popup appears
        QApplication.processEvents()
        
        # Clean CSV
        session_info, telemetry_df = clean_csv(self.csv_path)
        
        # Remove duplicates based on SessionTick (preserves temporal data during spins)
        telemetry_df = telemetry_df.drop_duplicates(
            subset=["SessionTick"],
            keep="first"
        ).reset_index(drop=True)

        # Sort by SessionTick for temporal order (DO NOT sort by LapTimeline)
        telemetry_df = telemetry_df.sort_values("SessionTick").reset_index(drop=True)

        # Create LapTimeline for compatibility (but don't sort by it)
        telemetry_df["LapTimeline"] = (
            telemetry_df["Lap"].astype(float) +
            telemetry_df["LapDistPct"].astype(float) / 100.0
        )

        # close popup
        msg.close()

        self.close()  
        
        # Create window
        self.telemetry_window = TelemetryWindow(session_info, telemetry_df, session_type)
        self.telemetry_window.setWindowFlags(Qt.Window)
        
        self.telemetry_window.showMaximized()
        
        # NOW detect the screen and update scale factor
        screen = self.telemetry_window.screen()
        if screen is None:
            screen = QApplication.primaryScreen()
        
        screen_width = screen.geometry().width()
        
        if screen_width <= 1920:
            self.telemetry_window.scale_factor = 0.7  
        elif screen_width <= 2560:
            self.telemetry_window.scale_factor = 0.85  
        else:
            self.telemetry_window.scale_factor = 1.0
        
        print(f"✓ Window shown on screen: {screen_width}px, Scale factor: {self.telemetry_window.scale_factor}")
        
        # Rebuild pages with correct scale
        self.telemetry_window.rebuild_pages()
        
        self.session_type = session_type


# ----------------------
# Run the app
# ----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icons/c2k.png"))
    window = CSVLoader()
    window.show()
    sys.exit(app.exec())

#TEMP TO TEST SIZES ON SMALLER MONITOR TODO: REMOVE UPON FINAL SHIP
"""if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icons/c2k.png"))
    window = CSVLoader()
    
    # Force to smallest screen (your 1080p monitor)
    screens = QApplication.screens()
    if len(screens) > 1:
        smallest_screen = min(screens, key=lambda s: s.geometry().width())
        screen_geo = smallest_screen.geometry()
        window.move(screen_geo.x() + 100, screen_geo.y() + 100)
    
    window.show()
    sys.exit(app.exec())"""

#TODO: Test scrollability of all tables, meaning, record a lot of laps, perform a lot of lockups
#TODO: Implement pitstop detection (inlap | outlap) colour them accordingly in table
#TODO: imp incident page
#TODO: imp lap v lap comaprison

