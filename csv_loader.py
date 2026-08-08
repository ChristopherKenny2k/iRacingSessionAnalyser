from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox,
    QButtonGroup, QProgressDialog,
)
from PySide6.QtCore import Qt

from csv_cleaner import clean_csv
from telemetry_window import TelemetryWindow


class CSVLoader(QWidget):
    """The initial drag-and-drop / browse window shown on app startup."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("iRacing CSV Analyser")
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
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.load_csv(file_path)

    def load_csv(self, file_path):
        try:
            self.csv_path = file_path
            self.label.setText(f"Loaded CSV:\n{file_path}")
            self.checkbox_group.setVisible(True)
        except Exception as e:
            self.label.setText(f"Error loading CSV:\n{e}")

    def show_continue(self):
        if self.practice_cb.isChecked() or self.qualifying_cb.isChecked() or self.race_cb.isChecked():
            self.continue_button.setVisible(True)
        else:
            self.continue_button.setVisible(False)

    def on_continue(self):
        session_type = (
            "Practice" if self.practice_cb.isChecked() else
            "Qualifying" if self.qualifying_cb.isChecked() else
            "Race"
        )

        progress = QProgressDialog("Please Wait \nLoading telemetry data...", None, 0, 100, self)
        progress.setWindowTitle("Loading")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setMinimumSize(350, 200)
        progress.resize(350, 200)

        progress.setStyleSheet("""
            QProgressDialog { font-size: 14px; }
            QProgressBar { border: 2px solid #d1d5db; border-radius: 5px; text-align: center; font-size: 12px; font-weight: bold; }
            QProgressBar::chunk { background-color: #22c55e; border-radius: 3px; }
        """)

        progress.setValue(0)
        QApplication.processEvents()

        progress.setLabelText("Please Wait \nReading CSV file...")
        progress.setValue(10)
        QApplication.processEvents()

        session_info, telemetry_df = clean_csv(self.csv_path)
        progress.setValue(40)
        QApplication.processEvents()

        progress.setLabelText("Please Wait \nRemoving duplicates...")
        QApplication.processEvents()

        telemetry_df = telemetry_df.drop_duplicates(subset=["SessionTick"], keep="first").reset_index(drop=True)
        progress.setValue(60)
        QApplication.processEvents()

        progress.setLabelText("Please Wait \nSorting telemetry data...")
        QApplication.processEvents()

        telemetry_df = telemetry_df.sort_values("SessionTick").reset_index(drop=True)
        progress.setValue(80)
        QApplication.processEvents()

        progress.setLabelText("Please Wait \nCreating lap timeline...")
        QApplication.processEvents()

        telemetry_df["LapTimeline"] = (
            telemetry_df["Lap"].astype(float) +
            telemetry_df["LapDistPct"].astype(float) / 100.0
        )
        progress.setValue(90)
        QApplication.processEvents()

        progress.setLabelText("Please Wait \nInitialising interface...")
        QApplication.processEvents()

        self.close()

        self.telemetry_window = TelemetryWindow(session_info, telemetry_df, session_type)
        self.telemetry_window.setWindowFlags(Qt.Window)
        self.telemetry_window.showMaximized()

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

        self.telemetry_window.rebuild_pages()

        progress.setValue(100)
        progress.close()

        self.session_type = session_type
