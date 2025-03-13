from dataclasses import dataclass, asdict
from typing import Any

from datatype._utils import DataType


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
    source: str
    properties: list[PropertyResult]

    def to_dict(self) -> dict:
        """
        Преобразует результат парсинга в словарь.

        :return: Словарь результатов.
        """
        return {
            'name': self.name,
            'source': self.source,
            'properties': [
                prop.to_dict() for prop in self.properties
            ]
        }

    @classmethod
    def empty(cls) -> "ParseResult":
        return ParseResult(name="", source="", properties=[])

    @property
    def rate(self) -> float:
        """
        Вычисляет рейтинг результатов парсинга.

        :return: Рейтинг.
        """
        return sum(prop.value is not None for prop in self.properties) / len(self.properties)


@dataclass
class PageResult:
    """
    Класс для хранения страницы.

    :var url: URL страницы.
    :var content: Содержимое страницы.
    """
    url: str
    title: str
    content: str

    def to_dict(self) -> dict:
        """Преобразует объект в словарь."""
        return asdict(self)

    def __str__(self) -> str:
        return f'PageResult(url={self.url}, title={self.title}, content={self.content[:100]}...)'
