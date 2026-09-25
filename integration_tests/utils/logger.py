"""
Модуль централизованного логирования для API-тестов.

Особенности:
- Вывод логов в консоль (INFO+) и файл (DEBUG+)
- Ротация файлов (max 10 МБ, 5 архивов)
- Маскирование чувствительных данных (токены, пароли)
- Специализированные методы для логирования HTTP-запросов/ответов
  (log_request / log_response / log_error) — используются BaseAPIClient
- Прокси-методы уровней (debug/info/warning/error/...) — используются
  тестами и клиентами напрямую (logger.info(...))
"""

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class TokenMaskingFilter(logging.Filter):
    

    SENSITIVE_KEYS = {"token", "password", "secret", "authorization", "access_token"}

    def filter(self, record: logging.LogRecord) -> bool:
        """Применяет маскирование к сообщению лога."""
        if not isinstance(record.msg, str):
            return True

        if "Bearer " in record.msg:
            record.msg = self._mask_bearer_token(record.msg)

        if "token" in record.msg.lower() and len(record.msg) > 100:
            record.msg = self._mask_json_tokens(record.msg)

        return True

    def _mask_bearer_token(self, message: str) -> str:
        """Маскирует Bearer-токен, оставляя первые и последние 10 символов."""
        parts = message.split("Bearer ")
        if len(parts) > 1:
            token_part = parts[1].split(",")[0].split("}")[0].strip()
            if len(token_part) > 20:
                masked = f"{token_part[:10]}...{token_part[-10:]}"
            else:
                masked = "***"
            message = message.replace(token_part, masked)
        return message

    def _mask_json_tokens(self, message: str) -> str:
        """Маскирует чувствительные поля в JSON-строке."""
        try:
            data = json.loads(message)
            if isinstance(data, dict):
                self._mask_dict(data)
                return json.dumps(data, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            pass
        return message

    def _mask_dict(self, data: dict) -> None:
        """Рекурсивно маскирует чувствительные ключи в словаре."""
        for key, value in data.items():
            if key.lower() in self.SENSITIVE_KEYS and isinstance(value, str):
                if len(value) > 20:
                    data[key] = f"{value[:10]}...{value[-10:]}"
                else:
                    data[key] = "***"
            elif isinstance(value, dict):
                self._mask_dict(value)


class CustomLogger:
    """
    Кастомный логгер с расширенными возможностями для API-тестов.

    Является прозрачной обёрткой над logging.Logger: предоставляет и атрибут
    ``logger`` (внутренний логгер), и специализированные HTTP-методы, и прокси
    стандартных уровней логирования.

    Attributes:
        logger: экземпляр logging.Logger
    """

    def __init__(
        self,
        name: str,
        log_file: str | None = None,
        log_level: str = "INFO",
    ) -> None:
        """
        Инициализация логгера.

        Args:
            name: имя логгера (обычно __name__ модуля / имя класса).
            log_file: путь к файлу логов (если None — только консоль).
            log_level: уровень логирования (DEBUG, INFO, WARNING, ERROR).
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, str(log_level).upper(), logging.INFO))

        # Избегаем дублирования handlers при повторной инициализации.
        if not self.logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            # Console handler — вывод в консоль (INFO+).
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # File handler с ротацией — вывод в файл (DEBUG+).
            if log_file:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)

                file_handler = RotatingFileHandler(
                    filename=str(log_path),
                    maxBytes=10 * 1024 * 1024,  # 10 МБ
                    backupCount=5,
                    encoding="utf-8",
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

            # Применяем фильтр маскирования токенов.
            self.logger.addFilter(TokenMaskingFilter())

    # ------------------------------------------------------------------ #
    # Прокси-методы стандартных уровней логирования.                      #
    # Нужны, чтобы тесты/клиенты могли писать logger.info(...) напрямую.  #
    # ------------------------------------------------------------------ #
    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Прокси для logging.Logger.debug."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Прокси для logging.Logger.info."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Прокси для logging.Logger.warning."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Прокси для logging.Logger.error."""
        self.logger.error(msg, *args, **kwargs)

    def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Прокси для logging.Logger.exception."""
        self.logger.exception(msg, *args, **kwargs)

    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        """Прокси для logging.Logger.critical."""
        self.logger.critical(msg, *args, **kwargs)

    # --- Специализированные методы для HTTP ---

    def log_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: Any | None = None,
        params: dict[str, str] | None = None,
    ) -> None:
        """Логирование HTTP-запроса."""
        safe_headers = self._mask_sensitive_data(headers or {})

        self.logger.debug(f"📤 REQUEST: {method} {url}")
        self.logger.debug(f"   Headers: {safe_headers}")

        if params:
            self.logger.debug(f"   Params: {params}")

        if body:
            body_str = str(body)
            if len(body_str) > 500:
                body_str = body_str[:500] + "... [truncated]"
            self.logger.debug(f"   Body: {body_str}")

    def log_response(
        self,
        status_code: int,
        response_time: float,
        body: Any | None = None,
    ) -> None:
        """Логирование HTTP-ответа."""
        if 200 <= status_code < 300:
            status_icon = "✅"
        elif 400 <= status_code < 500:
            status_icon = "⚠️"
        else:
            status_icon = "❌"

        self.logger.debug(f"{status_icon} RESPONSE: Status {status_code} | Time: {response_time:.3f}s")

        if body:
            body_str = str(body)
            if len(body_str) > 500:
                body_str = body_str[:500] + "... [truncated]"
            self.logger.debug(f"   Body: {body_str}")

    def log_error(self, error: Exception, context: str = "") -> None:
        """Логирование ошибки с контекстом."""
        error_msg = f"{context}: {type(error).__name__}: {error}" if context else f"{type(error).__name__}: {error}"
        self.logger.error(f"❌ ERROR: {error_msg}", exc_info=error)

    # --- Вспомогательные методы ---

    def _mask_sensitive_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Маскирование чувствительных данных в словаре."""
        sensitive_keys = {"authorization", "token", "password", "secret", "access_token"}
        masked = data.copy()

        for key in masked:
            if key.lower() in sensitive_keys:
                value = str(masked[key])
                if len(value) > 20:
                    masked[key] = f"{value[:10]}...{value[-10:]}"
                else:
                    masked[key] = "***"

        return masked


# --- Глобальный экземпляр логгера для быстрого доступа ---


def get_logger(name: str, log_file: str | None = None, log_level: str = "INFO") -> CustomLogger:
    """
    Фабрика для создания логгеров.

    Args:
        name: имя логгера.
        log_file: путь к файлу логов.
        log_level: уровень логирования.

    Returns:
        экземпляр CustomLogger
    """
    return CustomLogger(name=name, log_file=log_file, log_level=log_level)


# алиас 'logger' для удобного импорта
logger = get_logger("integration_tests")
