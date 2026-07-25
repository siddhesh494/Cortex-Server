from bson import ObjectId

from app.db.collections import users_collection


class UserRepository:

    @staticmethod
    async def find_by_email(email: str):

        return await users_collection().find_one({
            "email": email
        })

    @staticmethod
    async def find_by_id(user_id: str):

        return await users_collection().find_one({
            "_id": ObjectId(user_id)
        })

    @staticmethod
    async def create(user: dict):

        result = await users_collection().insert_one(user)

        return str(result.inserted_id)

    @staticmethod
    async def update(user_id: str, data: dict):

        return await users_collection().update_one(
            {
                "_id": ObjectId(user_id)
            },
            {
                "$set": data
            }
        )

    @staticmethod
    async def delete(user_id: str):

        return await users_collection().delete_one({
            "_id": ObjectId(user_id)
        })