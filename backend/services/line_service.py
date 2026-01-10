import os
from typing import Optional

import aiohttp


class LineProfileClient:
    """Client for fetching user profile from LINE Messaging API"""

    def __init__(self, channel_access_token: Optional[str] = None):
        self.channel_access_token = channel_access_token or os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
        self.userinfo_endpoint = "https://api.line.biz/v2/bot/profile"

        if not self.channel_access_token:
            raise ValueError("LINE_CHANNEL_ACCESS_TOKEN environment variable not set")

    async def get_user_profile(self, user_id: str) -> dict:
        """
        Fetch user profile from LINE Messaging API.

        Args:
            user_id: LINE user ID

        Returns:
            Dict containing displayName, pictureUrl, statusMessage (or empty if not available)

        Raises:
            Exception: If API call fails
        """
        url = f"{self.userinfo_endpoint}/{user_id}"
        headers = {
            "Authorization": f"Bearer {self.channel_access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Failed to get user profile: {resp.status} {error_text}")

                    user_info = await resp.json()
                    return {
                        "display_name": user_info.get("displayName"),
                        "picture_url": user_info.get("pictureUrl"),
                        "status_message": user_info.get("statusMessage"),
                    }
        except Exception as e:
            print(f"Error fetching LINE user profile: {e}")
            raise


async def get_line_profile(user_id: str) -> Optional[dict]:
    """
    Fetch LINE user profile.

    Args:
        user_id: LINE user ID

    Returns:
        Dict with display_name, picture_url, status_message or None if fetch fails
    """
    try:
        client = LineProfileClient()
        return await client.get_user_profile(user_id)
    except Exception as e:
        print(f"Error getting LINE profile: {e}")
        return None
