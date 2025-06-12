import asyncio
from prisma import Prisma

async def main():
    db = Prisma()
    await db.connect()

    user = await db.user.create(data={'email': 'dddoddoss@example.com', 'name': 'dododododododod'})
    print(user)

    await db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
