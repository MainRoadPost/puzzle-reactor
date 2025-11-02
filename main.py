#!/usr/bin/env python3
"""
Пример приложения-реактора для работы с Puzzle API.

Демонстрирует:
- Аутентификацию через GraphQL
- Выполнение GraphQL запросов (получение списка проектов)
- WebSocket подписки для отслеживания изменений в реальном времени
"""

import asyncio
import os
import logging

from dotenv import load_dotenv

# Импортируем патченый клиент Puzzle и связанные классы
# Патч добавляет поддержку WebSocket подписок к базовому клиенту ariadne-codegen
from puzzle_client_patched import PuzzleClient
from puzzle.exceptions import GraphQLClientHttpError
from puzzle.get_projects import GetProjectsProjects

# Настройка логирования для вывода информационных сообщений
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")


class PuzzleReactor:
    """Обрабатывает взаимодействие с Puzzle API для реакции на события.

    Класс отвечает за:
    - Авторизацию в системе Puzzle через GraphQL
    - Получение списка активных проектов через GraphQL запросы
    - Мониторинг изменений проектов и продуктов через WebSocket подписки
    """

    def __init__(self):
        """Инициализирует клиент Puzzle с HTTP и WebSocket подключениями."""
        load_dotenv()  # Загружаем переменные окружения из .env файла

        PUZZLE_API = os.getenv("PUZZLE_API")
        if not PUZZLE_API:
            raise ValueError("PUZZLE_API environment variable is not set.")

        # Формируем WebSocket URL из HTTP URL (http -> ws, /api/graphql -> /api/graphql/ws)
        ws_url = PUZZLE_API.replace("http", "ws").replace(
            "/api/graphql", "/api/graphql/ws"
        )

        # Создаем клиент с поддержкой как HTTP запросов, так и WebSocket подписок
        self.client = PuzzleClient(url=PUZZLE_API, ws_url=ws_url)

    async def login(self):
        """Выполняет аутентификацию в Puzzle API через GraphQL мутацию.

        Returns:
            bool: True если аутентификация успешна, False в противном случае.
        """
        domain = os.getenv("PUZZLE_USER_DOMAIN")
        username = os.getenv("PUZZLE_USERNAME")
        password = os.getenv("PUZZLE_PASSWORD")

        # Проверяем наличие всех необходимых учетных данных
        if username is None or password is None:
            logging.error("Login failed: Missing credentials.")
            return False

        try:
            response = await self.client.login(
                domain_name=domain if domain and len(domain) > 0 else None,
                username=username,
                password=password,
            )

            if response.login:
                # После успешной аутентификации cookie автоматически сохраняется
                # в http_client.cookies и будет использоваться для всех последующих
                # HTTP запросов и WebSocket подключений
                logging.info("Login successful.")
                return True
            else:
                logging.error("Login failed.")
                return False
        except GraphQLClientHttpError as e:
            logging.error(f"Login failed: {e.response}")
            return False

    async def fetch_projects(self) -> list[GetProjectsProjects]:
        """Получает список активных проектов через GraphQL запрос.

        Returns:
            list[GetProjectsProjects]: Список активных проектов (с done_at = None).
        """
        try:
            response = await self.client.get_projects()
            if response.projects:
                # Фильтруем только активные проекты (у которых done_at пустое)
                # Это проекты, которые еще не завершены
                active_projects = [p for p in response.projects if p.done_at is None]

                return active_projects
            else:
                logging.error("Failed to fetch projects.")
                return []
        except GraphQLClientHttpError as e:
            logging.error(f"Error fetching projects: {e.response}")
            return []

    async def run(self):
        """Запускает основной процесс приложения.

        Выполняет аутентификацию, затем создает WebSocket подписки для мониторинга
        изменений проектов и продуктов в реальном времени.
        """
        # Сначала выполняем аутентификацию
        if not await self.login():
            return

        # Опциональный пример: можно получить список активных проектов
        # active_projects = await self.fetch_projects()
        # if not active_projects:
        #     return
        #
        # # Обработка полученных проектов
        # for project in active_projects:
        #     logging.info(f"Processing project: {project.title}")

        # Создаем обработчики для WebSocket подписок
        async def handle_projects():
            """Обрабатывает события обновления проектов через WebSocket."""
            async for projectUpdated in self.client.on_projects_updated():
                logging.info(f"Project updated: {projectUpdated}")

        async def handle_products():
            """Обрабатывает события обновления продуктов через WebSocket."""
            async for productsUpdated in self.client.on_products_updated():
                logging.info(f"Products updated: {productsUpdated}")

        # Запускаем обе подписки параллельно
        # Обе будут работать одновременно, реагируя на события в реальном времени
        await asyncio.gather(handle_projects(), handle_products())


if __name__ == "__main__":
    app = PuzzleReactor()
    asyncio.run(app.run())
