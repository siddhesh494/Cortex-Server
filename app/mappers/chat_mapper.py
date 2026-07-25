from typing import Any


class ChatMapper:

    @staticmethod
    def to_response(chat: dict[str, Any]):

        if not chat:
            return None

        return {
            "id": str(chat["_id"]),
            "userId": chat["userId"],
            "chatSessionName": chat["chatSessionName"],
            "summary": chat.get("summary"),
            "recentMessage": chat.get("recentMessage", [])
        }