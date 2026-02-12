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
    QToolTip
)
from PySide6.QtCore import Qt
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

        palette = QPalette()
        palette.setColor(QPalette.ToolTipBase, QColor("white"))
        palette.setColor(QPalette.ToolTipText, QColor("black"))
        QApplication.setPalette(palette)

        self.setWindowTitle("iRacing Telemetry Viewer")
        self.resize(1600, 900)
        self.setStyleSheet("background-color: #eeeeee;")

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
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        # -=Header Ribbon=-
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: #0b2a4a;")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 0, 20, 0)
        header.setLayout(header_layout)

        driver = session_info.get("Driver", "Unknown Driver")
        vehicle = session_info.get("Vehicle", "Unknown Vehicle")
        venue = session_info.get("Venue", "Unknown Venue")

        header_label = QLabel(f"{driver} | {vehicle} | {venue}")
        header_label.setStyleSheet("""
            color: white;
            font-size: 20px;
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

       # ===== LEFT PANEL =====
        left_panel = QWidget()
        left_panel.setFixedWidth(70)
        left_panel.setStyleSheet("background-color: #ccffff;")

        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignTop)
        left_layout.setSpacing(10)

        # ===== STACKED VIEW =====
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #eeeeee;")

        # ===== PAGES =====
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

        # ===== BUTTONS =====
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
            ####BOZO - Add loading bar (thanks cameron)
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

        # Scrollbars
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # UX
        self.table.setAlternatingRowColors(True)
        self.table.resizeColumnsToContents()


    
    # -----------------------
    # Overview Page
    # -----------------------
    def make_overview_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # ===== Title =====
        session_type = self.session_type if hasattr(self, "session_type") else "Practice"
        title = QLabel(f"{session_type} Session Overview")
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #1f2937;
        """)
        layout.addWidget(title, alignment=Qt.AlignLeft)

        df = self.telemetry_df.copy()

        df_valid = df[
            (df["Lap"] > 0) &
            (df["LapLastLapTime"] > 0) &
            (~df["LapLastLapTime"].isna())
        ].copy()

        # ===== Calculations =====

        # Laps Completed (second highest Lap, cause partial final past finish tracked)
        laps = sorted(df_valid["Lap"].dropna().unique())
        laps_completed = int(laps[-1]) if len(laps) >= 1 else 0

        # Get the fastest lap 
        fastest_lap_seconds = df_valid["LapLastLapTime"].min()

        minutes = int(fastest_lap_seconds // 60)
        seconds = int(fastest_lap_seconds % 60)
        millis = int((fastest_lap_seconds - int(fastest_lap_seconds)) * 1000)
        fastest_lap_formatted = f"{minutes:02}:{seconds:02}.{millis:03}"

        # gotta get the lap of fastest lap 
        fastest_lap_row = df_valid.loc[df_valid["LapLastLapTime"].idxmin()]
        fastest_lap_on = int(fastest_lap_row["Lap"])

        #DEBUG TO GET VERIFY FASTEST SELECTED DELETE THIS BOZO
        unique_times = sorted(df_valid["LapLastLapTime"].dropna().unique())
        print("\n--- UNIQUE VALID LAP TIMES (seconds) ---")
        for t in unique_times[:20]:  
            print(t)

        print("\nFastest 10 laps:")
        for t in unique_times[:10]:
            mins = int(t // 60)
            secs = int(t % 60)
            ms = int((t - int(t)) * 1000)
        print(f"{mins:02}:{secs:02}.{ms:03}")
        # ===== Temporary Overview DataFrame =====
        overview_df = pd.DataFrame({
            "Metric": [
                "Laps Completed",
                "Fastest Lap",
                "Fastest Lap Set On"
            ],
            "Value": [
                laps_completed,
                fastest_lap_formatted,
                fastest_lap_on
            ]
        })

        # ===== Table Widget =====
        table = QTableWidget()
        table.setRowCount(len(overview_df))
        table.setColumnCount(len(overview_df.columns))
        table.setHorizontalHeaderLabels(overview_df.columns.tolist())

        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                color: #111827;
                gridline-color: #e5e7eb;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #0b2a4a;
                color: white;
                font-weight: bold;
                border: none;
                padding: 6px;
            }
        """)

        for row in range(len(overview_df)):
            for col in range(len(overview_df.columns)):
                item = QTableWidgetItem(str(overview_df.iat[row, col]))
                if col == 0:
                    item.setFlags(Qt.ItemIsEnabled)  # non-editable
                table.setItem(row, col, item)

        table.resizeColumnsToContents()
        table.setFixedWidth(500)
        table.setFixedHeight(200)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)

        layout.addWidget(table, alignment=Qt.AlignLeft)
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

        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()

        # If this is the Data Viewer page, add the table
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

            layout.addWidget(self.table)  # Add table to this page

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
         # show popup first - inform user to wait 
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
        
        #Round to 3 decimals
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

        self.close()  # close CSV loader
        self.telemetry_window = TelemetryWindow(session_info, telemetry_df, session_type)
        self.telemetry_window.setWindowFlags(Qt.Window)
        self.telemetry_window.showMaximized()
        self.session_type = session_type


# ----------------------
# Run the app
# ----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVLoader()
    window.show()
    sys.exit(app.exec())
