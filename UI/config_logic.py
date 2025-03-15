from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QFileDialog, QMessageBox

from UI._utils import StatusbarVariants
from UI.cache.configInfo import Ui_configInfo
from cache.config import Ui_Config
from cache.configAbout import Ui_configAbout
from datatype import ParserConfig, PropertyGroup


def colorize_sources(source: str):
    if source.lower().strip() in ['я.маркет', 'маркет', 'яндекс', 'яндекс.маркет', 'яндекс маркет']:
        return "<font color='#FF5226'>Я</font><font color='#A48E00'>.маркет</font>"
    elif source.lower().strip() in ['ozon', 'озон', 'оз', 'oz', 'ozon.ru']:
        return "<font color='#005BFF'>Ozon</font>"
    elif source.lower().strip() in ['wildberries', 'wild', 'wildberries.ru', 'wb']:
        return "<font color='#6612D3'>WildBerries</font>"
    elif source.lower().strip() in ['лавка', 'я.лавка', 'яндекс.лавка', 'яндекс лавка']:
        return "<font color='#FF5226'>Я</font><font color='#01ADFF'>.лавка</font>"
    return source


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

        self.parent().setStatusTip(StatusbarVariants.need_config)




    def select_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        # file_dialog.setNameFilter('ZIP (*.zip)')

        if file_dialog.exec():
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
        self.parent().setStatusTip(StatusbarVariants.config_loading)

        del self.config
        self.config = None

        if self.about is not None:
            self.about.close()
        del self.about
        self.about = None
        try:
            self.config = ParserConfig.load(file_path)
        except Exception as e:
            self.parent().setStatusTip(StatusbarVariants.config_loading_error)
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при загрузке конфигурации:\n{e}')
            return

        self.ui.fileInputLine.setText(file_path)

        self.about = ConfigAbout()
        self.about.ui.title.setText(self.config.title)
        self.about.ui.version.setText(self.config.version)
        self.about.ui.authorName.setText(self.config.author)

        self.about.ui.soursesNames.setText('; '.join(map(colorize_sources, self.config.accepted_sources)))

        for prop_group in self.config.property_groups:
            self.about.ui.scrollAreaWidgetContents.layout().addWidget(ConfigGroupInfo(prop_group))

        # Добавляем логику конфига
        config_layout = self.ui.fileDataContents.layout()
        config_layout.addWidget(self.about)

        self.parent().setStatusTip(StatusbarVariants.config_loaded)



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
