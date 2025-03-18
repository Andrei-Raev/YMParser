import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from UI.export_logic import ExportLogic
from cache.mainwindow import Ui_MainWindow
from config_logic import ConfigLogic


class MainWindow(QMainWindow):
    config_logic: ConfigLogic

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Добавляем логику конфига
        self.config_logic = ConfigLogic(self)
        config_layout = self.ui.config_area.layout()
        config_layout.addWidget(self.config_logic)

        # Добавляем логику экспорта
        self.export_logic = ExportLogic(self)
        export_layout = self.ui.output_area.layout()
        export_layout.addWidget(self.export_logic)

        self.setWindowTitle("Веб-парсер")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
