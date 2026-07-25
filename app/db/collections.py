from app.db.database import mongodb


def users_collection():
    return mongodb.database["users"]


def chat_sessions_collection():
    return mongodb.database["chat_sessions"]