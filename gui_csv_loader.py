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
    QComboBox,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt
from PySide6.QtCore import QSize
from PySide6.QtCore import QTimer

from PySide6.QtGui import QIcon
from PySide6.QtGui import QPixmap
from PySide6.QtGui import QIcon
from PySide6.QtGui import QFont
from PySide6.QtGui import QColor
from PySide6.QtGui import QPalette

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from csv_cleaner import clean_csv



class ZoomableCanvas(FigureCanvas):
    """FigureCanvas with scroll wheel zoom and click-drag pan support"""
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

# ----------------------
# Full-screen window after CSV load
# ----------------------
class TelemetryWindow(QWidget):
    def __init__(self, session_info, telemetry_df, session_type):
        super().__init__()
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

       # -=LEFT PANEL=-
        left_panel = QWidget()
        left_panel.setFixedWidth(70)
        left_panel.setStyleSheet("background-color: #e7bdc0;")

        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignTop)
        left_layout.setSpacing(10)

        # -=STACKED VIEW=-
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #bfbec1;")

        # -=PAGES=-
        self.page_overview = self.make_overview_page()
        self.page_timings  = self.make_page("Timings")
        self.page_tyres    = self.make_page("Tyres")
        self.page_pedals   = self.make_pedals_page()
        self.page_fuel     = self.make_page("Fuel")
        self.page_data     = self.make_page("Data Viewer")

        self.stack.addWidget(self.page_overview)  # 0
        self.stack.addWidget(self.page_timings)   # 1
        self.stack.addWidget(self.page_tyres)     # 2
        self.stack.addWidget(self.page_pedals)    # 3
        self.stack.addWidget(self.page_fuel)      # 4
        self.stack.addWidget(self.page_data)      # 5

        # -=BUTTONS=-
        buttons = [
            ("icons/icon_Overview.png", 0, "Session - Overview"),
            ("icons/icon_Timings.png",  1, "Session - Timings"),
            ("icons/icon_Tyre.png",     2, "Data - Tyres"),
            ("icons/icon_Pedals.png",   3, "Data - Pedals"),
            ("icons/icon_Fuel.png",     4, "Data - Fuel"),
            ("icons/icon_Data.png",     5, "View Data"),
        ]

        for icon_path, index, tooltip_text in buttons:
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(48, 48))
            btn.setFixedSize(48, 48)
            btn.setToolTip(tooltip_text) 
            btn.setStyleSheet("""
                QPushButton {
                border: none;
                background-color: transparent;
                }
                QPushButton:hover {
                background-color: rgba(30, 41, 59, 120);
                border-radius: 6px;
                }
            """)
            btn.clicked.connect(lambda _, i=index: self.stack.setCurrentIndex(i))
            left_layout.addWidget(btn)
            ####TODO: - Add loading bar (thanks cameron)
        
        body_layout.addWidget(left_panel)
        body_layout.addWidget(self.stack)

        # Load CSV head(ONLY 20 ROWS due to extreme dimensionality - maybe change to scrollable element)
        self.load_table_preview()

    # ===============================
    # CSV Preview Loader
    # ===============================
    def load_table_preview(self):
        self.preview_rows = 200  
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

    #==========
    # PLOT TRACK MAP
    #==========
    def make_track_map_widget(self, venue):
        """Create a track map visualization from GPS data"""
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        import numpy as np

        # for overview screen track "map" i plot the co-ord-s of the first clean* lap in the data set, if not clean lap is present, fastest lap is used
        # Clean Lap* = a clean lap is one where the car is recorded as being "on-track" for the entire lap, to ensure an accurate depiction of the map
        selected_lap_data = None

        # Get valid laps (Lap > 0) done because lap 0 in PRACTICE/QUALIFYING session starts in pits, and in RACE sessions is the small distance at start before crossing the line, either from a standing start or rolling start
        valid_laps = self.telemetry_df[self.telemetry_df["Lap"] > 0]["Lap"].unique()

        # Rretrieving the first clean* lap that i mentioned above
        for lap_num in sorted(valid_laps):
            lap_data = self.telemetry_df[
                (self.telemetry_df["Lap"] == lap_num)
            ].copy()
    
            # here is the check for the car on track for entirety of lap
            if (lap_data["IsOnTrackCar"] == 1).all():
                selected_lap_data = lap_data
                break

        # fallback = i go to the fastest lap in the dataset
        if selected_lap_data is None:
            fastest_lap_num = int(self.telemetry_df.loc[
                self.telemetry_df["LapLastLapTime"].idxmin()
            ]["Lap"])
            selected_lap_data = self.telemetry_df[
            self.telemetry_df["Lap"] == fastest_lap_num
        ].copy()
        
        # sorting by LapDistPct
        selected_lap_data = selected_lap_data.sort_values("LapDistPct")

        # Using matplot lib to plot the coordinates
        fig = Figure(figsize=(10, 8), facecolor='#bfbec1')
        ax = fig.add_subplot(111)

        # Plot the track TODO: potentially add some UI which allows user to alter the colours for preference
        ax.plot(selected_lap_data["Lon"], selected_lap_data["Lat"], 
            color='#2563eb', linewidth=3.5)

        # Here i add a red line perpendicular to the direction of the first two coordinates on the lap, while this could be achieved to a more accurate degree by taking the last point of the previous lap, doing it like this is adequate as the ibt file enters a row of data for every tick in the session, so even when downscaled, this is still accurate enough to be used on my map
        # first point of lap
        start_lon = selected_lap_data["Lon"].iloc[0]
        start_lat = selected_lap_data["Lat"].iloc[0]

        # second pont of the lap
        second_lon = selected_lap_data["Lon"].iloc[1]
        second_lat = selected_lap_data["Lat"].iloc[1]

        # calculating the direction of the line between these 2 points
        dx = second_lon - start_lon
        dy = second_lat - start_lat

        # Calculating the perpendicular line
        perp_dx = -dy
        perp_dy = dx

        # Scaling for this perpendicular line 
        length = np.sqrt(perp_dx**2 + perp_dy**2)
        if length > 0:
            perp_dx = perp_dx / length * 0.0003
            perp_dy = perp_dy / length * 0.0003

        # Plotting it
        ax.plot([start_lon - perp_dx, start_lon + perp_dx],
                [start_lat - perp_dy, start_lat + perp_dy],
                color='red', linewidth=2.5, zorder=10)
    
        # Extra function for capitalising the title of the track, and ensuring that if 'gp' is present it is written as 'GP' to realistically reflect the title of a track's Grand Prix layout
        def capitalize_venue(venue_name):
            words = venue_name.split()
            capitalized_words = []
            for word in words:
                if word.lower() == "gp":
                    capitalized_words.append("GP")
                else:
                    capitalized_words.append(word.capitalize())
            return " ".join(capitalized_words)

        track_title = f"{capitalize_venue(venue)} - Track Map"
        ax.set_aspect('equal')
        ax.set_title(track_title, fontsize=14, fontweight='bold', pad=10)
        ax.grid(True, alpha=0.2, linestyle='--')
        ax.set_facecolor('white')
    
        # remove axis labels
        ax.set_xticks([])
        ax.set_yticks([])
    
        # tight layout, to cut down on whitespace
        fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02)
    
        # Creating a widget to house the plot
        canvas = FigureCanvas(fig)
        return canvas
    
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
        title = QLabel(f"{session_type} Session Overview")
        title.setStyleSheet("""
            font-size: 38px;
            font-weight: bold;
            color: #000007;
        """)
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title)

        # Get Environmental Data from csv
        # taking from first non-null value (subject to change this as not very resilient)
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

        # Get weather condition using index and applying the icons
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
    
        # applying the weathre icon
        weather_icon = QLabel()
        weather_pixmap = QPixmap(f"icons/{weather_icon_name}.png")
        if not weather_pixmap.isNull():
            # Ensure border is visible, had some clipping issues
            weather_icon.setPixmap(weather_pixmap.scaled(55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        weather_icon.setFixedSize(60, 60)
        weather_icon.setAlignment(Qt.AlignCenter)
    
         # Weather text
        weather_value = QLabel(weather_text)
        weather_value.setStyleSheet("font-size: 24px; color: #111827; font-weight: bold;")

        #REFERENCE OF MEASUREMENTS (dont forget to remove after completion TODO)
        # Air & Track Temps in C*
        # Humidity in %
        # Air Pressure in Hg
        # Air Density in kg/m^3
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

        # -=Horizontal layout for table and track map=-
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)  # Space between table and map

        # -=Table Data=-
        # TODO: need to remove the headers
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

        # Set fixed table size to show all rows
        table.setFixedHeight(150) 
        table.setFixedWidth(500)  

        table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # no scrolling necesary on this one as its way smaller than the preview screen table
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
        #Map Size
        track_map.setFixedSize(600, 500) 
        table.setContentsMargins(0, 0, 0, 0)
        table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Add table and track map to horizontal layout
        content_layout.addWidget(table, alignment=Qt.AlignTop | Qt.AlignLeft)
        content_layout.addWidget(track_map, alignment=Qt.AlignTop | Qt.AlignLeft)
        content_layout.addStretch()  

        
        layout.addLayout(content_layout)

        layout.addStretch()

        return page



    # -----------------------
    # Make a page for the stacked widget
    # -----------------------
    def make_page(self, title):
        page = QWidget()
        layout = QVBoxLayout(page)

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

            layout.addWidget(self.table, alignment=Qt.AlignTop | Qt.AlignLeft)
            layout.addStretch() 

        return page
    
    #================
    # Pedal Data Page
    #================
    def make_pedals_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 1)
        layout.setSpacing(1)

        # Title
        title = QLabel("Pedal Usage Data")
        title.setStyleSheet("""
            font-size: 38px;
            font-weight: bold;
            color: #000007;
        """)
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        # Main content layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # === LEFT SIDE: Lap Selector ===
        lap_selector_container = QWidget()
        lap_selector_container.setFixedWidth(250)
        lap_selector_layout = QVBoxLayout(lap_selector_container)
        lap_selector_layout.setContentsMargins(0, 0, 0, 0)
        lap_selector_layout.setSpacing(0)

        order_layout = QHBoxLayout()
        order_label = QLabel("Order by:")
        order_label.setStyleSheet("font-size: 22px; color: black; font-weight: bold;")

        self.lap_order_selector = QComboBox()
        self.lap_order_selector.addItem("Chronological", "chronological")
        self.lap_order_selector.addItem("Fastest to Slowest", "fastest")
        self.lap_order_selector.addItem("Slowest to Fastest", "slowest")
        self.lap_order_selector.setStyleSheet("""
            QComboBox {
                font-size: 16px;
                color: black;
                padding: 5px;
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

        # === RIGHT SIDE widget: atm track map (coloured on throttle) + pedal playbackgraph ===
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Track map container
        self.pedal_map_container = QWidget()
        self.pedal_map_layout = QVBoxLayout(self.pedal_map_container)
        self.pedal_map_layout.setAlignment(Qt.AlignLeft)
        self.pedal_map_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.pedal_map_container)

        # Playback controls
        controls_widget = QWidget()
        controls_widget.setFixedHeight(50)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        controls_layout.setSpacing(10)

        self.play_pause_btn = QPushButton("▶ Play")
        self.play_pause_btn.setFixedWidth(100)
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
        self.reset_btn.setFixedWidth(100)
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

        # Speed multiplier
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet("font-size: 14px; font-weight: bold; color: black;")

        self.speed_selector = QComboBox()
        self.speed_selector.addItem("1x", 1)
        self.speed_selector.addItem("2x", 2)
        self.speed_selector.addItem("4x", 4)
        self.speed_selector.addItem("8x", 8)
        self.speed_selector.setFixedWidth(70)
        self.speed_selector.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                color: black;
                padding: 3px;
            }
        """)

        # Playback time label
        self.playback_time_label = QLabel("0.000s / 0.000s")
        self.playback_time_label.setStyleSheet("font-size: 14px; color: black; font-weight: bold;")

        controls_layout.addWidget(self.play_pause_btn)
        controls_layout.addWidget(self.reset_btn)
        controls_layout.addWidget(speed_label)
        controls_layout.addWidget(self.speed_selector)
        controls_layout.addWidget(self.playback_time_label)
        controls_layout.addStretch()

        right_layout.addWidget(controls_widget)

        # Pedal graph container
        self.pedal_graph_container = QWidget()
        self.pedal_graph_layout = QVBoxLayout(self.pedal_graph_container)
        self.pedal_graph_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.pedal_graph_container)

        # Add both sides to content layout
        content_layout.addWidget(lap_selector_container)
        content_layout.addWidget(right_container)
        content_layout.addStretch()

        layout.addLayout(content_layout)
        layout.addStretch()

        # Playback state TODO: noticed bug not resetting to 1x speed after switching to 8x speed and switching back to lower multiplier quickly after that
        self.playback_index = 0
        self.playback_active = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.playback_step)
        self.current_lap_data = None
        self.playback_interval = 100
        self.lap_data_dict = {}

        # Get valid laps
        valid_laps = sorted(self.telemetry_df[self.telemetry_df["Lap"] > 0]["Lap"].unique())
        if len(valid_laps) > 1:
            valid_laps = valid_laps[:-1]

        for lap in valid_laps:
            lap_times = self.telemetry_df[
                (self.telemetry_df["Lap"] == lap + 1) &
                (self.telemetry_df["LapLastLapTime"] > 0)
            ]["LapLastLapTime"]

            if len(lap_times) > 0:
                lap_time = lap_times.iloc[0]
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

        self.update_lap_list()

        if self.lap_list.count() > 0:
            self.lap_list.setCurrentRow(0)
            self.update_pedal_track_map_from_list()

        return page

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

        # Stop any active playback
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

        if selected_lap is None:
            return

        venue = self.session_info.get("Venue", "Unknown Venue")

        lap_data = self.telemetry_df[
            (self.telemetry_df["Lap"] == selected_lap) &
            (self.telemetry_df["IsOnTrackCar"] == 1)
        ].copy()

        if len(lap_data) == 0:
            error_label = QLabel("No data available for this lap")
            error_label.setAlignment(Qt.AlignCenter)
            self.pedal_map_layout.addWidget(error_label)
            return

        lap_data = lap_data.sort_values("LapDistPct").reset_index(drop=True)

        # Store for playback
        self.current_lap_data = lap_data
        self.playback_index = 0

        lap_time_val = self.lap_data_dict.get(selected_lap, {}).get('time', 0)
        lap_time_str = self.lap_data_dict.get(selected_lap, {}).get('time_str', 'N/A')
        row_count = len(lap_data)

        # Calculation to match realtime playback as closely as possible to 1s in data = 1s in realtime playback
        if lap_time_val > 0 and lap_time_val != float('inf') and row_count > 0:
            self.playback_interval = (lap_time_val / row_count) * 1000  # ms per row
        else:
            self.playback_interval = 100

        # Update time label
        self.playback_time_label.setText(f"0.000s / {lap_time_val:.3f}s")

        # ===== STATIC TRACK MAP =====
        fig_map = Figure(figsize=(15, 10), facecolor='#bfbec1')
        ax_map = fig_map.add_subplot(111)

        points = np.array([lap_data["Lon"].values, lap_data["Lat"].values]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        throttle = lap_data["Throttle"].values
        brake = lap_data["Brake"].values
        COAST_THRESHOLD = 3

        colors = []
        for i in range(len(throttle) - 1):
            if throttle[i] < COAST_THRESHOLD and brake[i] < COAST_THRESHOLD:
                colors.append('#ffcd03')
            elif throttle[i] > brake[i]:
                colors.append('#079902')
            else:
                colors.append('#ff0318')

        lc = LineCollection(segments, colors=colors, linewidths=3.5)
        ax_map.add_collection(lc)

        # Start/finish line NOTE: cant be green here due to colour being used for throttle
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

        # Driver dot (default pos at start of lap)
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

        ax_map.set_title(f"Lap {selected_lap} - Throttle/Brake Usage",
                        fontsize=14, fontweight='bold', pad=10, loc='left')
        ax_map.text(0.98, 0.98, f"Lap Time: {lap_time_str}",
                    transform=ax_map.transAxes, fontsize=12,
                    verticalalignment='top', horizontalalignment='right',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax_map.set_aspect('equal')
        ax_map.set_facecolor('white')
        ax_map.set_xticks([])
        ax_map.set_yticks([])
        ax_map.set_xlim(lap_data["Lon"].min() - 0.0005, lap_data["Lon"].max() + 0.0005)
        ax_map.set_ylim(lap_data["Lat"].min() - 0.0005, lap_data["Lat"].max() + 0.0005)
        fig_map.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02)

        self.map_canvas = ZoomableCanvas(fig_map)
        self.map_canvas.setFixedSize(800, 650)
        self.map_ax = ax_map
        self.pedal_map_layout.addWidget(self.map_canvas, alignment=Qt.AlignTop | Qt.AlignLeft)

        # ===== PEDAL GRAPH =====
        fig_pedal = Figure(figsize=(10, 3.5), facecolor='#bfbec1')
        self.pedal_ax = fig_pedal.add_subplot(111)
        self.pedal_ax.set_facecolor('#1a1a2e')
        self.pedal_ax.set_xlim(0, 5) 
        self.pedal_ax.set_ylim(-5, 105)
        self.pedal_ax.set_ylabel("Input %", fontsize=10, color='white')
        self.pedal_ax.tick_params(colors='white')
        self.pedal_ax.set_xlabel("Time (s)", fontsize=10, color='white')
        for spine in self.pedal_ax.spines.values():
            spine.set_edgecolor('#444444')

        # dashed lines for reference at 25,50 and 70 perc %
        for y_val in [25, 50, 75]:
            self.pedal_ax.axhline(
                y=y_val,
                color='#adadad',
                linewidth=1,
                linestyle='--',
                alpha=0.3,
                zorder=1
            )
            
        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#079902', label='Throttle'),
            Patch(facecolor='#ff0318', label='Brake'),
        ]
        self.pedal_ax.legend(
            handles=legend_elements,
            loc='upper left',
            bbox_to_anchor=(0, -.20),  
            ncol=2,                      
            facecolor='#bfbec1',
            labelcolor='black',
            fontsize=9,
            framealpha=1,
            edgecolor='#444444'
        )

        # Initialize empty lines
        self.throttle_line, = self.pedal_ax.plot([], [], color='#04ff00', linewidth=1, label='Throttle')
        self.brake_line, = self.pedal_ax.plot([], [], color='#ff0000', linewidth=1, label='Brake')

        fig_pedal.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=0.25)

        self.pedal_canvas = FigureCanvas(fig_pedal)
        self.pedal_canvas.setFixedSize(800, 250)
        self.pedal_graph_layout.addWidget(self.pedal_canvas, alignment=Qt.AlignTop | Qt.AlignLeft)

        # Playback time tracking
        self.playback_time_data = []
        self.playback_throttle_data = []
        self.playback_brake_data = []
        self.current_time = 0.0
        self.time_per_row = self.playback_interval / 1000.0

    def toggle_playback(self):
        if self.current_lap_data is None:
            return

        if self.playback_active:
            # Pause
            self.playback_timer.stop()
            self.playback_active = False
            self.play_pause_btn.setText("▶ Play")
        else:
            # Play - reset if at end
            if self.playback_index >= len(self.current_lap_data) - 1:
                self.reset_playback()

            self.playback_active = True
            self.play_pause_btn.setText("⏸ Pause")

            # Apply speed multiplier
            speed = self.speed_selector.currentData()
            interval = max(1, int(self.playback_interval / speed))
            self.playback_timer.start(interval)

    def reset_playback(self):
        self.playback_timer.stop()
        self.playback_active = False
        self.play_pause_btn.setText("▶ Play")
        self.playback_index = 0
        self.current_time = 0.0
        self.playback_time_data = []
        self.playback_throttle_data = []
        self.playback_brake_data = []

        if self.current_lap_data is not None:
            lap_time_val = 0
            for info in self.lap_data_dict.values():
                pass  

            # Reset dot to start
            if hasattr(self, 'driver_dot') and hasattr(self, 'map_canvas'):
                self.driver_dot.set_data(
                    [self.current_lap_data["Lon"].iloc[0]],
                    [self.current_lap_data["Lat"].iloc[0]]
                )
                self.map_canvas.draw()

            # Reset pedal graph
            if hasattr(self, 'throttle_line'):
                self.throttle_line.set_data([], [])
                self.brake_line.set_data([], [])
                self.pedal_ax.set_xlim(0, 5)
                self.pedal_canvas.draw()

            self.playback_time_label.setText(f"0.000s / {self.time_per_row * len(self.current_lap_data):.3f}s")

    def playback_step(self):
        if self.current_lap_data is None:
            return

        speed = self.speed_selector.currentData()

        # Advance multiple steps if speed > 1x
        for _ in range(speed):
            if self.playback_index >= len(self.current_lap_data) - 1:
                self.playback_timer.stop()
                self.playback_active = False
                self.play_pause_btn.setText("▶ Play")
                return

            row = self.current_lap_data.iloc[self.playback_index]
            self.current_time += self.time_per_row

            
            self.playback_time_data.append(self.current_time)
            self.playback_throttle_data.append(float(row["Throttle"]))
            self.playback_brake_data.append(float(row["Brake"]))

            self.playback_index += 1

        # Update driver dot on map
        current_row = self.current_lap_data.iloc[self.playback_index]
        self.driver_dot.set_data([current_row["Lon"]], [current_row["Lat"]])
        self.map_canvas.draw()

        # Update pedal graph with rolling 5 second window
        window_seconds = 5.0
        times = self.playback_time_data
        throttles = self.playback_throttle_data
        brakes = self.playback_brake_data

        # Find start of window
        window_start = self.current_time - window_seconds
        start_idx = 0
        for i, t in enumerate(times):
            if t >= window_start:
                start_idx = i
                break

        windowed_times = times[start_idx:]
        windowed_throttle = throttles[start_idx:]
        windowed_brake = brakes[start_idx:]

        self.throttle_line.set_data(windowed_times, windowed_throttle)
        self.brake_line.set_data(windowed_times, windowed_brake)

        # Scroll the x axis
        if self.current_time > window_seconds:
            self.pedal_ax.set_xlim(self.current_time - window_seconds, self.current_time)
        else:
            self.pedal_ax.set_xlim(0, window_seconds)

        self.pedal_canvas.draw()

        # Update time label
        total_time = self.time_per_row * len(self.current_lap_data)
        self.playback_time_label.setText(f"{self.current_time:.3f}s / {total_time:.3f}s")
        

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
        telemetry_df["LapTimeline"] = (
            telemetry_df["Lap"].astype(float) +
            telemetry_df["LapDistPct"].astype(float) / 100.0
        )
        
        
        telemetry_df["LapTimeline"] = telemetry_df["LapTimeline"].round(3)
        #Removing dupes
        telemetry_df = telemetry_df.drop_duplicates(
            subset=["LapTimeline"],
            keep="first"
        ).reset_index(drop=True)

        # Add Ordering Row Lap + LapDist-ct /100 [LapTimeline]
        telemetry_df = telemetry_df.sort_values("LapTimeline").reset_index(drop=True)

        # close window
        msg.close()

        self.close()  
        self.telemetry_window = TelemetryWindow(session_info, telemetry_df, session_type)
        self.telemetry_window.setWindowFlags(Qt.Window)
        self.telemetry_window.showMaximized()
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
