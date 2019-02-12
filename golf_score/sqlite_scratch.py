import sqlite3

con = sqlite3.connect('/home/pi/golf.db')
cur = con.cursor()
q = '''
select * from players
'''
cur.execute(q)
print(cur.fetchall())
q = '''
select * from shots
'''
cur.execute(q)
print(cur.fetchall())
con.close()
