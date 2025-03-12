from PySide6.QtWidgets import QWidget, QFileDialog

from cache.config import Ui_Config


class ConfigLogic(QWidget):
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