# 🤖 AI-Assisted API Auto Tests

[![CI](https://github.com/KAKnetuz/ai_assisted_api_auto_tests/actions/workflows/ci.yml/badge.svg)](https://github.com/KAKnetuz/ai_assisted_api_auto_tests/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python)](https://www.python.org/)
[![pytest](https://img.shields.io/badge/pytest-8.4+-orange?style=flat-square&logo=pytest)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](LICENSE)

Интеграционные автотесты REST API: заказы, тарифы, блокировка и списание средств, лицевые счета.

## 🧩 Технические характеристики

*   **Архитектура:** паттерн **API Client / Service Layer**. Работа с HTTP и сборка запросов вынесены в клиенты, тесты остаются «тонкими» и читаемыми.
*   **Параметризация:** тесты параметризованы по платформам (`core`, `platform_a`, `platform_b`); сценарии, завязанные на контрагента, прогоняются на **трёх разных контрагентах**.
*   **Работа с данными:** настройки вынесены в `.env` и типизированы через `pydantic-settings`.
*   **Чистый стенд:** созданные тестами заказы отменяются, а блокировки средств снимаются в teardown фикстур.
*   **Безопасные повторы:** автоматически повторяются только идемпотентные запросы (GET), чтобы не создать дубль заказа или списания.
*   **Логирование и отладка:** централизованный логгер с **маскированием чувствительных данных** (токены, пароли — в заголовках, параметрах и телах запросов/ответов) и ротацией логов.
*   **Контекст тестов:** `autouse`-фикстура добавляет в сообщение об ошибке контрагента и счёт, на которых упал тест.
*   **CI:** GitHub Actions — линтер (ruff), офлайн-тесты фреймворка и проверка сборки тестов на каждый push и PR.
*   **Стек:** Python 3.13, `pytest`, `requests`, `pydantic-settings`, `Allure`.

> 🔒 **Примечание для портфолио:** код представляет собой демонстрационную версию. Все реальные эндпоинты, данные контрагентов, UUID, коды ответов и бизнес-логика заменены на обобщённые плейсхолдеры для соблюдения NDA корпоративного клиента.

## 📁 Структура

```
integration_tests/
├── api_clients/   # API-клиенты (Service Layer), BaseAPIClient — HTTP, повторы, логирование
├── config/        # settings (.env), endpoints (платформы и пути), constants, suppliers
├── helpers/       # кастомные ассерты и генераторы тестовых данных
├── tests/         # интеграционные тесты (требуют доступ к API)
├── unit_tests/    # офлайн-тесты самого фреймворка (запускаются в CI)
└── utils/         # логгер с маскированием
```

## 🚀 Как запустить

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r integration_tests/requirements.txt

cp integration_tests/.env.example integration_tests/.env   # заполнить BASE_URL, SUPPLIER_UUIDS и т.д.

pytest                                   # все интеграционные тесты
pytest -m smoke                          # только smoke
pytest -k platform_b                     # сценарии одной платформы
pytest integration_tests/tests/test_payment.py
```

Отчёт Allure (результаты пишутся в `allure-results/`):

```bash
allure serve allure-results
```

### Проверки без доступа к API

```bash
ruff check --config integration_tests/ruff.toml integration_tests
pytest integration_tests/unit_tests      # маршрутизация, политика повторов, маскирование
pytest --collect-only -q                 # все тесты собираются
```

## 📄 Документация и аналитика
Примеры оформления тест-кейсов, баг-репортов и тест-планов доступны в отдельном репозитории-портфолио:
➡️ [test-artifacts-examples](https://github.com/KAKnetuz/test-artifacts-examples)
