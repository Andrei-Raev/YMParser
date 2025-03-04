import re
import json
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, List, Optional, Pattern, Union
from enum import Enum
from aiohttp import ClientSession

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


class PropertyType(Enum):
    """Перечисление типов свойств."""
    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"


@dataclass
class Property:
    """Класс, представляющий отдельное свойство для парсинга."""
    name: str
    type: PropertyType
    signatures: List[Pattern]

    def match(self, text: str) -> Optional[Any]:
        """
        Ищет значение свойства в тексте с использованием сигнатур.

        :param text: Текст для поиска.
        :return: Найденное значение с приведением к указанному типу или None.
        """
        for pattern in self.signatures:
            match = pattern.search(text)
            if match:
                value = match.group(1)
                logger.debug("Найдено совпадение для свойства '%s': %s", self.name, value)
                return self._convert_type(value)
        logger.debug("Совпадение для свойства '%s' не найдено.", self.name)
        return None

    def _convert_type(self, value: str) -> Any:
        """
        Преобразует строковое значение в указанный тип.

        :param value: Строковое значение.
        :return: Значение нужного типа.
        """
        try:
            if self.type == PropertyType.STRING:
                return value
            elif self.type == PropertyType.INTEGER:
                return int(value)
            elif self.type == PropertyType.FLOAT:
                return float(value)
            elif self.type == PropertyType.BOOLEAN:
                return value.lower() in ('true', '1', 'yes')
        except ValueError as e:
            logger.error("Ошибка преобразования значения '%s' к типу '%s': %s", value, self.type, e)
            return None


@dataclass
class PropertyGroup:
    """Класс, представляющий группу свойств для парсинга."""
    name: str
    properties: List[Property]

    @classmethod
    def from_config(cls, config: dict) -> 'PropertyGroup':
        """
        Создает экземпляр PropertyGroup из конфигурационного словаря.

        :param config: Словарь конфигурации.
        :return: Экземпляр PropertyGroup.
        """
        properties = [
            Property(
                name=prop['name'],
                type=PropertyType(prop['type']),
                signatures=[re.compile(sig) for sig in prop['signatures']]
            )
            for prop in config.get('properties', [])
        ]
        return cls(name=config['name'], properties=properties)

    def to_config(self) -> dict:
        """
        Преобразует текущую конфигурацию группы свойств в словарь.

        :return: Словарь конфигурации.
        """
        return {
            'name': self.name,
            'properties': [
                {
                    'name': prop.name,
                    'type': prop.type.value,
                    'signatures': [sig.pattern for sig in prop.signatures]
                }
                for prop in self.properties
            ]
        }


@dataclass
class ParseResult:
    """Класс для хранения результатов парсинга."""
    data: dict

    def to_dict(self) -> dict:
        """
        Преобразует результат парсинга в словарь.

        :return: Словарь результатов.
        """
        return self.data


class WebPageParser:
    """Класс для парсинга веб-страниц с использованием регулярных выражений."""

    _session: Optional[ClientSession] = None
    _property_groups: List[PropertyGroup] = []

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """
        Инициализирует WebPageParser.

        :param logger: Объект логгера. Если не указан, используется глобальный логгер.
        """
        self.logger = logger or logger
        self._initialize()

    def _initialize(self) -> None:
        """Выполняет начальную инициализацию парсера."""
        self._property_groups = []
        self.logger.debug("Инициализация парсера завершена.")

    @classmethod
    async def _get_session(cls) -> ClientSession:
        """
        Получает или создает асинхронную сессию для HTTP-запросов.

        :return: Экземпляр ClientSession.
        """
        if cls._session is None:
            cls._session = ClientSession()
            logger.debug("Создана новая HTTP-сессия.")
        return cls._session

    @classmethod
    async def close_session(cls) -> None:
        """Закрывает асинхронную сессию."""
        if cls._session:
            await cls._session.close()
            cls._session = None
            logger.debug("HTTP-сессия закрыта.")

    def add_property_group(self, group: PropertyGroup) -> 'WebPageParser':
        """
        Добавляет группу свойств для парсинга.

        :param group: Экземпляр PropertyGroup.
        :return: Ссылка на текущий экземпляр WebPageParser.
        """
        self._property_groups.append(group)
        self.logger.info("Добавлена группа свойств: %s", group.name)
        return self

    @classmethod
    def load_config(cls, file_path: str) -> 'PropertyGroup':
        """
        Загружает конфигурацию группы свойств из файла.

        :param file_path: Путь к конфигурационному файлу.
        :return: Экземпляр PropertyGroup.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
            logger.debug("Конфигурация загружена из файла: %s", file_path)
            return PropertyGroup.from_config(config)

    def save_config(self, group: PropertyGroup, file_path: str) -> 'WebPageParser':
        """
        Сохраняет конфигурацию группы свойств в файл.

        :param group: Экземпляр PropertyGroup.
        :param file_path: Путь к файлу для сохранения.
        :return: Ссылка на текущий экземпляр WebPageParser.
        """
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(group.to_config(), file, ensure_ascii=False, indent=4)
            self.logger.debug("Конфигурация группы '%s' сохранена в файл: %s", group.name, file_path)
        return self

    async def parse(self, url: str) -> ParseResult:
        """
        Парсит веб-страницу по указанному URL и извлекает значения свойств.

        :param url: URL веб-страницы для парсинга.
        :return: Объект ParseResult с результатами парсинга.
        """
        session = await self._get_session()
        try:
            async with session.get(url) as response:
                self.logger.info("Запрос к %s завершен с статусом %s", url, response.status)
                if response.status != 200:
                    self.logger.error("Не удалось загрузить страницу: %s", url)
                    return ParseResult(data={})
                text = await response.text()
                result = self._extract_properties(text)
                return ParseResult(data=result)
        except Exception as e:
            self.logger.error("Ошибка при парсинге страницы %s: %s", url, e)
            return ParseResult(data={})

    def _extract_properties(self, text: str) -> dict:
        """
        Извлекает свойства из текста страницы.

        :param text: Текст веб-страницы.
        :return: Словарь с результатами парсинга.
        """
        parsed_data = {}
        for group in self._property_groups:
            self.logger.debug("Парсинг группы свойств: %s", group.name)
            for prop in group.properties:
                if prop.name not in parsed_data:
                    value = prop.match(text)
                    if value is not None:
                        parsed_data[prop.name] = value
        self.logger.info("Парсинг завершен. Найденные данные: %s", parsed_data)
        return parsed_data


# Пример использования
if __name__ == "__main__":
    async def main():
        parser = WebPageParser()

        # Загрузка конфигурации из файла
        cpu_config = WebPageParser.load_config('cpu_config.json')
        parser.add_property_group(cpu_config)

        # Парсинг веб-страницы
        url = 'https://example.com/product-page'
        result = await parser.parse(url)

        # Вывод результатов
        print(result.to_dict())

        # Закрытие сессии
        await WebPageParser.close_session()


    asyncio.run(main())
