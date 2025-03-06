import re
from time import sleep

import pandas as pd
import requests

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

url = "https://market.yandex.ru/product--ryzen-9-7900x/1777144709?sku=101853105497&uniqueId=1230896&do-waremd5=phaZJ9Jqx-EWerdGt5XLzw&cpc=4xebjd1itj_nLNrYT1rCyzXpiB6Ea4WPz95UzbHKYArP-0QSYOMmZiDoKiPdu9NTuO-Xeb3ZV-RabhoQLLu1BcaGuJAExF3-FBgtepaks7MNDBLtV7_lSxgmtv2FHakEmPBgqQVpJ9jbKw-g4CGjoVO8DdHvY5y7oN01bjn1sZmr9bPYB9c3dCN9fgHmZH7GoWwcBByO0ZYpN35036peYYa9FVyWilit-R1lHS41amWsip2TXRpuKBQxhwHxIugYJwN4w1kRZfOsQA-vF1HzsE1SkcRXndq-X50vJSsRnyh55_AbbxWwUDnXWROVxNbF2k4m6IfdF5GjPe8YN12ojrjf9ixAOfFPWuwi5FzRmOol7ehtE80tQqI7b0jMkIkWkql0GAT1xYT6TZ9z-U4Q1Jur8HOKmqE1KsWXYl2tqEvGQxJXvBf-KdgRM6pe8r8ZPGU-CAS6Vpg%2C"

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Host': 'market.yandex.ru',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
}

# print(response.status_code)

# with open('index.html', 'wb') as f:
#     f.write(response.text.encode('utf8'))

# Константа для поля "Источник"
ИСТОЧНИК = "Я.Маркет"


# Пример переменной с HTML содержимым страницы


# Функция для извлечения данных из document.title
def extract_model(html):
    title_pattern = r'document\.title="Процессор\s+([^—]+)'
    match = re.search(title_pattern, html)
    if match:
        модель = match.group(1).strip()
        return модель
    return None


# Функция для извлечения спецификаций из <noframes>
def extract_specs(html):
    specs = {}

    json_content = html

    # Извлечение значений с помощью регулярных выражений
    title_pattern = r'document\.title="Процессор\s+([^—]+)'
    бренд_pattern = r'"brand":"([^"]+)"'
    сокет_pattern = r'{"value":"([^"]+)","transition":{[^}]+},"type":"catalog"},"name":"Сокет"}]}'
    тип_памяти_pattern = r'{"value":"([^"]+)","transition":{"params":{[^}]+},"type":"catalog"},"name":"Тип памяти"}'
    количество_ядер_pattern = r'"Ядро процессора"},{"value":"(\d+)\s*шт\."'
    количество_потоков_pattern = r'"name":"Количество потоков","value":"(\d+)"'
    техпроцесс_pattern = r'"value":"(\d+)\s*нм"'
    частота_pattern = r'"value":"(\d+)\s*МГц"'
    tdp_pattern = r'"value":"(\d+)\s*Вт"'

    # Поиск и сохранение значений
    бренд = re.search(бренд_pattern, json_content)
    if бренд:
        specs["Производитель"] = бренд.group(1)

    количество_ядер = re.search(количество_ядер_pattern, json_content)
    if количество_ядер:
        specs["Ядра"] = количество_ядер.group(1)

    количество_потоков = re.search(количество_потоков_pattern, json_content)
    if количество_потоков:
        specs["Потоки"] = количество_потоков.group(1)

    техпроцесс = re.search(техпроцесс_pattern, json_content)
    if техпроцесс:
        specs["Техпроцесс"] = техпроцесс.group(1)

    частота = re.search(частота_pattern, json_content)
    if частота:
        specs["Базовая частота"] = частота.group(1)

    модель = extract_model(html)
    if модель:
        specs["Модель"] = модель.split(',')[0]

    tdp = re.search(tdp_pattern, json_content)
    if tdp:
        specs["TDP"] = tdp.group(1)

    return specs


# Функция для извлечения цены из JSON
def extract_price(html):
    if html:
        price_content = html
        # Извлечь значение цены с учетом скидки
        main_price_pattern = r'"price":{"value":(\d+),"currency":"RUR"},"type":"withoutDiscount"'
        discount_pattern = r'"discountPercent":\s*(\d+)'

        main_price = re.search(main_price_pattern, price_content)
        discount = re.search(discount_pattern, price_content)

        # print(main_price, discount)

        if main_price:
            цена = int(main_price.group(1))
            if discount:
                скидка = int(discount.group(1))
                цена = цена  # Предполагается, что mainPrice уже с учётом скидки
            return цена
    return "Не указана"


# Основная функция парсинга
def parse_product(html):
    данные = {}

    # Извлечение модели
    модель = extract_model(html)
    if модель:
        данные["Модель"] = модель

    # Извлечение спецификаций
    specs = extract_specs(html)
    данные.update(specs)

    # Извлечение цены
    цена = extract_price(html)
    данные["Цена"] = цена

    # Добавление "Источник"
    данные["Источник"] = ИСТОЧНИК

    return данные


from pyperclip import paste

h = True
last_link = paste()
while True:
    # Парсинг страницы
    link = paste()
    if link == last_link:
        sleep(.5)
        continue
    last_link = link

    product_data = parse_product(requests.request("GET", last_link, headers=headers).text)

    # Определение порядка столбцов
    столбцы = [
        "Производитель", "Источник", "Модель", "Техпроцесс",
        "Ядра", "Потоки", "Базовая частота", "TDP", "Цена"
    ]

    # Создание таблицы с заполненными данными
    df = pd.DataFrame([product_data], columns=столбцы)

    # Вывод таблицы
    print(df.to_csv(index=False, sep=';', header=h), end='')
    h = False
