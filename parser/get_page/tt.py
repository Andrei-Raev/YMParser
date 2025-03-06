import asyncio
import logging
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from enum import Enum
from dataclasses import dataclass, asdict
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class PageAnalysisResult:
    url: str
    content: str

    def to_dict(self) -> dict:
        return asdict(self)


class SeleniumAnalyzer:
    """
    Класс для асинхронного анализа веб-страниц с использованием Selenium.

    :val patterns: Список регулярных паттернов для поиска на странице.
    :val headless: Флаг работы браузера в безголовом режиме.
    :val driver_path: Путь к исполняемому файлу драйвера Chrome.
    :val logger: Объект логгера для записи логов.
    """

    patterns: List[str]
    headless: bool
    driver_path: str
    logger: Optional[logging.Logger]

    def __init__(
            self,
            headless: bool = False,
            driver_path: str = './drivers/chromedriver.exe',
            logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Инициализирует SeleniumAnalyzer с заданными параметрами.
        """
        self.headless = headless
        self.driver_path = driver_path
        self.logger = logger or logging.getLogger(__name__)
        self._initialize_driver()

    def _initialize_driver(self) -> None:
        """
        Инициализирует WebDriver с заданными опциями.
        """
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        self.driver_service = ChromeService(executable_path=self.driver_path)
        self.driver = webdriver.Chrome(service=self.driver_service, options=options)
        self.driver.minimize_window()
        self.logger.debug("WebDriver инициализирован.")

    async def fetch_page(self, url: str) -> PageAnalysisResult:
        """
        Асинхронно загружает страницу и анализирует её содержимое.

        :param url: URL веб-страницы для анализа.
        :return: Результат анализа страницы.
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._load_and_analyze, url)
        return result

    def _load_and_analyze(self, url: str) -> PageAnalysisResult:
        """
        Загружает страницу и выполняет анализ синхронно.

        :param url: URL веб-страницы для анализа.
        :return: Результат анализа страницы.
        """
        self.logger.info(f"Загрузка страницы: {url}")
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time_loaded = time.time()
        content = self.driver.find_element(By.TAG_NAME, "body").text
        self.logger.info(f"Содержимое страницы загружено за {time.time() - time_loaded:.2f} секунд.")
        print(content)
        # patterns_found = self._search_patterns(content)
        # if not patterns_found:
        #     self._handle_additional_verification()
        # asyncio.run_coroutine_threadsafe(self._return_result(url, content), asyncio.get_event_loop())
        return PageAnalysisResult(url=url, content=content)

    # def _search_patterns(self, content: str) -> bool:
    #     """
    #     Ищет заданные паттерны в содержимом страницы.
    #
    #     :param content: Текстовое содержимое страницы.
    #     :return: True, если паттерны найдены, иначе False.
    #     """
    #     for pattern in self.patterns:
    #         if re.search(pattern, content):
    #             self.logger.info(f"Найден паттерн: {pattern}")
    #             return True
    #     return False
    #
    # def _handle_additional_verification(self) -> None:
    #     """
    #     Открывает браузерное окно на 30 секунд для дополнительной проверки пользователем.
    #     """
    #     self.logger.info("Требуется дополнительная проверка. Открытие окна браузера на 30 секунд.")
    #     options = Options()
    #     options.add_argument("--disable-headless")
    #     temp_driver = webdriver.Chrome(service=self.driver_service, options=options)
    #     temp_driver.get("about:blank")
    #     time.sleep(30)
    #     temp_driver.quit()
    #     self.logger.info("Дополнительная проверка завершена.")

    # async def _return_result(self, url: str, content: str, patterns_found: bool) -> None:
    #     """
    #     Возвращает результат анализа через 0.5 секунды после полной загрузки страницы.
    #
    #     :param url: URL проанализированной страницы.
    #     :param content: Текстовое содержимое страницы.
    #     :param patterns_found: Флаг наличия паттернов.
    #     """
    #     # await asyncio.sleep(.5)
    #     result = PageAnalysisResult(url=url, content=content, patterns_found=patterns_found)
    #     self.logger.info(f"Результат анализа: {result.to_dict()}")

    def close(self) -> None:
        """
        Закрывает WebDriver.
        """
        self.driver.quit()
        self.logger.debug("WebDriver закрыт.")

    @classmethod
    def factory(cls, headless: bool = False,
                driver_path: str = './drivers/chromedriver.exe') -> 'SeleniumAnalyzer':
        """
        Фабричный метод для создания экземпляра SeleniumAnalyzer.

        :param headless: Флаг работы браузера в безголовом режиме.
        :param driver_path: Путь к драйверу Chrome.
        :return: Экземпляр SeleniumAnalyzer.
        """
        return cls(headless=headless, driver_path=driver_path)


async def main() -> None:
    """
    Основная асинхронная функция для запуска анализа веб-страниц.
    """
    analyzer = SeleniumAnalyzer.factory()

    urls = [
        "https://market.yandex.ru/product--pentium-g4400/12874524?sku=100334386827&uniqueId=12704317&do-waremd5=v3g8KpEiHt8KOb0pV_pQqg&sponsored=1&cpc=Ptm_NSDKHoVg-ZvpfdCmOYXCmgc14_K8AYJ2m5txWoeCYNUHGg6uhg1Pd41vzosJcNvHG8wr7nYqmYOg2s5nbnq47MMmqjfwTTignKIlFdZRB6-lrwjc_5gpyumzzy84Kjl_8kX-6s49HqJw905Kf3H51GEqMA3IQz0pU0VJDExKajbYL8Q93Zd8NmjywIL1hKtf9Ski5hXAhOM_WBLYWU1iFMO6qnUhe3xLXu8Gnxb7tZrplKjLZFPWfLlDMq_xp36DBcGZzMLCcoUhZqhd4CV6DyyrSRZtzX_djpARtLThr4_Y4-8Lu8C493NV5EhJdSfaAjyaHRpnib9SppD1Q3O6ZvFA9NsuCGuV-ENMh2re0m95PWqYd98qnOOG9oXMQAnlCU8uf6_BOb3-ZhF6WO0FlIrx2iJylso-Uzu4hZwJ4bkqLOkVW9-lysOOkAaB-fQFuK6jNaCK5T9cr0Uj54Tffl02pFzuaHa_mzJ0MuhxISSNkpjWRos46z26cSMRNUnZoZXnePZCeWzrSKHCGHLOm-0hBl1shjZFuOCxSk2wUKjS0BRgA3VlUkMm0MpS0jRdPa8aiglIDs2prYlTjpQvDV9wWVCTUZCdS3vxlfxyuaweTqqgfg%2C%2C",
    ]

    tasks = [analyzer.fetch_page(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, PageAnalysisResult):
            logger.info(f"URL: {result.url}")
        else:
            logger.error(f"Ошибка при обработке: {result}")

    analyzer.close()


if __name__ == "__main__":
    asyncio.run(main())
