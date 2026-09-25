# API Integration Tests

## Структура проекта
- `api_clients/` — API клиенты (паттерн Service Layer)
- `config/` — Конфигурация (settings.py, endpoints.py)
- `helpers/` — Вспомогательные функции (assertions, generators)
- `tests/` — Интеграционные тесты (тонкий слой)
- `unit_tests/` — Офлайн-тесты фреймворка (запускаются в CI)
- `utils/` — Утилиты (логгер)
