"""
Хелперы для работы с API-запросами.
"""

import json
import time
from collections.abc import Callable
from typing import Any

import requests


class APIHelpers:
    """Вспомогательные методы для API-тестов."""

    @staticmethod
    def retry_request(
        func: Callable[[], requests.Response],
        max_retries: int = 3,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        expected_status: int = 200,
    ) -> requests.Response:
        """
        Выполнение запроса с retry-механизмом.

        Полезно для нестабильных эндпоинтов, которые могут временно
        возвращать 5xx или не тот статус.

        Args:
            func: функция, возвращающая requests.Response.
            max_retries: максимальное число попыток.
            delay: начальная задержка между попытками (в секундах).
            backoff_factor: множитель увеличения задержки.
            expected_status: ожидаемый статус-код для успеха.

        Returns:
            requests.Response после успешной попытки.

        Raises:
            AssertionError: если все попытки не дали ожидаемый статус.
        """
        last_response: requests.Response | None = None
        current_delay = delay

        for attempt in range(1, max_retries + 1):
            try:
                last_response = func()
                if last_response.status_code == expected_status:
                    return last_response
            except requests.exceptions.RequestException:
                pass  # Игнорируем сетевые ошибки — пробуем снова

            if attempt < max_retries:
                time.sleep(current_delay)
                current_delay *= backoff_factor

        # Если все попытки провалились — возвращаем последний ответ
        if last_response is None or last_response.status_code != expected_status:
            raise AssertionError(
                f"После {max_retries} попыток не получен статус {expected_status}. "
                f"Последний статус: {last_response.status_code if last_response else 'None'}"
            )
        return last_response

    @staticmethod
    def safe_parse_json(response: requests.Response) -> Any:
        """
        Безопасный парсинг JSON из ответа.

        Args:
            response: объект requests.Response.

        Returns:
            Распарсенный JSON (dict/list) или исходный текст,
            если парсинг не удался.
        """
        try:
            return response.json()
        except (ValueError, json.JSONDecodeError):
            return response.text

    @staticmethod
    def extract_by_path(data: Any, path: str, default: Any = None) -> Any:
        """
        Извлечение значения из вложенного JSON по пути.

        Примеры путей:
            - 'Data.0.AccountNumber'
            - 'Orders.0.Status'
            - 'Count'

        Args:
            data: JSON-объект (dict/list).
            path: строка пути через '.' (поддерживает индексы списков).
            default: значение по умолчанию, если путь не найден.

        Returns:
            Найденное значение или default.
        """
        keys = path.split(".")
        current: Any = data

        for key in keys:
            try:
                # Пробуем как индекс списка
                if isinstance(current, list):
                    current = current[int(key)]
                # Пробуем как ключ словаря
                elif isinstance(current, dict):
                    current = current[key]
                else:
                    return default
            except (KeyError, IndexError, TypeError, ValueError):
                return default

        return current

    @staticmethod
    def validate_response_schema(
        response_data: dict[str, Any],
        required_fields: list[str],
    ) -> None:
        """
        Валидация наличия обязательных полей в ответе.

        Args:
            response_data: JSON-объект ответа.
            required_fields: список обязательных полей.

        Raises:
            AssertionError: если хотя бы одно поле отсутствует.
        """
        missing = [f for f in required_fields if f not in response_data]
        if missing:
            raise AssertionError(
                f"В ответе отсутствуют обязательные поля: {missing}. Полученные поля: {list(response_data.keys())}"
            )
