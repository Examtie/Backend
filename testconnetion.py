import asyncio
from prisma import Prisma

async def main():
    db = Prisma()
    await db.connect()

    user = await db.user.create(data={'email': 'alice@example.com', 'name': 'Alice'})
    print(user)

    await db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
