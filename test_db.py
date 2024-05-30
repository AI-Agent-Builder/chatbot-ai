import functools

import asyncpg
import asyncio
import config_db


# Декоратор для подключения к БД
def db_connection(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        dsn = f"postgresql://{config_db.DB_USER}:{config_db.DB_PASSWORD}@{config_db.DB_URL}:{config_db.DB_PORT}/{config_db.DB_NAME}"

        pool = await asyncpg.create_pool(dsn)

        try:
            async with pool.acquire() as connection:
                async with connection.transaction():
                    result = await func(connection, *args, **kwargs)
        finally:
            await pool.close()

        return result

    return wrapper


@db_connection
async def postr(connection):
    cursor1 = await connection.cursor(
        """
            SELECT *
            FROM traits;
        """
    )
    cursor2 = await connection.cursor(
        """
            SELECT *
            FROM expertises;
        """
    )
    result1 = await cursor1.fetch(1000)
    result2 = await cursor2.fetch(1000)
    return result1,result2


# async def postr():
#
#     lst = await is_exist_db()
#     return lst
#
# async def main():
#     db = await postr()
#     print(db)

#
# if __name__ == '__main__':
#      asyncio.run(main())