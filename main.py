from fastapi import FastAPI
from contextlib import asynccontextmanager
import aiosqlite
from endpoints import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('start')
    async with aiosqlite.connect('database.db') as cursor:
        await cursor.execute('CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price FLOAT, per_unit_price FLOAT, weight FLOAT, weight_unit TEXT, shop TEXT)')
        await cursor.execute('CREATE TABLE IF NOT EXISTS shopping_list(id INTEGER, name TEXT, quantity TEXT, note TEXT, user_id INTEGER NOT NULL)')
        await cursor.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, email TEXT NOT NULL, password TEXT NOT NULL)')
        await cursor.commit()
    yield
    print('end')

app = FastAPI(lifespan=lifespan, title='Levia app', description='Finds the best prices of products in your shopping list.', version='1.0.0')

app.include_router(router)