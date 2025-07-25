# init_db.py

import sqlite3

# DBファイルを作成／接続
conn = sqlite3.connect('inventory.db')

# schema.sql を読み込んで実行
with open('schema.sql', 'r', encoding='utf-8') as f:
    conn.executescript(f.read())

conn.commit()
conn.close()

print("データベースを初期化しました（inventory.db）")
