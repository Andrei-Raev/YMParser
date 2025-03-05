from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class PropertyResult:
    name: str
    value: Any
    type: "DataType"

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'value': self.value,
            'type': self.type.title if self.type else None
        }


@dataclass
class ParseResult:
    """Класс для хранения результатов парсинга."""
    name: str
    table_name: str
    source: str
    properties: list[PropertyResult]

    def to_dict(self) -> dict:
        """
        Преобразует результат парсинга в словарь.

        :return: Словарь результатов.
        """
        return {
            'name': self.name,
            'table_name': self.table_name,
            'source': self.source,
            'properties': [
                prop.to_dict() for prop in self.properties
            ]
        }

    @classmethod
    def empty(cls) -> "ParseResult":
        return ParseResult(name="empty", table_name="empty", source="empty", properties=[])

    @property
    def rate(self) -> float:
        """
        Вычисляет рейтинг результатов парсинга.

        :return: Рейтинг.
        """
        return sum(prop.value is not None for prop in self.properties) / len(self.properties)


class DataType:
    """
    Перечисление типов данных для форматирования.

    :var title: Название типа.
    :var decoder: Функция декодирования строки в тип.
    :var to_excel: Функция кодирования типа в строку.
    """
    title: str
    decoder: Callable[[str], Any]
    to_excel: Callable[[Any], str]

    def __init__(self, title: str, decoder: Callable[[str], Any], to_excel: Callable[[Any], str]) -> None:
        self.title = title
        self.decoder = decoder
        self.to_excel = to_excel

    def __str__(self) -> str:
        return f'{self.title.upper()}'

    def decode(self, x: str) -> Any:
        return self.decoder(x)

    def encode(self, x: Any) -> str:
        return self.to_excel(x)

    def __call__(self, x: str) -> Any:
        return self.decode(x)
