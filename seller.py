import io
import logging.config
import os
import re
import zipfile
from environs import Env

import pandas as pd
import requests

logger = logging.getLogger(__file__)


def get_product_list(last_id, client_id, seller_token):
    """
    Получает список товаров из магазина Ozon.

    Эта функция делает POST-запрос к API Ozon для получения списка
    товаров, начиная с указанного `last_id`. Функция возвращает
    JSON-объект с информацией о товарах.

    Args:
        last_id (str): Идентификатор последнего элемента в списке. Используется
            для пагинации.
        client_id (str): Идентификатор клиента Ozon API.
        seller_token (str): Токен аутентификации продавца.

    Returns:
        dict: Словарь с информацией о товарах, извлеченной из API Ozon.

    Raises:
        HTTPError: Возникает, если запрос не был успешным.

    Example:
        >>> get_product_list("", "my_client_id", "my_seller_token")
        {'items': [...], 'total': 100, 'last_id': '...'}

    Exception Example:
        >>> get_product_list("", None, None)
        requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url
    """
    url = "https://api-seller.ozon.ru/v2/product/list"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {
        "filter": {
            "visibility": "ALL",
        },
        "last_id": last_id,
        "limit": 1000,
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def get_offer_ids(client_id, seller_token):
    """
    Получает артикулы всех товаров из магазина Ozon.

    Эта функция извлекает все артикулы товаров, проходя по массиву
    товаров, полученных от API Ozon.

    Args:
        client_id (str): Идентификатор клиента Ozon API.
        seller_token (str): Токен аутентификации продавца.

    Returns:
        list: Список строк, содержащих артикулы товаров.

    Example:
        >>> get_offer_ids("my_client_id", "my_seller_token")
        ['12345', '67890', ...]

    Exception Example:
        >>> get_offer_ids(None, None)
        requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url
    """
    last_id = ""
    product_list = []
    while True:
        some_prod = get_product_list(last_id, client_id, seller_token)
        product_list.extend(some_prod.get("items"))
        total = some_prod.get("total")
        last_id = some_prod.get("last_id")
        if total == len(product_list):
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer_id"))
    return offer_ids


def update_price(prices: list, client_id, seller_token):
    """
    Обновляет цены товаров на платформе Ozon.

    Эта функция отправляет POST-запрос в API Ozon для обновления цен
    на указанные товары. Ожидается, что `prices` будет содержать список
    словарей с информацией о товарах и их новых ценах.

    Args:
        prices (list): Список словарей, каждый из которых содержит информацию
            о товаре и его новой цене.
        client_id (str): Идентификатор клиента Ozon API.
        seller_token (str): Токен аутентификации продавца.

    Returns:
        dict: Ответ от Ozon API с информацией о результатах обновления цен.

    Raises:
        HTTPError: Возникает, если запрос не был успешным.

    Example:
        >>> update_price([{'offer_id': '12345', 'price': '100.00'}], "my_client_id", "my_seller_token")
        {'result': ...}

    Exception Example:
        >>> update_price([{'offer_id': '12345', 'price': '100.00'}], None, None)
        requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url
    """
    url = "https://api-seller.ozon.ru/v1/product/import/prices"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"prices": prices}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def update_stocks(stocks: list, client_id, seller_token):
    """Обновляет остатки товаров на платформе Ozon.

    Эта функция отправляет POST-запрос в API Ozon для обновления остатков
    на указанные товары. Ожидается, что `stocks` будет содержать список
    словарей с информацией о товарах и их новых остатках.

    Args:
        stocks (list): Список словарей, каждый из которых содержит информацию
            о товаре и его новом остатке.
        client_id (str): Идентификатор клиента Ozon API.
        seller_token (str): Токен аутентификации продавца.

    Returns:
        dict: Ответ от Ozon API с информацией о результатах обновления остатков.

    Raises:
        HTTPError: Возникает, если запрос не был успешным.

    Example:
        >>> update_stocks([{'offer_id': '12345', 'stock': 50}], "my_client_id", "my_seller_token")
        {'result': ...}

    Exception Example:
        >>> update_stocks([{'offer_id': '12345', 'stock': 50}], None, None)
        requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url
    """
    url = "https://api-seller.ozon.ru/v1/product/import/stocks"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"stocks": stocks}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def download_stock():
    """Скачивает и извлекает файл с остатками с сайта Casio.

    Эта функция делает запрос на сайт Casio для загрузки файла
    остатков в формате ZIP, извлекает содержимое и преобразует его
    в список словарей, каждый из которых содержит информацию о часах.

    Returns:
        list: Список словарей, содержащих информацию о часах и их запасах.

    Raises:
        HTTPError: Возникает, если запрос на сайт Casio не был успешным.

    Example:
        >>> watch_remnants = download_stock()
        >>> len(watch_remnants)
        1000
    """
    casio_url = "https://timeworld.ru/upload/files/ostatki.zip"
    session = requests.Session()
    response = session.get(casio_url)
    response.raise_for_status()
    with response, zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        archive.extractall(".")
    excel_file = "ostatki.xls"
    watch_remnants = pd.read_excel(
        io=excel_file,
        na_values=None,
        keep_default_na=False,
        header=17,
    ).to_dict(orient="records")
    os.remove("./ostatki.xls")
    return watch_remnants


