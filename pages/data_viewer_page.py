from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QSizePolicy
from PySide6.QtCore import Qt


class DataViewerPageMixin:
    """Simple raw-data preview page (used for the 'Data Viewer' nav item).
    this page doesnt feature any visualistions, its simply just a window displaying the raw ibt->csv data should any user be interested in 
    seeing the vast amount of data that iracing can provide"""

    def make_page(self, title):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 22px; font-weight: bold; color: #1f2937;")
        layout.addWidget(label)

        if title == "Data Viewer":
            self.table = QTableWidget()
            self.table.setStyleSheet("""
                QTableWidget { background-color: #f2f2f2; color: #000000; gridline-color: #cccccc; font-size: 12px; }
                QHeaderView::section { background-color: #2c3e50; color: white; font-weight: bold; border: none; padding: 4px; }
                QTableWidget::item:selected { background-color: #3498db; color: white; }
            """)
            self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            layout.addWidget(self.table)

        return page

    def load_table_preview(self):
        self.preview_rows = 75
        df = self.telemetry_df.iloc[:self.preview_rows]

        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns.tolist())

        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iat[row, col]
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setAlternatingRowColors(True)
        self.table.resizeColumnsToContents()
