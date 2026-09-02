from fastapi import APIRouter, HTTPException, status
import aiosqlite, httpx, bcrypt
from schemas import SSAveToList

router = APIRouter()

async def api_get(url: str, search: str | None = None) -> dict:
    headers = {
            "Authorization": "Bearer HbH0BXkpJM02KKrJBjtAZBEl9rBTm5RpTFdyX06n",
            "Accept": "application/json"
        }
    if search:
        url+=f'search={search}&'

    async with httpx.AsyncClient() as client:
        result = await client.get(url, headers=headers)
    if result.is_error or not result.json()['data']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Bad input!')
    result_json = result.json()['data']
    if type(result_json) == list:
        return [{'id': product['id'], 'name': product['name'], 'price': product['current_price'], 'per_unit_price': product['current_unit_price'], 'shop': product['store']['name'], 'weight_unit': product['weight_unit'], 'weight': product['weight']} for product in result_json
                 if product['current_price'] and product['store'] and product['weight_unit'] and product['weight'] and product['weight'] >= 0.1]
    return {'id': result_json['id'], 'name': result_json['name'], 'price': result_json['current_price'], 'per_unit_price': result_json['current_unit_price'], 'shop': result_json['store']['name'], 'weight_unit': result_json['weight_unit'], 'weight': result_json['weight']}


@router.get('/get_products')
async def get_products(search: str | None = None):
    url = f'https://kassal.app/api/v1/products?'
    products = await api_get(url, search)
    products.sort(key=lambda x: x['price'])
    async with aiosqlite.connect('database.db') as cursor:
        stmt = await cursor.execute('SELECT id FROM products')
        stmt = await stmt.fetchall()
        prod = [int(*i) for i in stmt]
        for product in products:
            if not product['id'] in prod:
                await cursor.execute('INSERT INTO products VALUES(?, ?, ?, ?, ?, ?, ?)', (tuple(product.values())))
        await cursor.commit()
    return products

@router.post('/save_to_list')
async def save_to_db(schema: SSAveToList):
    result = []
    async with aiosqlite.connect('database.db') as cursor:
        stmt = await cursor.execute('SELECT id FROM users WHERE id=?', (schema.user_id,))
        user_fetched = await stmt.fetchone()
        if not user_fetched:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='No such user id in our database!')
        for i in schema.task_ids:
            stmt = await cursor.execute('SELECT * FROM products WHERE id=?', (i[0],))
            products_fetched = await stmt.fetchone()
            if not products_fetched:
                url = f'https://kassal.app/api/v1/products/id/{i[0]}'
                products = await api_get(url) 
                await cursor.execute('INSERT INTO products VALUES(?, ?, ?, ?, ?, ?, ?)', (*tuple(products.values()),))
                await cursor.commit()
                stmt = await cursor.execute('SELECT * FROM products WHERE id=?',(products['id'],))
                products_fetched = await stmt.fetchone()
            await cursor.execute('INSERT INTO shopping_list VALUES(?, ?, ?, ?, ?)', (products_fetched[0], products_fetched[1], i[1], schema.note, schema.user_id))
            result.append(products_fetched)
        await cursor.commit()
    return result

@router.get('/test')
async def test():
    result = []
    async with aiosqlite.connect('database.db') as cursor:
        stmt = await cursor.execute('SELECT * FROM products')
        result.append(await stmt.fetchall())
        stmt = await cursor.execute('SELECT * FROM shopping_list')
        result.append(await stmt.fetchall())
        stmt = await cursor.execute('SELECT * FROM users')
        result.append(await stmt.fetchall())
    return result

@router.post('/register', tags=['user'])
async def register(username: str, email: str, password: str):
    async with aiosqlite.connect('database.db') as cursor:
        stmt = await cursor.execute('SELECT * FROM users WHERE username=? OR email=?', (username, email))
        fetched = await stmt.fetchone()
        print(fetched)
        if fetched:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail='You are already registered!')
        salt = bcrypt.gensalt()
        bytes_password = password.encode()
        hash_pass = bcrypt.hashpw(bytes_password, salt)
        await cursor.execute('INSERT INTO users(username, email, password) VALUES (?, ?, ?)', (username, email, hash_pass))
        await cursor.commit()

@router.post('/login', tags=['user'])
async def login(username_or_email: str, password: str):
    async with aiosqlite.connect('database.db') as cursor:
        stmt = await cursor.execute('SELECT password FROM users WHERE username=? OR email=?', (username_or_email, username_or_email))
        user_db_pass = await stmt.fetchone()
        if not user_db_pass:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Wrong password or email!')
        in_pass=password.encode()
        if bcrypt.checkpw(in_pass, *user_db_pass):
            return {'msg': 'success'}
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Wrong password!')

@router.get('/my_list/{user_id}')
async def get_my_list(user_id):
    async with aiosqlite.connect('database.db') as cursor:
        stmt = await cursor.execute('SELECT * FROM shopping_list WHERE user_id=?', (user_id,))
        result = await stmt.fetchall()
        return result