import asyncio
import json
import logging
import re
import zipfile
from dataclasses import dataclass
from io import TextIOWrapper
from typing import Any, List, Optional, Pattern

from aiohttp import ClientSession

import datatype

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


@dataclass
class Property:
    """Класс, представляющий отдельное свойство для парсинга."""
    name: str
    type: datatype.DataType
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
            return self.type(value)
        except ValueError as e:
            logger.error("Ошибка преобразования значения '%s' к типу '%s': %s", value, self.type, e)
            return None


@dataclass
class PropertyGroup:
    """Класс, представляющий группу свойств для парсинга."""
    name: str
    table_name: str
    properties: List[Property]

    @classmethod
    def from_config(cls, config: dict, table_name: str = None) -> 'PropertyGroup':
        """
        Создает экземпляр PropertyGroup из конфигурационного словаря.

        :param config: Словарь конфигурации.
        :param table_name: Имя таблицы.
        :return: Экземпляр PropertyGroup.
        """
        if not table_name:
            table_name = config['table_name']

        properties = [
            Property(
                name=prop['name'],
                type=datatype.get_datatype(prop['type']),
                signatures=[re.compile(sig) for sig in prop['signatures']]
            )
            for prop in config.get('properties', [])
        ]
        return cls(name=config['name'], table_name=table_name, properties=properties)

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
                    'table_name': self.table_name,
                    'type': prop.type.title,
                    'signatures': [sig.pattern for sig in prop.signatures]
                }
                for prop in self.properties
            ]
        }

    def pars(self, html: str) -> "ParseResult":
        return ParseResult(
            name=self.name,
            properties=[PropertyResult(name=prop.name, value=prop.match(html), type=prop.type)
                        for prop in self.properties]
        )


@dataclass
class PropertyResult:
    name: str
    value: Any
    type: datatype.DataType

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'value': self.value,
            'type': self.type.title
        }


@dataclass
class ParseResult:
    """Класс для хранения результатов парсинга."""
    name: str
    properties: list[PropertyResult]

    def to_dict(self) -> dict:
        """
        Преобразует результат парсинга в словарь.

        :return: Словарь результатов.
        """
        return {
            'name': self.name,
            'properties': [
                prop.to_dict() for prop in self.properties
            ]
        }

    @classmethod
    def empty(cls) -> "ParseResult":
        return ParseResult(name="empty", properties=[])

    @property
    def rate(self) -> float:
        """
        Вычисляет рейтинг результатов парсинга.

        :return: Рейтинг.
        """
        return sum(prop.value is not None for prop in self.properties) / len(self.properties)


class WebPageParser:
    """Класс для парсинга веб-страниц с использованием регулярных выражений."""

    _session: Optional[ClientSession] = None
    _property_groups: List[PropertyGroup] = []

    def __init__(self, _logger: Optional[logging.Logger] = logger) -> None:
        """
        Инициализирует WebPageParser.

        :param _logger: Объект логгера. Если не указан, используется глобальный логгер.
        """
        self.logger = _logger
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

    # @classmethod
    # def load_config(cls, file_path: str) -> 'PropertyGroup':
    #     """
    #     Загружает конфигурацию группы свойств из файла.
    #
    #     :param file_path: Путь к конфигурационному файлу.
    #     :return: Экземпляр PropertyGroup.
    #     """
    #     with open(file_path, 'r', encoding='utf-8') as file:
    #         config = json.load(file)
    #         logger.debug("Конфигурация загружена из файла: %s", file_path)
    #         return PropertyGroup.from_config(config)
    @classmethod
    def from_configfile(cls, file_path: str) -> 'WebPageParser':
        c = cls()
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for json_file in zip_ref.namelist():
                with zip_ref.open(json_file) as file:
                    with TextIOWrapper(file, encoding='utf-8') as text_file:
                        c.add_prop_from_config(json.load(text_file))
        return c

    def add_prop_from_config(self, config: dict) -> 'WebPageParser':
        self._property_groups.append(PropertyGroup.from_config(config))
        return self

    def to_configfile(self, file_path: str) -> 'WebPageParser':
        """
        Сохраняет конфигурацию группы свойств в файл.

        :param group: Экземпляр PropertyGroup.
        :param file_path: Путь к файлу для сохранения.
        :return: Ссылка на текущий экземпляр WebPageParser.
        """
        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True, compresslevel=9) as zip_ref:
            for prop in self._property_groups:
                # Открываем файл внутри архива в режиме записи ('w')
                with zip_ref.open(prop.table_name, 'w') as file_bin:
                    # Оборачиваем бинарный поток в текстовый для записи JSON
                    with TextIOWrapper(file_bin, encoding='utf-8') as file_text:
                        conf = prop.to_config()
                        # Запись конфигурации в файл
                        json.dump(conf, file_text, ensure_ascii=False, indent=4)

        self.logger.debug("Конфигурация сохранена в файл: %s", file_path)
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
                    return ParseResult.empty()
                text = await response.text()
                results = [group.pars(text) for group in self._property_groups]
                return sorted(results, key=lambda x: x.rate, reverse=True)[0]
        except Exception as e:
            self.logger.error("Ошибка при парсинге страницы %s: %s", url, e)
            return ParseResult.empty()

    # def _extract_properties(self, text: str) -> dict:
    #     """
    #     Извлекает свойства из текста страницы.
    #
    #     :param text: Текст веб-страницы.
    #     :return: Словарь с результатами парсинга.
    #     """
    #     parsed_data = {}
    #     for group in self._property_groups:
    #         self.logger.debug("Парсинг группы свойств: %s", group.name)
    #         for prop in group.properties:
    #             if prop.name not in parsed_data:
    #                 value = prop.match(text)
    #                 if value is not None:
    #                     parsed_data[prop.name] = value
    #     self.logger.info("Парсинг завершен. Найденные данные: %s", parsed_data)
    #     return parsed_data


# Пример использования
if __name__ == "__main__":
    async def main():
        parser = WebPageParser()
        #бренд_pattern = r'"brand":"([^"]+)"'
        # сокет_pattern = r'{"value":"([^"]+)","transition":{[^}]+},"type":"catalog"},"name":"Сокет"}]}'
        # тип_памяти_pattern = r'{"value":"([^"]+)","transition":{"params":{[^}]+},"type":"catalog"},"name":"Тип памяти"}'
        # количество_ядер_pattern = r'"Ядро процессора"},{"value":"(\d+)\s*шт\."'
        # количество_потоков_pattern = r'"name":"Количество потоков","value":"(\d+)"'
        # техпроцесс_pattern = r'"value":"(\d+)\s*нм"'
        # частота_pattern = r'"value":"(\d+)\s*МГц"'
        # tdp_pattern = r'"value":"(\d+)\s*Вт"'
        # Загрузка конфигурации из файла
        group = PropertyGroup('Процессор', 'cpu', [
            Property('Производитель', datatype.STRING, [re.compile(r'"brand":"([^"]+)"')]),
            Property('Сокет', datatype.STRING, [re.compile(r'{"value":"([^"]+)","transition":{[^}]+},"type":"catalog"},"name":"Сокет"}]}')]),
            Property('Тип памяти', datatype.STRING, [re.compile(r'{"value":"([^"]+)","transition":{"params":{[^}]+},"type":"catalog"},"name":"Тип памяти"}')]),
        ])

        parser.add_property_group(group)
        parser.to_configfile('cfg.zip')

        # Закрытие сессии
        await WebPageParser.close_session()

    asyncio.run(main())
