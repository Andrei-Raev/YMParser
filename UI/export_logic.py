from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QPushButton, QLabel

from cache.exportLogic import Ui_ExportLogic
from one_line_widget import OneLineWidget


class ExportLogic(QWidget):
    excel_status: OneLineWidget
    excel_table_status: OneLineWidget

    connect_excel: QPushButton

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ExportLogic()
        self.ui.setupUi(self)

        self.excel_status = OneLineWidget("Подключение Excel", QLabel("<font color='red'>Отсутствует</font>"))
        self.ui.excel_connect.layout().addWidget(self.excel_status)

        self.connect_excel = QPushButton("Подключить Excel")
        self.connect_excel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.connect_excel.clicked.connect(self.connect_excel_func)

        self.excel_table_status = OneLineWidget("Состояние таблицы Excel", self.connect_excel)
        self.ui.excel_table_status.layout().addWidget(self.excel_table_status)

    def connect_excel_func(self):
        self.excel_status.widget = QLabel("<font color='green'>Подключено</font>")
