"""
Базовый API клиент — фундамент для всех специализированных клиентов.

Предоставляет:
- Единый интерфейс HTTP-запросов (GET, POST, PUT, PATCH, DELETE)
- Автоматическую подстановку base_url, headers, auth
- Логирование каждого запроса и ответа
- Обработку ошибок, таймаутов и retry-механизм

Принцип: все API клиенты наследуются от BaseAPIClient и переиспользуют его логику.
"""

import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from integration_tests.config.settings import settings
from integration_tests.utils.logger import CustomLogger


class BaseAPIClient:
    """
    Базовый класс для работы с API.

    Attributes:
        base_url: базовый URL API (по умолчанию из settings.BASE_URL)
        auth_token: Bearer-токен авторизации (опционально)
        session: requests.Session с настроенными retry и headers
        logger: экземпляр CustomLogger для логирования
    """

    def __init__(
        self,
        base_url: str | None = None,
        auth_token: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """
        Инициализация API клиента.

        Args:
            base_url: базовый URL. Если None — берётся из settings.BASE_URL.
            auth_token: токен авторизации. Если передан — добавляется в заголовки.
            timeout: таймаут запроса в секундах. По умолчанию settings.REQUEST_TIMEOUT.
        """
        self.base_url: str = (base_url or settings.BASE_URL).rstrip("/")
        self.auth_token: str | None = auth_token
        self.timeout: int = timeout or settings.REQUEST_TIMEOUT

        log_file = getattr(settings, "LOG_FILE", None)
        log_level = getattr(settings, "LOG_LEVEL", "INFO")

        self.logger: CustomLogger = CustomLogger(
            name=self.__class__.__name__,
            log_file=log_file,
            log_level=log_level,
        )
        self.session: requests.Session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        Создание сессии requests с retry-механизмом и базовыми заголовками.

        Returns:
            Настроенная requests.Session.
        """
        session = requests.Session()

        # Retry-стратегия: 3 попытки с экспоненциальной задержкой.
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Базовые заголовки для всех запросов.
        default_headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Если передан токен — добавляем Authorization.
        if self.auth_token:
            default_headers["Authorization"] = f"Bearer {self.auth_token}"

        session.headers.update(default_headers)
        return session

    # --- Основные HTTP-методы ---

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Выполнение GET-запроса."""
        return self._request("GET", endpoint, params=params, **kwargs)

    def post(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Выполнение POST-запроса."""
        return self._request("POST", endpoint, json=json, **kwargs)

    def put(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Выполнение PUT-запроса."""
        return self._request("PUT", endpoint, json=json, **kwargs)

    def patch(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Выполнение PATCH-запроса."""
        return self._request("PATCH", endpoint, json=json, **kwargs)

    def delete(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Выполнение DELETE-запроса."""
        return self._request("DELETE", endpoint, json=json, **kwargs)

    # --- Внутренний метод выполнения запроса ---

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Внутренний метод выполнения HTTP-запроса с логированием и обработкой ошибок.

        Raises:
            requests.exceptions.Timeout / ConnectionError / RequestException.
        """
        url = self._build_url(endpoint)

        # Объединяем заголовки: базовые из сессии + переданные в kwargs.
        merged_headers = dict(self.session.headers)
        if "headers" in kwargs:
            merged_headers.update(kwargs["headers"])

        # Логируем запрос (методы log_* живут в CustomLogger).
        self.logger.log_request(
            method=method,
            url=url,
            headers=merged_headers,
            body=kwargs.get("json"),
            params=kwargs.get("params"),
        )

        # Засекаем время и выполняем запрос.
        start_time = time.time()
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs,
            )
            response_time = time.time() - start_time

            # Пытаемся распарсить ответ как JSON.
            try:
                response_body: dict | str = response.json()
            except ValueError:
                response_body = response.text

            # Логируем ответ.
            self.logger.log_response(
                status_code=response.status_code,
                response_time=response_time,
                body=response_body,
            )

            return response

        except requests.exceptions.Timeout as e:
            self.logger.log_error(e, context=f"Timeout при {method} {url}")
            raise
        except requests.exceptions.ConnectionError as e:
            self.logger.log_error(e, context=f"ConnectionError при {method} {url}")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.log_error(e, context=f"RequestException при {method} {url}")
            raise

    # --- Вспомогательные методы ---

    def _build_url(self, endpoint: str) -> str:
        """Формирование полного URL из base_url и endpoint."""
        endpoint_clean = endpoint.lstrip("/")
        return f"{self.base_url}/{endpoint_clean}"

    def set_auth_token(self, token: str) -> None:
        """Установка или обновление токена авторизации."""
        self.auth_token = token
        self.session.headers["Authorization"] = f"Bearer {token}"
        # self.logger.logger — внутренний logging.Logger (см. CustomLogger).
        self.logger.logger.info("Токен авторизации обновлён.")

    def clear_auth_token(self) -> None:
        """Удаление токена авторизации из сессии."""
        self.auth_token = None
        self.session.headers.pop("Authorization", None)
        self.logger.logger.info("Токен авторизации удалён.")
