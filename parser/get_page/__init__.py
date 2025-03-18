import asyncio
import logging
from typing import List, Optional

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from datatype._classes import PageResult


class PageExtractor:
    """
    Класс для асинхронного анализа веб-страниц с использованием Selenium.

    :val patterns: Список регулярных паттернов для поиска на странице.
    :val headless: Флаг работы браузера в безголовом режиме.
    :val driver_path: Путь к исполняемому файлу драйвера Chrome.
    :val logger: Объект логгера для записи логов.
    """

    _instance = None
    _lock = asyncio.Lock()

    patterns: List[str]
    driver: Optional[async_playwright]
    browser: Optional[Browser]
    context: Optional[BrowserContext]
    # window: Optional[gw.BaseWindow]
    logger: Optional[logging.Logger]

    def __init__(
            self,
            _logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Инициализирует PageExtractor с заданными параметрами.
        """
        self.logger = _logger or logging.getLogger(__name__)

    async def _initialize_driver(self) -> None:
        """
        Инициализирует WebDriver с заданными опциями.
        """
        self.driver = await async_playwright().start()
        self.browser = await self.driver.chromium.launch(headless=False)
        self.context = await self.browser.new_context()

        # Thread(target=lambda x: asyncio.run(ww(x)), args=(self.context,)).start()

        await self.context.new_page()
        # gw.getActiveWindow().minimize()
        self.logger.debug("WebDriver инициализирован.")

    @classmethod
    async def init(cls, _logger: Optional[logging.Logger] = None) -> 'PageExtractor':
        """
        Асинхронно инициализирует PageExtractor.
        """
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = PageExtractor(_logger=_logger)
                    await cls._instance._initialize_driver()
                    cls._instance.logger.debug("PageExtractor инициализирован.")
        return cls._instance

    @classmethod
    async def get(cls, url: str) -> PageResult:
        """
        Асинхронно получает веб-страницу по указанному URL.
        """
        if not cls._instance:
            await cls.init()

        instance: PageExtractor = cls._instance
        page: Page = await instance.context.new_page()

        instance.logger.debug(f"Запрашивается веб-страница: {url}")

        # gw.getActiveWindow().minimize()

        await page.goto(url)
        await page.wait_for_load_state()
        if 'вы не робот' in (await page.content()).lower():
            while 'вы не робот' in (await page.title()).lower():
                await asyncio.sleep(2)
            await asyncio.sleep(2)
            await page.reload()
            await asyncio.sleep(2)

        instance.logger.info(f"Получена веб-страница: {url}")

        title = await page.title()
        content = await page.content()
        await page.close()

        return PageResult(url=url, content=content, title=title)

    @classmethod
    async def close(cls) -> None:
        """
        Закрывает WebDriver.
        """
        instance: PageExtractor = cls._instance
        await instance.context.close()
        await instance.browser.close()
        await instance.driver.stop()
        instance.logger.debug("WebDriver закрыт.")
        del instance
        cls._instance = None


async def main() -> None:
    """
    Основная асинхронная функция для запуска анализа веб-страниц.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)

    await PageExtractor.init(_logger=logger)
    urls = [
        "https://market.yandex.ru/product--pentium-g4400/12874524",
        "https://market.yandex.ru/product--protsessor-intel-core-i3-12100f-lga1700-4-x-3300mhz-oem/1497301526",
        "https://market.yandex.ru/product--core-i3-12100f/1497301526?sku=101556128769&uniqueId=1499763&do-waremd5=vy1tbMTtKhJ1lfsw6aOp3Q&cpc=vUynCLqrgPKDLduJkd5bHKOdIvHVpwxZfGu-95XMslakFEfw7oyaqpUydiGl4W8Wraktc07CHH3Gvmqid4-H9_MI3gvWui-OuYKrcqDn5gBBpUVlMj-Bq6dlu-ww9Ge6xeF26WdQd8-TXzYzng0JE5B7gVEZdKZUFpLo9WDIbiCq3X25oVjlZZ09o6fjjZ7-IGrUIBixWTiv6GQ64v6YRw-nzFG87yLtbDIBWtcTHKLJFXvpNN8BH7F_BS5WtaNYqfnFQYQ6u_yhRdXnH-aJyO_2UqMXu_QlcuY3uF_7z8qg1pw_1K6gKIvxrMtwj6vuBAGtunVIw1FPKcpN0uVkmTa4fn2xH-an3BNy6VLS6rO-chkztsWyZzLd9hTnz1w8GhNztArZuUSqQvGb1R_k-bgsej2dM2c-AmDvnOmse49r1xPNsyUdCJrxoPEJ0eEAU0uWKnF70dmei7fBlQJJiQ%2C%2C&nid=26912730",
        "https://market.yandex.ru/product--ryzen-5-7600x3d/896898214?sku=103675341024&uniqueId=182563203&do-waremd5=vQL0rTFItXoZnb3Q-D3opg&sponsored=1&cpc=vUynCLqrgPI6HGZg42oz3w9JbWB0_DwScrxx-tXqcFI21Zmsl6RiRc6C3MwkwKk-6ra9cOXiHPOj2BcADk1B9L3nwbIBmwTrdhoG6Fzjys7Mij2kJwhZuOFeTxuy54kzDAf7Pel8ZrsgTqeFk2wdCLokV1dCc2QGd6EU13yj5XuHZj1kIWnKvcrHNn_6Wsq1yg1-3c4o2zCSdehAhnEkGimk_4d645Wlh1cfCCGK-hvZC_GYHOlEpHulHByDRW9IXlkWJAvOhWZ5fDRyWPSSR5I3OvFkAzznQK3WCNlA35VHWingsiOYGzLG_MV0zE7sBg10z0vimSLQFg-T5z8DrfjjUeVMR16dlpF5pCceUhCMDjOQ9Xjvf5zC1b12CwZKTW1uMf3qc49PaGamopoobkbmA9FpgIpu98QU_GP9U4OchnEgYObZokYEs_hsS5_rBz-ggfv71BjNQzSj5m1yEJdtmJUnO9q9dufYUEhtGTofXdpjvvVyiENXPxDolKfgM5gqonqvsQD2knAspsqxLIpgv3U4YjLoPh7zygqPm_F5Rh0ma2PuHwrONIg0KUqcBO-vwotiMQjRZAQPNEwY6sYjekrJQuAJCxwQRBHyCCZFqeIIRsWC97P8ty9YaC9c&nid=26912730"
    ]

    print(*urls, sep="\n")

    bunch = [PageExtractor.get(url) for url in urls]

    print(*bunch, sep="\n")

    pages = await asyncio.gather(*bunch)

    print(*pages, sep="\n")
    await asyncio.sleep(3)
    await PageExtractor.close()


if __name__ == "__main__":
    asyncio.run(main())