def create_stocks(watch_remnants, offer_ids):
    """
    Создает список словарей с информацией об остатках для Ozon.

    Эта функция обрабатывает информацию о часах и создает список,
    содержащий артикулы и соответствующие им запасы товаров, которые
    нужно обновить на Ozon.

    Args:
        watch_remnants (list): Список словарей с информацией о часах.
        offer_ids (list): Список артикулов товаров, загруженных на Ozon.

    Returns:
        list: Список словарей с обновлением остатков для товаров Ozon.

    Example:
        >>> stocks = create_stocks(watch_remnants, offer_ids)
        >>> len(stocks)
        998
    """
    stocks = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append({"offer_id": str(watch.get("Код")), "stock": stock})
            offer_ids.remove(str(watch.get("Код")))
    for offer_id in offer_ids:
        stocks.append({"offer_id": offer_id, "stock": 0})
    return stocks


def create_prices(watch_remnants, offer_ids):
    """Создает списки цен для обновления на платформе Ozon.

    Функция преобразует данные о часах из файла остатков в
    список словарей, содержащих информацию о новых ценах
    на товары для обновления на Ozon.

    Args:
        watch_remnants (list): Список словарей с информацией о часах.
        offer_ids (list): Список артикулов товаров, загруженных на Ozon.

    Returns:
        list: Список словарей с обновлением цен для товаров Ozon.

    Example:
        >>> prices = create_prices(watch_remnants, offer_ids)
        >>> len(prices)
        987
    """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "auto_action_enabled": "UNKNOWN",
                "currency_code": "RUB",
                "offer_id": str(watch.get("Код")),
                "old_price": "0",
                "price": price_conversion(watch.get("Цена")),
            }
            prices.append(price)
    return prices


def price_conversion(price: str) -> str:
    """Преобразует форматированную строку цены в простую строку с целым числом.

    Эта функция обрабатывает переданную строку с ценой, удаляя все нечисловые символы,
    и возвращает только целочисленное значение в виде строки.

    Аргументы:
        price (str): Строка с ценой, которая должна быть преобразована, может содержать
        символы и текст (например, "5'990.00 руб.").

    Возвращает:
        str: Числовая строка, извлеченная из входной цены (например, "5990" для "5'990.00 руб.").

    Примеры:
        Корректное выполнение:
        >>> price_conversion("5'990.00 руб.")
        '5990'

        Некорректное выполнение (входное значение не строка):
        >>> price_conversion(5990)
        TypeError: 'int' object is not subscriptable

    """
    return re.sub("[^0-9]", "", price.split(".")[0])


def divide(lst: list, n: int):
    """Разделяет список на подсписки заданной длины.

    Функция использует генератор для разделения входного списка на
    подсписки длиной `n` элементов.

    Args:
        lst (list): Список элементов для разделения.
        n (int): Размер подсписков, на которые делится `lst`.

    Yields:
        list: Следующий подсписок из `lst` размером `n` элементов.

    Example:
        >>> list(divide([1, 2, 3, 4, 5], 2))
        [[1, 2], [3, 4], [5]]

    Exception Example:
        N/A
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def upload_prices(watch_remnants, client_id, seller_token):
    """Обновляет цены на платформе Ozon.

    Получает текущие артикулы товаров и загружает новые цены из
    списка остатков на платформу Ozon.

    Args:
        watch_remnants (list): Список словарей с информацией о запасах товаров.
        client_id (str): Идентификатор клиента Ozon API.
        seller_token (str): Токен аутентификации продавца.

    Returns:
        list: Список цен по каждому товару, загруженный на платформу Ozon.

    Example:
        >>> await upload_prices(watch_remnants, "my_client_id", "my_seller_token")
        [{'offer_id': '12345', 'price': '1000'}, ...]

    Exception Example:
        requests.exceptions.HTTPError если не удалось подключиться к API с указанными параметрами.
    """
    offer_ids = get_offer_ids(client_id, seller_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_price in list(divide(prices, 1000)):
        update_price(some_price, client_id, seller_token)
    return prices


async def upload_stocks(watch_remnants, client_id, seller_token):
    """Обновляет остатки на платформе Ozon.

    Получает текущие артикулы товаров и загружает новые остатки из
    списка остатков на платформу Ozon.

    Args:
        watch_remnants (list): Список словарей с информацией о запасах товаров.
        client_id (str): Идентификатор клиента Ozon API.
        seller_token (str): Токен аутентификации продавца.

    Returns:
        tuple: (список остатков с ненулевым количеством, полный список остатков).

    Example:
        >>> await upload_stocks(watch_remnants, "my_client_id", "my_seller_token")
        ([{'offer_id': '12345', 'stock': 50}, ...], [{'offer_id': '12345', 'stock': 50}, ...])

    Exception Example:
        requests.exceptions.HTTPError если не удалось подключиться к API с указанными параметрами.
    """
    offer_ids = get_offer_ids(client_id, seller_token)
    stocks = create_stocks(watch_remnants, offer_ids)
    for some_stock in list(divide(stocks, 100)):
        update_stocks(some_stock, client_id, seller_token)
    not_empty = list(filter(lambda stock: (stock.get("stock") != 0), stocks))
    return not_empty, stocks


def main():
    env = Env()
    seller_token = env.str("SELLER_TOKEN")
    client_id = env.str("CLIENT_ID")
    try:
        offer_ids = get_offer_ids(client_id, seller_token)
        watch_remnants = download_stock()
        stocks = create_stocks(watch_remnants, offer_ids)
        for some_stock in list(divide(stocks, 100)):
            update_stocks(some_stock, client_id, seller_token)
        prices = create_prices(watch_remnants, offer_ids)
        for some_price in list(divide(prices, 900)):
            update_price(some_price, client_id, seller_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
