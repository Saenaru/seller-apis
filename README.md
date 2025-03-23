# Описание проекта market.py

Данный скрипт предназначен для работы с API Яндекс.Маркета, позволяя автоматизировать обновление остатков и цен на товары в системе. Он создаёт и обновляет данные о запасах и ценах для кампаний FBS и DBS, помогая поддерживать актуальную информацию на торговой платформе.

## Функциональные возможности

- Получение списка товаров: Скрипт получает артикулы товаров, загруженных в Яндекс.Маркет, через API и обрабатывает их для дальнейшего использования.
- Обновление запасов: Автоматически обновляет информацию о наличии товаров по заданным идентификаторам кампании и склада.
- Обновление цен: Устанавливает актуальные цены на товары с использованием текущих данных.
- Поддержка FBS и DBS: Поддерживает как FBS (Fulfillment by Seller), так и DBS (Dropshipping by Seller) кампании.


# Описание проекта seller.py

Этот скрипт создан для автоматизации работы с API Ozon и направлен на управление ценами и остатками товаров. Он загружает данные с сайта производителя, обрабатывает их и синхронизирует с платформой Ozon, обеспечивая актуальность информации о товарах в магазине.

## Функциональные возможности

- Загрузка данных: Скрипт загружает и распаковывает актуальные данные о запасах от поставщика.
- Синхронизация данных с Ozon:
 - Обновление остатков: Автоматически актуализирует информацию о наличии товаров в Ozon.
 - Обновление цен: Устанавливает текущие цены на товары, используя данные, полученные от поставщика.
 - Эффективная обработка больших массивов данных: Реализация обработки данных партиями для оптимизации взаимодействия с API и снижения нагрузки.