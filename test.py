import sqlite3

conn = sqlite3.connect('logSensor.db')
cur = conn.cursor()
cur.execute('select * from sensor')
rs = cur.fetchall()

for row in rs:
    print(row)