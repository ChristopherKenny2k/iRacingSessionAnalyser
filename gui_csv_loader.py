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
    QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtGui import QPixmap
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from PySide6.QtGui import QFont
from PySide6.QtGui import QColor
from PySide6.QtGui import QPalette
from csv_cleaner import clean_csv  # csv cleaner

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
        self.page_pedals   = self.make_page("Pedals")
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
        # ===== ADD TO BODY =====
        body_layout.addWidget(left_panel)
        body_layout.addWidget(self.stack)

        # Load CSV head(ONLY 20 ROWS due to extreme dimensionality - maybe change to scrollable element)
        self.load_table_preview()

    # ===============================
    # CSV Preview Loader
    # ===============================
    def load_table_preview(self):
        self.preview_rows = 200   # safe limit for UI
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


    
    # -----------------------
    # Overview Page
    # -----------------------
    def make_overview_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 2, 2, 5)
        layout.setSpacing(5)

        # -=Title=-
        session_type = self.session_type if hasattr(self, "session_type") else "Practice"
        title = QLabel(f"{session_type} Session Overview")
        title.setStyleSheet("""
            font-size: 38px;
            font-weight: bold;
            color: #000007;
        """)
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title)  # title at the top

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
        pressure_str = f"{air_pressure / 3386.39:.2f} inHg"
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
        weather_icon.setFixedSize(60, 60) #keep slightly larger so border is visible
        weather_icon.setAlignment(Qt.AlignCenter)
    
        # Weather text
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
        track_temp_value = QLabel(air_temp_str)
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
        table.setHorizontalHeaderLabels(overview_df.columns.tolist())
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
        table.setFixedHeight(137) 
        table.setFixedWidth(400)  

        
        table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # no scrolling necesary on this one
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                color: #111827;
                gridline-color: #27272b;
                font-size: 20px;
            }
            QHeaderView::section {
                background-color: #d4d3e6;
                color: black;
                font-weight: bold;
                font-size: 20px;
                border: none;
                padding: 6px;
            }
        """)

        # Add table directly under the horiz bar
        layout.addWidget(table, alignment=Qt.AlignTop | Qt.AlignLeft)


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
            layout.addStretch()  # Add table to this page

        return page
    
    

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
         # show popup first - "wait" message
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
