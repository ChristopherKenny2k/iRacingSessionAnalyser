import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from utils.resource_path import resource_path
from csv_loader import CSVLoader


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("icons/c2k.png")))
    window = CSVLoader()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
