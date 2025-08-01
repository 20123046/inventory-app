import sqlite3
import os

def check_database():
    try:
        # データベースファイルの存在確認
        if not os.path.exists('inventory.db'):
            print("エラー: inventory.dbファイルが見つかりません")
            print("python init_db.py を実行してデータベースを初期化してください")
            return
        
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        
        print("=== データベース接続確認 ===")
        print("✓ データベースに正常に接続しました")
        
        # テーブル一覧を確認
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n=== テーブル一覧 ===")
        for table in tables:
            print(f"- {table[0]}")
        
        print("\n=== ユーザーテーブル ===")
        try:
            users = conn.execute('SELECT * FROM users').fetchall()
            if users:
                for user in users:
                    print(f"ID: {user['id']}, ユーザー名: {user['username']}, グループID: {user['group_id']}")
            else:
                print("ユーザーが登録されていません")
        except sqlite3.Error as e:
            print(f"ユーザーテーブルエラー: {e}")
        
        print("\n=== グループテーブル ===")
        try:
            groups = conn.execute('SELECT * FROM groups').fetchall()
            if groups:
                for group in groups:
                    print(f"ID: {group['id']}, グループ名: {group['name']}")
            else:
                print("グループが登録されていません")
        except sqlite3.Error as e:
            print(f"グループテーブルエラー: {e}")
        
        print("\n=== 商品テーブル ===")
        try:
            products = conn.execute('SELECT * FROM products').fetchall()
            if products:
                for product in products:
                    print(f"ID: {product['id']}, 商品名: {product['name']}, 作成者ID: {product['created_by']}, グループID: {product['group_id']}")
            else:
                print("商品が登録されていません")
        except sqlite3.Error as e:
            print(f"商品テーブルエラー: {e}")
        
        print("\n=== 在庫テーブル ===")
        try:
            stocks = conn.execute('SELECT * FROM stocks').fetchall()
            if stocks:
                for stock in stocks:
                    print(f"ID: {stock['id']}, 商品ID: {stock['product_id']}, 種類: {stock['type']}, 数量: {stock['qty']}, 作成者ID: {stock['created_by']}, グループID: {stock['group_id']}")
            else:
                print("在庫履歴がありません")
        except sqlite3.Error as e:
            print(f"在庫テーブルエラー: {e}")
        
        conn.close()
        print("\n✓ データベースチェックが完了しました")
        
    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
    except Exception as e:
        print(f"予期しないエラー: {e}")

if __name__ == '__main__':
    check_database() 