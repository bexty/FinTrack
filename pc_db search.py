import sqlite3
from prettytable import from_db_cursor

DB = './fintrack.db'

c = input('Что ищем?\n')

a = c.lower()
b = a.capitalize()

connection = sqlite3.connect(DB)
db = connection.cursor()
transactions = db.execute('''SELECT id as Id,
    name as name,
    date as date,
    price as price,
    category as category,
    note as note
    FROM purchases
    WHERE name LIKE ? OR name LIKE ?
    ORDER BY date DESC''', ('%{}%'.format(a), '%{}%'.format(b)))
table = from_db_cursor(db)
table.align = 'l'
connection.close()
print(table)
