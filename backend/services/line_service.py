import os

import httpx

from logger import logger


class LineService:
    def __init__(self) -> None:
        self.line_notify_token = os.getenv("LINE_NOTIFY_TOKEN")
        self.line_notify_url = "https://notify-api.line.me/api/notify"

    async def send_notification(self, message: str) -> bool:
        """
        Send a notification to LINE Notify.
        """
        if not self.line_notify_token:
            logger.warning("LINE_NOTIFY_TOKEN not set. Skipping LINE notification.")
            logger.debug(f"LINE NOTIFICATION MOCK: {message}")
            return True

        try:
            headers = {
                "Authorization": f"Bearer {self.line_notify_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            payload = {"message": message}

            async with httpx.AsyncClient() as client:
                response = await client.post(self.line_notify_url, headers=headers, data=payload, timeout=10.0)

                if response.status_code == 200:
                    logger.info("LINE notification sent successfully")
                    return True
                logger.error(f"Failed to send LINE notification: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending LINE notification: {e}")
            return False


line_service = LineService()
