import asyncio
import logging
import threading
import traceback
from typing import Optional

import pyperclip

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
    _config: Optional[ParserConfig] = None

    def __init__(self, config: Optional[ParserConfig] = None, _logger: Optional[logging.Logger] = logger) -> None:
        """
        Инициализирует WebPageParser.

        :param _logger: Объект логгера. Если не указан, используется глобальный логгер.
        """
        self.logger = _logger
        self._config = config
        self._initialize()

    def _initialize(self) -> None:
        """Выполняет начальную инициализацию парсера."""
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

    # def add_property_group(self, group: PropertyGroup) -> 'WebPageParser':
    #     """
    #     Добавляет группу свойств для парсинга.
    #
    #     :param group: Экземпляр PropertyGroup.
    #     :return: Ссылка на текущий экземпляр WebPageParser.
    #     """
    #     self._property_groups.append(group)
    #     self.logger.info("Добавлена группа свойств: %s", group.name)
    #     return self

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

            results = [group.pars(data.content, clean_url(url)) for group in self._config.property_groups]

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
        config = ParserConfig.load('cfg.zip')
        parser = WebPageParser(config=config)
        await parser.start_watch()


    asyncio.run(main())
