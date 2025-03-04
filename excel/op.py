import asyncio
from concurrent.futures import ThreadPoolExecutor

import pythoncom

from yma.excel import logger
import xlwings as xw


def insert_row_into_table(workbook_path: str, sheet_name: str, table_name: str, position: int, row_data: dict):
    """
    Вставляет новую строку в указанную таблицу Excel на заданной позиции.

    :param workbook_path: Путь к файлу Excel.
    :param sheet_name: Имя листа, содержащего таблицу.
    :param table_name: Имя таблицы (ListObject).
    :param position: Позиция вставки (начиная с 1 для первой данных строки).
    :param row_data: Словарь с данными для новой строки. Ключи соответствуют именам столбцов.
    """
    try:
        # Инициализируем COM для текущего потока
        pythoncom.CoInitialize()

        # Открываем рабочую книгу
        wb = xw.Book(workbook_path)
        print(wb, type(wb))
        sht = wb.sheets[sheet_name]
        print(sht, sheet_name)
        logger.info(f'Открыта книга: {workbook_path}, лист: {sheet_name}')

        # Получаем объект таблицы
        table = sht.api.ListObjects(table_name)
        if not table:
            logger.error(f'Таблица с именем "{table_name}" не найдена на листе "{sheet_name}".')
            return

        # Вставляем новую строку на указанной позиции
        # вставка на последнюю строку
        position = table.ListRows.Count + 1
        print(position)
        new_list_row = table.ListRows.Add(Position=position, AlwaysInsert=True)
        new_row_range = new_list_row.Range
        logger.info(f'Вставлена новая строка на позиции {position}.')
        print(new_row_range)
        # Преобразуем COM-Range в xlwings Range для удобства работы
        new_row = sht.range(new_row_range.Address)
        # Получаем заголовки столбцов таблицы
        headers = [cell.value for cell in sht.range(table.HeaderRowRange.Address)]
        logger.info(f'Заголовки таблицы: {headers}')

        # Формируем список значений в соответствии с порядком столбцов
        new_row_values = [row_data.get(header, None) for header in headers]
        logger.info(f'Данные для новой строки: {new_row_values}')

        for a, b in zip(new_row, new_row_values):
            a.value = b

        logger.info('Новая строка успешно добавлена и заполнена данными.')

    except Exception as e:
        logger.error(f'Ошибка при вставке строки: {e}')
    finally:
        # Деинициализируем COM для текущего потока
        pythoncom.CoUninitialize()


def insert_row_sync(*args, **kwargs):
    insert_row_into_table(*args, **kwargs)


async def main():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        await loop.run_in_executor(
            pool,
            insert_row_sync,
            "Книга1.xlsx",
            "Лист1",
            "Table1",
            2,
            {"Column1": "Асинхронное значение", "Column2": 456}
        )


if __name__ == "__main__":
    asyncio.run(main())
