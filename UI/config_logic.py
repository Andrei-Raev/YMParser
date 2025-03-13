from PySide6.QtWidgets import QWidget, QFileDialog

from UI.cache.configAbout import Ui_configAbout
from cache.config import Ui_Config


class ConfigLogic(QWidget):
    about: "ConfigAbout" = None
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Config()
        self.ui.setupUi(self)

        self.ui.selectFile.clicked.connect(self.select_file)

    def select_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.ui.fileInputLine.setText(file_path)

        self.about = ConfigAbout()

        # Добавляем логику конфига
        config_layout = self.ui.fileDataContents.layout()
        config_layout.addWidget(self.about)


class ConfigAbout(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_configAbout()
        self.ui.setupUi(self)
