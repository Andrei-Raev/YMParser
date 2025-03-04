# excel_table_manager.py

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from functools import wraps
from typing import List

import pythoncom
import xlwings as xw

# Настройка логирования
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class DataType(Enum):
    """Перечисление типов данных для форматирования."""
    BOOLEAN = 'BOOLEAN'
    INTEGER = 'INTEGER'
    FLOAT = 'FLOAT'
    STRING = 'STRING'
    DATE = 'DATE'
    HZ = 'HZ'
    DPI = 'DPI'
    INCH = 'INCH'
    RUB = 'RUB'


def com_init(func):
    """
    Декоратор для инициализации и деинициализации COM.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        pythoncom.CoInitialize()
        try:
            return func(*args, **kwargs)
        finally:
            pythoncom.CoUninitialize()

    return wrapper


class _ExcelWorker:
    """
    Вспомогательный класс для выполнения всех COM-операций с Excel.
    Выполняется в отдельном потоке.
    """

    sheet: xw.Sheet

    @com_init
    def __init__(self, workbook_name: str, table_name: str) -> None:
        """
        Инициализирует подключение к книге и таблице Excel.

        :param workbook_name: Имя открытой книги Excel.
        :param table_name: Имя таблицы, созданной с помощью Ctrl+T.
        """
        self.workbook_name = workbook_name
        try:
            self.workbook = xw.books[self.workbook_name]
            logger.info(f'Подключено к книге: {self.workbook_name}')
        except IndexError:
            raise Exception(f'Книга {self.workbook_name} не найдена.')

        self.table_name = table_name
        try:
            sheets = self.workbook.sheets
            for sheet in sheets:
                self.table = sheet.api.ListObjects(table_name)
                if self.table:
                    self.sheet = xw.Sheet(sheet)
                    logger.info(f'Таблица {self.table_name} найдена на листе: {sheet.name}.')
                    break

            if not self.table:
                raise Exception(f'Таблица {self.table_name} не найдена.')
        except Exception as e:
            logger.error(f'Ошибка при поиске таблицы: {e}')
            exit(1)
            # raise Exception(f'Таблица {self.table_name} не найдена.')

    # def _apply_formatting(self, row: xw.Range) -> None:
    #     """Применяет стандартное форматирование к строке."""
    #     try:
    #         row.api.Font.Color = 0  # Черный текст
    #         row.api.Interior.Color = 16777215  # Белый фон
    #         logger.debug('Форматирование применено.')
    #     except Exception as e:
    #         logger.error(f'Ошибка при применении форматирования: {e}')

    def _read_rows_sync(self) -> List[dict]:
        """Синхронно читает строки из таблицы."""
        if not self.table:
            logger.error('Таблица не подключена.')
            return []
        try:
            headers = [cell.value for cell in self.sheet.range(self.table.HeaderRowRange.Address)]
            data = []
            print(1)
            for row in self.table.ListRows:
                row_data = {headers[i]: row.Range.Value[0][i] for i in range(len(headers))}
                data.append(row_data)
            logger.info('Строки успешно прочитаны.')
            return data
        except Exception as e:
            logger.error(f'Ошибка при чтении строк: {e}')
            return []

    @com_init
    def _add_row_sync(self, row_data: dict | list) -> None:
        """Синхронно добавляет новую строку в таблицу."""
        if not self.table:
            logger.error('Таблица не подключена.')
            return
        try:
            new_row = self.sheet.range(
                self.table.ListRows
                .Add(Position=self.table.ListRows.Count + 1, AlwaysInsert=True)
                .Range.Address
            )

            headers = [cell.value for cell in self.sheet.range(self.table.HeaderRowRange.Address)]

            if isinstance(row_data, dict):
                new_row.value = [row_data.get(header, None) for header in headers]
            elif isinstance(row_data, list):
                new_row.value = row_data
            else:
                logger.error('Неверный формат данных для добавления строки.')
                return

            logger.info('Новая строка добавлена.')
        except Exception as e:
            logger.error(f'Ошибка при добавлении строки: {e}')

    def _delete_row_sync(self, index: int) -> None:
        """Синхронно удаляет строку из таблицы по индексу."""
        if not self.table:
            logger.error('Таблица не подключена.')
            return
        try:
            self.table.ListRows(index + 1).Delete()
            logger.info(f'Строка {index} удалена.')
        except Exception as e:
            logger.error(f'Ошибка при удалении строки: {e}')

    def _update_row_sync(self, index: int, row_data: dict) -> None:
        """Синхронно обновляет данные строки по индексу."""
        if not self.table:
            logger.error('Таблица не подключена.')
            return
        try:
            headers = [cell.value for cell in self.sheet.range(self.table.HeaderRowRange.Address)]
            target_row = self.table.ListRows(index + 1)
            for i, header in enumerate(headers):
                if header in row_data:
                    target_row.Range(i + 1).Value = row_data[header]

            logger.info(f'Строка {index} обновлена.')
        except Exception as e:
            logger.error(f'Ошибка при обновлении строки: {e}')

    def _format_column_sync(self, column_name: str, data_type: DataType) -> None:
        """Синхронно форматирует столбец по заданному типу данных."""
        if not self.table:
            logger.error('Таблица не подключена.')
            return
        try:
            headers = [cell.value for cell in self.sheet.range(self.table.HeaderRowRange.Address)]
            if column_name not in headers:
                logger.error(f'Столбец {column_name} не найден.')
                return
            col_index = headers.index(column_name) + 1
            column = self.table.ListColumns(col_index)
            if data_type == DataType.DATE:
                column.Range.NumberFormat = 'YYYY-MM-DD'
            elif data_type == DataType.INTEGER:
                column.Range.NumberFormat = '0'
            elif data_type == DataType.FLOAT:
                column.Range.NumberFormat = '0.00'
            elif data_type == DataType.BOOLEAN:
                # Пример: заменяем 1/0 на Да/Нет
                column.Range.NumberFormat = '[Цвет 43]"Да";[Красный]"Нет";[Красный]"Нет"'
            elif data_type == DataType.STRING:
                column.Range.NumberFormat = '@'
            elif data_type == DataType.HZ:
                column.Range.NumberFormat = '0" Hz"'
            elif data_type == DataType.DPI:
                column.Range.NumberFormat = '0"dpi"'
            elif data_type == DataType.INCH:
                column.Range.NumberFormat = '0\\"'
            elif data_type == DataType.RUB:
                column.Range.NumberFormat = '_-* # ##0 ₽_-;-* # ##0 ₽_-;_-* "-" ₽_-;_-@_-'
            logger.info(f'Столбец {column_name} отформатирован как {data_type.value}.')
        except Exception as e:
            logger.error(f'Ошибка при форматировании столбца: {e}')

    def _refresh_table_sync(self) -> None:
        """Синхронно обновляет диапазон таблицы после изменений."""
        if not self.workbook:
            logger.error('Книга не подключена.')
            return
        try:
            self.workbook.api.RefreshAll()
            logger.info('Таблица обновлена.')
        except Exception as e:
            logger.error(f'Ошибка при обновлении таблицы: {e}')


class ExcelTableManager:
    """Класс для управления таблицами Excel с использованием xlwings."""

    def __init__(self, workbook_name: str, table_name: str) -> None:
        """
        Инициализирует менеджер таблицы Excel.

        :param workbook_name: Имя открытой книги Excel.
        :param table_name: Имя таблицы, созданной с помощью Ctrl+T.
        """
        self.workbook_name = workbook_name
        self.table_name = table_name
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._loop = asyncio.get_event_loop()
        # Инициализация _ExcelWorker в отдельном потоке
        self._worker = self._executor.submit(_ExcelWorker, self.workbook_name, self.table_name).result()
        logger.info('ExcelTableManager инициализирован.')

    async def read_rows(self) -> List[dict]:
        """
        Асинхронно читает строки из таблицы.

        :return: Список словарей с данными строк.
        """
        return await self._loop.run_in_executor(self._executor, self._worker._read_rows_sync)

    async def add_row(self, row_data: dict | list) -> 'ExcelTableManager':
        """
        Асинхронно добавляет новую строку в таблицу.

        :param row_data: Словарь с данными для новой строки.
        :return: Ссылка на экземпляр менеджера.
        """
        await self._loop.run_in_executor(self._executor, self._worker._add_row_sync, row_data)
        return self

    async def delete_row(self, index: int) -> 'ExcelTableManager':
        """
        Асинхронно удаляет строку из таблицы по индексу.

        :param index: Индекс строки для удаления (начиная с 1 после заголовка).
        :return: Ссылка на экземпляр менеджера.
        """
        await self._loop.run_in_executor(self._executor, self._worker._delete_row_sync, index)
        return self

    async def update_row(self, index: int, row_data: dict) -> 'ExcelTableManager':
        """
        Асинхронно обновляет данные строки по индексу.

        :param index: Индекс строки для обновления (начиная с 1 после заголовка).
        :param row_data: Словарь с новыми данными для строки.
        :return: Ссылка на экземпляр менеджера.
        """
        await self._loop.run_in_executor(self._executor, self._worker._update_row_sync, index, row_data)
        return self

    async def format_column(self, column_name: str, data_type: DataType) -> 'ExcelTableManager':
        """
        Асинхронно форматирует столбец по заданному типу данных.

        :param column_name: Имя столбца для форматирования.
        :param data_type: Тип данных для форматирования.
        :return: Ссылка на экземпляр менеджера.
        """
        await self._loop.run_in_executor(self._executor, self._worker._format_column_sync, column_name, data_type)
        return self

    async def refresh_table(self) -> 'ExcelTableManager':
        """
        Асинхронно обновляет диапазон таблицы после изменений.

        :return: Ссылка на экземпляр менеджера.
        """
        await self._loop.run_in_executor(self._executor, self._worker._refresh_table_sync)
        return self

    def __del__(self):
        """Закрывает исполнитель при уничтожении экземпляра."""
        self._executor.shutdown(wait=False)


# Пример использования
if __name__ == "__main__":
    async def main():
        # manager = ExcelTableManager(workbook_name="Книга1.xlsx", table_name="Table1")
        # data = await manager.read_rows()
        # logger.info(f'Прочитанные данные: {data}')
        # await manager.add_row([1, 2])

        # await manager.delete_row(0)
        # await manager.update_row(1, {"Column1": "Обновленное значение"})
        # await manager.format_column("Column2", DataType.RUB)
        # await manager.refresh_table()
        pass


    asyncio.run(main())
