from bson import ObjectId
from app.db.database import mongodb


class ChatRepository:

    @property
    def collection(self):
        return mongodb.database["chatSession"]

    async def create_session(
        self,
        document: dict,
    ) -> str:
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def find_by_id(
        self,
        chat_session_id: str,
    ):
        return await self.collection.find_one(
            {
                "_id": ObjectId(chat_session_id)
            }
        )

    async def get_user_sessions(
        self,
        user_id: str,
    ):
        cursor = self.collection.find(
            {
                "user_id": user_id
            }
        )
        return await cursor.to_list(length=None)

    async def update_session(
        self,
        chat_session_id: str,
        update_data: dict,
    ):
        await self.collection.update_one(
            {
                "_id": ObjectId(chat_session_id)
            },
            {
                "$set": update_data
            }
        )

    async def delete_session(
        self,
        chat_session_id: str,
    ):
        await self.collection.delete_one(
            {
                "_id": ObjectId(chat_session_id)
            }
        )
        
    async def find_by_id_and_user(
        self,
        chat_session_id: str,
        user_id: str,
    ):

        return await self.collection.find_one(
            {
                "_id": ObjectId(chat_session_id),
                "user_id": user_id
            }
        )