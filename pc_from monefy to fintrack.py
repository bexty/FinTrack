import pandas, sqlite3
DB = './fintrack.db'
EXCEL = './20210424 monefy.xlsx'

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS purchases(
                            id INTEGER PRIMARY KEY,
                            name TEXT,
                            category TEXT,
                            price REAL,
                            date TEXT,
                            note TEXT)''')

cur.execute('''CREATE TABLE IF NOT EXISTS categories(
                            id INTEGER PRIMARY KEY,
                            name TEXT)''')

testDataCategories = [('Продукты', ),
                    ('Хозяйство', ),
                    ('Бытовая химия', ),
                    ('Анка', ),
                    ('Машина', ),
                    ('Фастфуд', ),
                    ('Бензин', ),
                    ('Долги', ),
                    ('Другое', ),
                    ('Жилье', ),
                    ('Здоровье', ),
                    ('Канцелярия', ),
                    ('Обед на работе', ),
                    ('Одежда', ),
                    ('Подарки', ),
                    ('Проезд', ),
                    ('Развлечения', ),
                    ('Саша', ),
                    ('Связь', ),
                    ('Списание', ),
                    ('Стрижка', )]

cur.executemany('INSERT INTO categories (name) VALUES(?)', testDataCategories)
conn.commit()
conn.close()

test = pandas.read_excel(EXCEL)

connection = sqlite3.connect(DB)
db = connection.cursor()

for x in range(len(test.index)):
    a = {'name':None, 'category':None,'price':None, 'date':None, 'note':None}

    if str(test.iloc[x]['name']) == 'nan':
        a['name'] = ''
    else:
        a['name'] = str(test.iloc[x]['name'])

    a['category'] = str(test.iloc[x]['category'])
    a['price'] = float(test.iloc[x]['price'])
    a['date'] = str(test.iloc[x]['date'])
    a['note'] = str(test.iloc[x]['note'])

    print(a)

    db.execute('INSERT INTO purchases (name, category, price, date, note) VALUES(?, ?, ?, ?, ?)', (a['name'], a['category'], a['price'], a['date'], a['note']))
    connection.commit()
connection.close()
print('done')