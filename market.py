import datetime
import logging.config
from environs import Env
from seller import download_stock

import requests

from seller import divide, price_conversion

logger = logging.getLogger(__file__)


def get_product_list(page, campaign_id, access_token):
    """Получает список товаров из магазина Яндекс.Маркет.

    Эта функция делает запрос к API Яндекс.Маркета для получения
    маппингов товаров, начиная с указанной страницы.

    Args:
        page (str): Номер страницы или токен страницы для пагинации.
        campaign_id (str): Идентификатор кампании в Яндекс.Маркете.
        access_token (str): Токен доступа API Яндекс.Маркета.

    Returns:
        list: Список товаров, полученных из маппинга (если существует в ответе API).

    Raises:
        HTTPError: Возникает, если запрос не был успешным.

    Example:
        >>> get_product_list("some_page_token", "campaign_123", "access_token_abc")
        [...]

    Exception Example:
        >>> get_product_list("", "campaign_123", None)
        requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {
        "page_token": page,
        "limit": 200,
    }
    url = endpoint_url + f"campaigns/{campaign_id}/offer-mapping-entries"
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def update_stocks(stocks, campaign_id, access_token):
    """Обновляет остатки для товаров в Яндекс.Маркете.

    Отправляет PUT-запрос в API Яндекс.Маркета для обновления
    остатков по указанным кампаниям и товарам.
    
    Args:
        stocks (list): Список с информацией о товарных остатках.
        campaign_id (str): Идентификатор кампании.
        access_token (str): Токен доступа для API Яндекс.Маркета.

    Returns:
        dict: Ответ API Яндекс.Маркета о статусе обновления.

    Raises:
        HTTPError: Возникает, если запрос не был успешным.

    Example:
        >>> update_stocks([{"sku": "12345", "warehouseId": 1, "items": [{"type": "FIT", "count": 10}]}], "campaign_123", "access_token_abc")
        {'status': 'OK'}

    Exception Example:
        >>> update_stocks([], "campaign_123", None)
        requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"skus": stocks}
    url = endpoint_url + f"campaigns/{campaign_id}/offers/stocks"
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def update_price(prices, campaign_id, access_token):
    """Обновляет цены для товаров в Яндекс.Маркете.

    Отправляет POST-запрос в API Яндекс.Маркета для обновления
    цен товаров в указанной кампании.
    
    Args:
        prices (list): Список с информацией о ценах товаров.
        campaign_id (str): Идентификатор кампании.
        access_token (str): Токен доступа для API Яндекс.Маркета.

    Returns:
        dict: Ответ API Яндекс.Маркета о статусе обновления цен.

    Raises:
        HTTPError: Возникает, если запрос не был успешным.

    Example:
        >>> update_price([{"sku": "12345", "price": 1000}], "campaign_123", "access_token_abc")
        {'status': 'OK'}

    Exception Example:
        >>> update_price([], "campaign_123", None)
        requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"offers": prices}
    url = endpoint_url + f"campaigns/{campaign_id}/offer-prices/updates"
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def get_offer_ids(campaign_id, market_token):
    """Получает список артикулов товаров на Яндекс.Маркете.

    Эта функция делает серию запросов к API Яндекс.Маркета для получения
    всех доступных артикулов (SKU) из конкретной кампании. Она обходит
    все страницы с данными о товарах и возвращает полный список артикулов.

    Args:
        campaign_id (str): Идентификатор кампании на Яндекс.Маркете.
        market_token (str): Токен доступа к API Яндекс.Маркета.

    Returns:
        list: Список артикулов (SKU) товаров в кампании.

    Example:
        >>> get_offer_ids("campaign_123", "market_token_abc")
        ['SKU123', 'SKU124', 'SKU125', ...]

    Exception Example:
        >>> get_offer_ids("campaign_123", None)
        requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url
    """
    page = ""
    product_list = []
    while True:
        some_prod = get_product_list(page, campaign_id, market_token)
        product_list.extend(some_prod.get("offerMappingEntries"))
        page = some_prod.get("paging").get("nextPageToken")
        if not page:
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer").get("shopSku"))
    return offer_ids


def create_stocks(watch_remnants, offer_ids, warehouse_id):
    """Создает список объектов для обновления остатков в Яндекс.Маркете.

    Функция обрабатывает остатки из списка `watch_remnants` и формирует
    структуру данных, необходимую для API Яндекс.Маркета для обновления
    информации о запасах на складе.

    Args:
        watch_remnants (list): Список словарей с информацией о запасах.
        offer_ids (list): Список артикулов (SKU), присутствующих в Яндекс.Маркете.
        warehouse_id (int): Идентификатор склада для обновления запасов.

    Returns:
        list: Список структурированных данных для обновления остатков товаров.

    Example:
        >>> create_stocks([{'Код': '12345', 'Количество': '5'}], ['12345'], 1)
        [{'sku': '12345', 'warehouseId': 1, 'items': [{'count': 5, 'type': 'FIT', 'updatedAt': '...'}]}, ...]

    Exception Example:
        N/A
    """
    stocks = list()
    date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append(
                {
                    "sku": str(watch.get("Код")),
                    "warehouseId": warehouse_id,
                    "items": [
                        {
                            "count": stock,
                            "type": "FIT",
                            "updatedAt": date,
                        }
                    ],
                }
            )
            offer_ids.remove(str(watch.get("Код")))
    for offer_id in offer_ids:
        stocks.append(
            {
                "sku": offer_id,
                "warehouseId": warehouse_id,
                "items": [
                    {
                        "count": 0,
                        "type": "FIT",
                        "updatedAt": date,
                    }
                ],
            }
        )
    return stocks


def create_prices(watch_remnants, offer_ids):
    """Создает список цен для обновления в Яндекс.Маркете.

    Эта функция обрабатывает данные о часах и формирует структуру цен,
    которая будет загружена на Яндекс.Маркет. Каждый элемент в списке
    соответствует товару и содержит его цену и другие параметры.

    Args:
        watch_remnants (list): Список словарей с информацией о запасах часов.
        offer_ids (list): Список доступных артикулов (SKU) на Яндекс.Маркете.

    Returns:
        list: Список словарей с информацией о ценах для обновления.

    Example:
        >>> create_prices([{'Код': '12345', 'Цена': '999.99'}], ['12345'])
        [{'id': '12345', 'price': {'value': 1000, 'currencyId': 'RUR'}}]

    Exception Example:
        N/A
    """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "id": str(watch.get("Код")),
                # "feed": {"id": 0},
                "price": {
                    "value": int(price_conversion(watch.get("Цена"))),
                    # "discountBase": 0,
                    "currencyId": "RUR",
                    # "vat": 0,
                },
                # "marketSku": 0,
                # "shopSku": "string",
            }
            prices.append(price)
    return prices


async def upload_prices(watch_remnants, campaign_id, market_token):
    """Обновляет цены товаров в Яндекс.Маркете.

    Получает список артикулов, создает структуру цен и загружает
    её партиями на Яндекс.Маркет для обновления цен кампании.

    Args:
        watch_remnants (list): Список словарей с информацией о запасах часов.
        campaign_id (str): Идентификатор кампании в Яндекс.Маркете.
        market_token (str): Токен доступа к API Яндекс.Маркета.

    Returns:
        list: Список цен, которые были отправлены для обновления.

    Example:
        >>> await upload_prices(watch_remnants, "campaign_123", "market_token_abc")
        [{'id': '12345', 'price': {'value': 1000, 'currencyId': 'RUR'}}, ...]

    Exception Example:
        requests.exceptions.HTTPError если запрос к API неудачен.
    """
    offer_ids = get_offer_ids(campaign_id, market_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_prices in list(divide(prices, 500)):
        update_price(some_prices, campaign_id, market_token)
    return prices


async def upload_stocks(watch_remnants, campaign_id, market_token, warehouse_id):
    """Обновляет остатки товаров в Яндекс.Маркете.

    Получает список артикулов, создаёт структуру остатков и загружает
    её партиями на Яндекс.Маркет для обновления запасов кампании.

    Args:
        watch_remnants (list): Список словарей с информацией о запасах часов.
        campaign_id (str): Идентификатор кампании в Яндекс.Маркете.
        market_token (str): Токен доступа к API Яндекс.Маркета.
        warehouse_id (int): Идентификатор склада.

    Returns:
        tuple: (список товаров с ненулевыми остатками, полный список остатков).

    Example:
        >>> await upload_stocks(watch_remnants, "campaign_123", "market_token_abc", 1)
        ([{'sku': '12345', 'warehouseId': 1, 'items': [{'count': 5, ...}]}, ...], ...)

    Exception Example:
        requests.exceptions.HTTPError если запрос к API неудачен.
    """
    offer_ids = get_offer_ids(campaign_id, market_token)
    stocks = create_stocks(watch_remnants, offer_ids, warehouse_id)
    for some_stock in list(divide(stocks, 2000)):
        update_stocks(some_stock, campaign_id, market_token)
    not_empty = list(
        filter(lambda stock: (stock.get("items")[0].get("count") != 0), stocks)
    )
    return not_empty, stocks


def main():
    env = Env()
    market_token = env.str("MARKET_TOKEN")
    campaign_fbs_id = env.str("FBS_ID")
    campaign_dbs_id = env.str("DBS_ID")
    warehouse_fbs_id = env.str("WAREHOUSE_FBS_ID")
    warehouse_dbs_id = env.str("WAREHOUSE_DBS_ID")

    watch_remnants = download_stock()
    try:
        # FBS
        offer_ids = get_offer_ids(campaign_fbs_id, market_token)
        # Обновить остатки FBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_fbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_fbs_id, market_token)
        # Поменять цены FBS
        upload_prices(watch_remnants, campaign_fbs_id, market_token)

        # DBS
        offer_ids = get_offer_ids(campaign_dbs_id, market_token)
        # Обновить остатки DBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_dbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_dbs_id, market_token)
        # Поменять цены DBS
        upload_prices(watch_remnants, campaign_dbs_id, market_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
