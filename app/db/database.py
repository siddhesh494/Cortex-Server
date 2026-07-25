from motor.motor_asyncio import AsyncIOMotorClient
import certifi
from app.config import settings


class MongoDB:

    client: AsyncIOMotorClient | None = None

    async def connect(self):

        self.client = AsyncIOMotorClient(
            settings.MONGO_URI,
            tlsCAFile=certifi.where()
        )

        print("MongoDB Connected")

    async def close(self):

        if self.client:
            self.client.close()

            print("MongoDB Closed")

    @property
    def database(self):

        return self.client[settings.DATABASE_NAME]


mongodb = MongoDB()