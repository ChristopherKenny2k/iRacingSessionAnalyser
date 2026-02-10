import sys
import pandas as pd
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QSizePolicy,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QButtonGroup,
    QMessageBox
)
from PySide6.QtCore import Qt
from csv_cleaner import clean_csv  # our cleaner function

# ----------------------
# Full-screen window after CSV load
# ----------------------
class TelemetryWindow(QWidget):
    def __init__(self, session_info, telemetry_df):
        super().__init__()
        self.session_info = session_info
        self.telemetry_df = telemetry_df

        # Window title and size
        self.setWindowTitle("iRacing Telemetry Viewer")
        self.setGeometry(100, 100, 1280, 720)  # start windowed
        self.setStyleSheet("background-color: #D3D3D3;")  # light grey background

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # remove default margins
        self.setLayout(layout)

        # ----------------------
        # Top banner ribbon
        # ----------------------
        driver = session_info.get("Driver", "Unknown Driver")
        vehicle = session_info.get("Vehicle", "Unknown Vehicle")
        venue = session_info.get("Venue", "Unknown Venue")
        header_text = f"{driver} | {vehicle} | {venue}"

        self.header_label = QLabel(header_text)
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet("""
            background-color: #003366;  /* dark blue */
            color: white;
            font-size: 24px;
            font-weight: bold;
            padding: 10px;
        """)
        # Make banner only as tall as it needs to be
        self.header_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.header_label)

        # ----------------------
        # Main content area
        # ----------------------
        self.info_label = QLabel("Telemetry loaded! Graphs will appear here...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            font-size: 18px;
            padding: 20px;
        """)
        # Expand to fill remaining space
        self.info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.info_label)

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
            # Don't try to parse the CSV fully here — just check it exists
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
         # Show popup first
        msg = QMessageBox()
        msg.setWindowTitle("Please Wait")
        msg.setText("Reading Data: This may take a few seconds")
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.NoButton)  # no buttons so it’s just a message
        msg.show()
    
        # Force the GUI to update so the message appears
        QApplication.processEvents()
        # Clean CSV
        session_info, telemetry_df = clean_csv(self.csv_path)

        # Close this window
        msg.close()

        self.close()  # close CSV loader
        self.telemetry_window = TelemetryWindow(session_info, telemetry_df)
        self.telemetry_window.setWindowFlags(Qt.Window)
        self.telemetry_window.showMaximized()


# ----------------------
# Run the app
# ----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVLoader()
    window.show()
    sys.exit(app.exec())
