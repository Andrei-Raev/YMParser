from typing import Optional

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QSizePolicy

from cache.horizontalDualField import Ui_HorizontalDualField


class OneLineWidget(QWidget):
    def __init__(self, title: str, value: Optional[QWidget] = None):
        super().__init__()
        self.ui = Ui_HorizontalDualField()
        self.ui.setupUi(self)

        self.ui.label.setText(title)
        if value is not None:
            value.setParent(self.ui.valueLayout.parent())
            self.ui.valueLayout.layout().addWidget(value)
            print(self.ui.valueLayout.widget().findChildren(QWidget))

    @property
    def widgets(self) -> list[QWidget]:
        return self.ui.valueLayout.layout().findChildren(QWidget)

    @property
    def widget(self) -> QWidget:
        if len(self.widgets) != 1:
            raise Warning('Виджетов более одного')
        return self.widgets[0]

    @widget.setter
    def widget(self, value: QWidget):
        """
        Заменяет виджет

        :param value: новый виджет
        """
        _all_widgets = self.ui.valueLayout.findChildren(QWidget)
        print(_all_widgets)
        for widget in _all_widgets:
            self.ui.valueLayout.removeWidget(widget)
        value.setParent(self.ui.valueLayout.widget())
        self.ui.valueLayout.addWidget(value)

    @property
    def title(self) -> str:
        return self.ui.label.text()

    @title.setter
    def title(self, value: str):
        self.ui.label.setText(value)

    def add_widget(self, widget: QWidget):
        self.ui.valueLayout.addWidget(widget)
