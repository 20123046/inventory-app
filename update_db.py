# update_db.py

import sqlite3

def update_database():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    try:
        # productsテーブルにimage_urlカラムを追加
        cursor.execute('ALTER TABLE products ADD COLUMN image_url TEXT')
        print("image_urlカラムを追加しました")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("image_urlカラムは既に存在します")
        else:
            print(f"エラー: {e}")
    
    conn.commit()
    conn.close()
    print("データベースの更新が完了しました")

if __name__ == '__main__':
    update_database() 