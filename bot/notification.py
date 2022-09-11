from datetime import datetime
from aiohttp import ClientSession

from .search import CourseData


PAYLOAD = {
    "DISCORD": {
        "SELECT_SUCCESS": {
            "content": None,
            "embeds": [
                {
                    "title": "✅ D1234567 已成功加選 1356 班級活動",
                    "color": 5685812,
                    "fields": [{"name": "目前學分", "value": "23 / 25"}],
                    "author": {"name": "幹課大師"},
                    "timestamp": "2022-09-10T14:41:00.000Z",
                }
            ],
            "username": "幹課大師",
            "attachments": [],
        }
    },
    "LINE": {"SELECT_SUCCESS": {}},
}


class DiscordNotification:
    def __init__(self, session: ClientSession, webhook: str):
        self.session = session
        self.webhook = webhook

    async def select_successful(self, username: str, course_data: CourseData, max_credit: int, current_credit: int):
        await self.session.post(
            self.webhook,
            json={
                "embeds": [
                    {
                        "title": f"✅ {username} 已成功加選 {course_data.id} {course_data.name}",
                        "color": 5685812,
                        "fields": [
                            {
                                "name": "課程資訊",
                                "value": f"{course_data.period}\n[課程大綱]({course_data.url})",
                            },
                            {
                                "name": "目前學分",
                                "value": f"{current_credit} / {max_credit}",
                            },
                        ],
                        "author": {"name": "幹課大師"},
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
                "username": "幹課大師",
                "avatar_url": "https://cdn.discordapp.com/icons/1006153693315465248/1a6670cfeea62fb9b333aee0999c739e.webp",
            },
        )

    async def error(self, username: str, message: str):
        await self.session.post(
            self.webhook,
            json={
                "embeds": [
                    {
                        "title": f"⚠️ {username} 發生錯誤",
                        "description": message,
                        "color": 15411497,
                        "author": {"name": "幹課大師"},
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
                "username": "幹課大師",
                "avatar_url": "https://cdn.discordapp.com/icons/1006153693315465248/1a6670cfeea62fb9b333aee0999c739e.webp",
            },
        )


class LineNotification:
    def __init__(self, session: ClientSession, webhook: str):
        self.session = session
        self.webhook = webhook

    async def select_successful(self, username: str, course_data: CourseData, max_credit: int, current_credit: int):
        await self.session.post(
            "https://notify-api.line.me/api/notify",
            headers={"Authorization": f"Bearer {self.webhook}"},
            data={
                "message": f"✅ {username} 已成功加選 {course_data.id} {course_data.name}，目前學分：{current_credit} / {max_credit}",
            },
        )

    async def error(self, username: str, message: str):
        await self.session.post(
            "https://notify-api.line.me/api/notify",
            headers={"Authorization": f"Bearer {self.webhook}"},
            data={
                "message": f"⚠️ {username} 發生錯誤，{message}",
            },
        )


class Notification:
    def __init__(self, username: str, webhook: str):
        self.session = ClientSession()
        self.username = username
        self.webhook = webhook
        self.handler = (
            DiscordNotification(self.session, self.webhook)
            if self.webhook.startswith("https://discord")
            else LineNotification(self.session, self.webhook)
        )

    async def select_successful(self, course_data: CourseData, max_credit: int, current_credit: int):
        await self.handler.select_successful(self.username, course_data, max_credit, current_credit)

    async def error(self, message: str):
        await self.handler.error(self.username, message)

    async def stoped(self, message: str):
        await self.handler.error(self.username, message)