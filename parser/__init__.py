import asyncio
import json
import logging
import re
import threading
import traceback
import zipfile
from dataclasses import dataclass
from io import TextIOWrapper
from typing import List, Optional, Pattern

import pyperclip

import datatype
from datatype import *
from parser._utils import clean_url
from parser.get_page import PageExtractor

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

    def match(self, text: str) -> Optional:
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

    def _convert_type(self, value: str):
        """
        Преобразует строковое значение в указанный тип.

        :param value: Строковое значение.
        :return: Значение нужного типа.
        """
        if self.type is None:
            return value

        if value is None:
            return None

        try:
            return self.type(value)
        except (ValueError, TypeError) as e:
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
            'table_name': self.table_name,
            'properties': [
                {
                    'name': prop.name,
                    'type': prop.type.title,
                    'signatures': [sig.pattern for sig in prop.signatures]
                }
                for prop in self.properties
            ]
        }

    def pars(self, html: str, source: str) -> "ParseResult":
        _properties = []
        for prop in self.properties:
            _properties.append(PropertyResult(name=prop.name, value=prop.match(html), type=prop.type))

        return ParseResult(
            name=self.name,
            properties=_properties,
            table_name=self.table_name,
            source=source
        )


class Watchdog:
    _logger: logging.Logger
    _watchdog: Optional[asyncio.Task]
    _web_parser: "WebPageParser"

    def __init__(self, web_parser: "WebPageParser", _logger: Optional[logging.Logger] = logger):
        self._logger = _logger
        self._watchdog = None
        if not isinstance(web_parser, WebPageParser):
            raise TypeError("web_parser должен быть экземпляром WebPageParser")
        self._web_parser = web_parser

    async def start(self, background: bool = False):
        if self._watchdog:
            self._watchdog.cancel()

        if background:
            self._watchdog = asyncio.create_task(self._watch(), name="watchdog")
            self._logger.info("Наблюдение за буфером обмена запущено в фоновом режиме.")
        else:
            self._logger.info("Наблюдение за буфером обмена запущено в интерактивном режиме.")
            await self._watch()

    async def _watch(self):
        _last_val = pyperclip.paste()
        while True:
            await asyncio.sleep(.5)
            val = pyperclip.paste()
            if val != _last_val:
                self._logger.info("Новое значение в буфере обмена: %s", val)
                threading.Thread(target=self._parse, args=(asyncio.get_event_loop(), val)).start()
                _last_val = val

    def _parse(self, loop: asyncio.AbstractEventLoop, url: str) -> None:
        _res = asyncio.run_coroutine_threadsafe(self._web_parser.parse(url), loop=loop)  # self._web_parser.parse(url)
        # _res = asyncio.run(self._web_parser.parse(url))  # self._web_parser.parse(url)
        if _res:
            self._logger.info("Результат парсинга: %s", _res.result().to_dict())


class WebPageParser:
    """Класс для парсинга веб-страниц с использованием регулярных выражений."""

    # _session: Optional[ClientSession] = None
    _watchdog: Optional[Watchdog] = None
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
        self._watchdog = Watchdog(self)
        self.logger.debug("Инициализация парсера завершена.")

    # @classmethod
    # async def _get_session(cls) -> ClientSession:
    #     """
    #     Получает или создает асинхронную сессию для HTTP-запросов.
    #
    #     :return: Экземпляр ClientSession.
    #     """
    #     if cls._session is None:
    #         cls._session = ClientSession()
    #         logger.debug("Создана новая HTTP-сессия.")
    #     return cls._session

    # @classmethod
    # async def close_session(cls) -> None:
    #     """Закрывает асинхронную сессию."""
    #     if cls._session:
    #         await cls._session.close()
    #         cls._session = None
    #         logger.debug("HTTP-сессия закрыта.")

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

        :param file_path: Путь к файлу для сохранения.
        :return: Ссылка на текущий экземпляр WebPageParser.
        """
        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True, compresslevel=9) as zip_ref:
            for prop in self._property_groups:
                # Открываем файл внутри архива в режиме записи ('w')
                with zip_ref.open(prop.table_name + '.json', 'w') as file_bin:
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
        # headers = {
        #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
        #               'q=0.8,application/signed-exchange;v=b3;q=0.9',
        #     'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        #     'Connection': 'keep-alive',
        #     'Host': 'market.yandex.ru',
        #     'Sec-Fetch-Dest': 'document',
        #     'Sec-Fetch-Mode': 'navigate',
        #     'Sec-Fetch-Site': 'none',
        #     'Sec-Fetch-User': '?1',
        #     'Upgrade-Insecure-Requests': '1',
        #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
        #                   '83.0.4103.61 Safari/537.36',
        # }
        #
        # session = await self._get_session()
        try:
            # async with session.get(url, headers=headers) as response:
            #     self.logger.info("Запрос к %s завершен с статусом %s", url, response.status)
            #     if response.status != 200:
            #         self.logger.error("Не удалось загрузить страницу: %s", url)
            #         return ParseResult.empty()
            #     text = await response.text()
            #     with open('log.html', 'w', encoding='utf-8') as f:
            #         f.write(text.replace(r'"/', '"https://market.yandex.ru/'))
            data = await PageExtractor.get(url)

            results = [group.pars(data.content, clean_url(url)) for group in self._property_groups]

            return sorted(results, key=lambda x: x.rate, reverse=True)[0]
        except Exception as e:
            self.logger.error("Ошибка при парсинге страницы %s: %s номер строки %s", url, e, traceback.format_exc())
            return ParseResult.empty()

    async def start_watch(self, background: bool = False) -> None:
        """
        Запускает наблюдение за буфером обмена и парсинг веб-страниц.

        :param background: Флаг, указывающий, нужно ли запускать наблюдение в фоновом режиме.
        """
        await self._watchdog.start(background)


if __name__ == "__main__":
    async def main():
        parser = WebPageParser.from_configfile('cfg.zip')
        await parser.start_watch()


    asyncio.run(main())
