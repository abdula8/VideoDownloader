import sqlite3, os
p=r'd:/scripts/youtubedownloader/development-env-last-code-with-full-features-working/download_history.db'
print('DB path', p)
print('DB exists?', os.path.exists(p))
conn=sqlite3.connect(p)
cur=conn.cursor()
cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='downloads'")
print('downloads table exists?', cur.fetchone()[0]==1)
try:
    cur.execute('SELECT id, url, title, status, download_date FROM downloads ORDER BY download_date DESC LIMIT 5')
    rows=cur.fetchall()
    print('rows sample:', rows)
except Exception as e:
    print('select failed', e)
conn.close()