"""
Клиент для получения токена авторизации.
Токен получается через GET-запрос на эндпоинт settings.TOKEN_SERVICE_URL.
"""
from integration_tests.api_clients.base_api_client import BaseAPIClient
from integration_tests.config.settings import settings


class AuthClient(BaseAPIClient):
    def __init__(self) -> None:
        super().__init__()

    def get_token(self) -> str:
        response = self.get(settings.TOKEN_SERVICE_URL)
        if response.status_code != 200:
            raise AssertionError(
                f"Не удалось получить токен. Статус: {response.status_code}. Ответ: {response.text[:200]}"
            )
        data = response.json()
        token = data.get("token")
        if not token:
            raise AssertionError("В ответе отсутствует поле 'token'")
        self.logger.info("Токен авторизации успешно получен.")
        return token

    def get_auth_headers(self) -> dict:
        token = self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
