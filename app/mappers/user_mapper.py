from typing import Any


class UserMapper:

    @staticmethod
    def to_response(user: dict[str, Any]) -> dict:

        if not user:
            return None

        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "createdAt": user.get("created_at"),
            "updatedAt": user.get("updated_at")
        }

    @staticmethod
    def to_auth_response(
        user: dict[str, Any],
        token: str
    ):

        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "token": token
        }