from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QWidget, QFileDialog, QDialog, QErrorMessage, QMessageBox, QSizePolicy

from UI.cache.configInfo import Ui_configInfo
from cache.configAbout import Ui_configAbout
from cache.config import Ui_Config
from datatype import ParserConfig, PropertyGroup


class ConfigLogic(QWidget):
    about: Optional["ConfigAbout"] = None
    config: Optional[ParserConfig] = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_Config()
        self.ui.setupUi(self)

        self.config = None
        self.about = None

        self.ui.selectFile.clicked.connect(self.select_file)

        self.setAcceptDrops(True)

    def select_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        # file_dialog.setNameFilter('ZIP (*.zip)')

        if file_dialog.exec():

            del self.config
            self.config = None

            if self.about is not None:
                self.about.close()
            del self.about
            self.about = None

            file_path = file_dialog.selectedFiles()[0]
            self.load_from_file(file_path)

    def dragEnterEvent(self, event):
        """Обрабатывает событие начала перетаскивания."""
        if event.mimeData().hasUrls() and event.mimeData().urls()[0].scheme() == 'file':
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Обрабатывает событие отпускания перетаскиваемых объектов."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                self.load_from_file(file_path)

    def load_from_file(self, file_path: str):
        try:
            self.config = ParserConfig.load(file_path)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при загрузке конфигурации:\n{e}')
            return

        self.ui.fileInputLine.setText(file_path)

        self.about = ConfigAbout()
        self.about.ui.title.setText(self.config.title)
        self.about.ui.version.setText(self.config.version)
        self.about.ui.authorName.setText(self.config.author)
        self.about.ui.soursesNames.setText('; '.join(self.config.accepted_sources))

        for prop_group in self.config.property_groups:
            self.about.ui.scrollAreaWidgetContents.layout().addWidget(ConfigGroupInfo(prop_group))

        # Добавляем логику конфига
        config_layout = self.ui.fileDataContents.layout()
        config_layout.addWidget(self.about)


class ConfigAbout(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_configAbout()
        self.ui.setupUi(self)


class ConfigGroupInfo(QWidget):
    def __init__(self, prop_group: PropertyGroup, parent=None):
        super().__init__(parent)

        self.ui = Ui_configInfo()
        self.ui.setupUi(self)

        self.prop_group = prop_group

        self.ui.Name.setTitle(prop_group.name)

        for prop in prop_group.properties:
            self.ui.Fields.addItem(prop.name)

        # self.resize(QSize(200, 300))
        # self.sizePolicy().setHorizontalPolicy(QSizePolicy.Policy.Fixed)
        # self.ui.Name.sizePolicy().setHorizontalPolicy(QSizePolicy.Policy.Fixed)
