import pythoncom
import win32com.client as win32
from excel import logger
import os


def insert_row_into_table(workbook_path: str, sheet_name: str, table_name: str, position: int, row_data: dict):
    """
    Вставляет новую строку в указанную таблицу Excel на заданной позиции.

    :param workbook_path: Путь к файлу Excel.
    :param sheet_name: Имя листа, содержащего таблицу.
    :param table_name: Имя таблицы (ListObject).
    :param position: Позиция вставки (начиная с 1 для первой строки данных).
    :param row_data: Словарь с данными для новой строки. Ключи соответствуют именам столбцов.
    """
    try:
        # Инициализируем COM для текущего потока
        pythoncom.CoInitialize()

        # Подключаемся к уже запущенному Excel
        excel = win32.GetActiveObject("Excel.Application")
        # excel.Visible = False
        # excel.DisplayAlerts = False

        # Получаем имя рабочей книги из пути
        workbook_name = os.path.basename(workbook_path)

        # Получаем уже открытую рабочую книгу
        try:
            wb = excel.Workbooks(workbook_name)
            logger.info(f'Подключено к уже открытой книге: {workbook_name}')
        except Exception:
            logger.error(f'Рабочая книга "{workbook_name}" не найдена среди открытых книг.')
            return

        sht = wb.Worksheets(sheet_name)
        logger.info(f'Лист выбран: {sheet_name}')

        # Получаем объект таблицы
        table = sht.ListObjects(table_name)
        if not table:
            logger.error(f'Таблица с именем "{table_name}" не найдена на листе "{sheet_name}".')
            return

        # Вставляем новую строку на указанной позиции
        logger.info(f'Позиция вставки: {position}')
        if position < 1 or position > table.ListRows.Count + 1:
            logger.error(f'Некорректная позиция вставки: {position}')
            return

        new_list_row = table.ListRows.Add(Position=position, AlwaysInsert=True)
        logger.info(f'Вставлена новая строка на позиции {position}.')

        # Получаем заголовки столбцов таблицы

        headers = sht.Range(table.HeaderRowRange.Address).Value[0]
        logger.info(f'Заголовки таблицы: {headers}')

        # Заполняем новую строку данными
        for header, value in row_data.items():
            if header in headers:
                col_index = headers.index(header) + 1
                sht.Cells(new_list_row.Range.Row, col_index).Value = value
            else:
                logger.warning(f'Столбец "{header}" не найден в таблице.')

        logger.info('Новая строка успешно добавлена и заполнена данными.')

        # Сохраняем рабочую книгу
        wb.Save()

    except Exception as e:
        logger.error(f'Ошибка при вставке строки: {e}')
    finally:
        # Деинициализируем COM для текущего потока
        pythoncom.CoUninitialize()


import pythoncom
from excel import logger  # Предполагается, что модуль logger настроен
import os

def create_dynamic_table(workbook_path: str, sheet_name: str, table_name: str, start_cell: str, headers: list):
    """
    Создаёт динамическую таблицу в указанном листе Excel с заданными заголовками.

    :param workbook_path: Путь к файлу Excel.
    :param sheet_name: Имя листа, где будет создана таблица.
    :param table_name: Имя для новой таблицы (ListObject).
    :param start_cell: Начальная ячейка для таблицы (например, "A1").
    :param headers: Список заголовков столбцов таблицы.
    """
    try:
        # Инициализируем COM для текущего потока
        pythoncom.CoInitialize()

        # Подключаемся к уже запущенному Excel
        excel = win32.GetActiveObject("Excel.Application")
        # excel.Visible = False
        # excel.DisplayAlerts = False

        # Получаем имя рабочей книги из пути
        workbook_name = os.path.basename(workbook_path)

        # Получаем уже открытую рабочую книгу
        try:
            wb = excel.Workbooks(workbook_name)
            logger.info(f'Подключено к уже открытой книге: {workbook_name}')
        except Exception as e:
            logger.error(f'Рабочая книга "{workbook_name}" не найдена среди открытых книг. Ошибка: {e}')
            return

        sht = wb.Worksheets(sheet_name)
        logger.info(f'Лист выбран: {sheet_name}')

        # Определяем диапазон для заголовков
        # start_range = sht.Range(start_cell)
        start_range = excel.Selection.Cells(1, 1).Address
        excel.Worksheets('Лист1').Activate()
        print(start_range)
        return
        end_cell = sht.Cells(start_range.Row, start_range.Column + len(headers) - 1)
        header_range = sht.Range(start_range, end_cell)
        header_range.Value = [headers]
        logger.info(f'Заголовки таблицы установлены: {headers}')

        # Определяем диапазон таблицы (только заголовки на данный момент)
        table_range = sht.Range(start_cell, end_cell)

        # Создаём таблицу
        try:
            table = sht.ListObjects.Add(SourceType=win32.constants.xlSrcRange,
                                        Source=table_range,
                                        XlListObjectHasHeaders=win32.constants.xlYes)
            table.Name = table_name
            logger.info(f'Таблица "{table_name}" успешно создана на диапазоне {table_range.Address}.')
        except Exception as e:
            logger.error(f'Ошибка при создании таблицы "{table_name}": {e}')
            return

        # Применяем стиль таблицы (опционально)
        try:
            table.TableStyle = "TableStyleMedium9"  # Можно изменить на желаемый стиль
            logger.info(f'Применён стиль "TableStyleMedium9" к таблице "{table_name}".')
        except Exception as e:
            logger.warning(f'Не удалось применить стиль к таблице "{table_name}": {e}')

        # Сохраняем рабочую книгу
        try:
            wb.Save()
            logger.info(f'Рабочая книга "{workbook_name}" успешно сохранена после создания таблицы.')
        except Exception as e:
            logger.error(f'Ошибка при сохранении рабочей книги: {e}')

    except Exception as e:
        logger.error(f'Общая ошибка при создании таблицы: {e}')
    finally:
        # Деинициализируем COM для текущего потока
        pythoncom.CoUninitialize()


def sync_main():
    # loop = asyncio.get_running_loop()
    # loop.run_in_executor(
    #         pool,
    #         insert_row_sync,
    #         "Книга1.xlsx",
    #         "Лист1",
    #         "Table1",
    #         1,
    #         {"Column1": "Асинхронное значение", "Column2": 456}
    #     )
    insert_row_into_table("Книга1.xlsx", "Лист1", "Table1", 10, {"Column1": "Асинхронное значение", "Column2": 456})


if __name__ == "__main__":
    workbook_path = r"Книга1.xlsx"
    sheet_name = "Лист2"
    table_name = "Table1"
    start_cell = "A1"
    headers = ["ID", "Имя", "Возраст", "Email"]

    create_dynamic_table(workbook_path, sheet_name, table_name, start_cell, headers)

