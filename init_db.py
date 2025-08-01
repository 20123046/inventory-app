# init_db.py

import sqlite3
import os

def init_database():
    try:
        # DBファイルを作成／接続
        conn = sqlite3.connect('inventory.db')
        
        # schema.sql を読み込んで実行
        with open('schema.sql', 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        
        conn.commit()
        conn.close()
        
        print("データベースを初期化しました（inventory.db）")
        
        # データベースファイルの存在確認
        if os.path.exists('inventory.db'):
            print("✓ データベースファイルが正常に作成されました")
        else:
            print("✗ データベースファイルの作成に失敗しました")
            
    except FileNotFoundError:
        print("エラー: schema.sqlファイルが見つかりません")
    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
    except Exception as e:
        print(f"予期しないエラー: {e}")

if __name__ == '__main__':
    init_database()
