import sqlite3
from datetime import datetime

def fix_database():
    try:
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        
        print("=== データベース修復開始 ===")
        
        # 孤立した在庫データを削除
        print("孤立した在庫データを削除中...")
        conn.execute('''
            DELETE FROM stocks 
            WHERE product_id NOT IN (SELECT id FROM products)
        ''')
        deleted_count = conn.execute('SELECT changes()').fetchone()[0]
        print(f"削除された在庫レコード数: {deleted_count}")
        
        # テスト用の商品を追加
        print("\nテスト用の商品を追加中...")
        
        # グループID 1（デフォルトグループ）に商品を追加
        test_products = [
            ('テスト商品1', 'TEST001', '個', 10, 1, 1),
            ('テスト商品2', 'TEST002', '箱', 5, 1, 1),
            ('テスト商品3', 'TEST003', '本', 20, 1, 1)
        ]
        
        for name, sku, unit, min_qty, group_id, created_by in test_products:
            conn.execute('''
                INSERT INTO products (name, sku, unit, min_qty, group_id, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, sku, unit, min_qty, group_id, created_by, datetime.now()))
        
        # テスト用の在庫データを追加
        print("テスト用の在庫データを追加中...")
        products = conn.execute('SELECT id FROM products WHERE group_id = 1').fetchall()
        
        for product in products:
            product_id = product['id']
            # 入庫データ
            conn.execute('''
                INSERT INTO stocks (product_id, type, qty, note, group_id, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (product_id, 'in', 50, '初期在庫', 1, 1, datetime.now()))
            
            # 出庫データ
            conn.execute('''
                INSERT INTO stocks (product_id, type, qty, note, group_id, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (product_id, 'out', 10, 'テスト出庫', 1, 1, datetime.now()))
        
        conn.commit()
        print("✓ データベース修復が完了しました")
        
        # 修復後の確認
        print("\n=== 修復後の確認 ===")
        products = conn.execute('SELECT * FROM products').fetchall()
        print(f"商品数: {len(products)}")
        for product in products:
            print(f"  - {product['name']} (ID: {product['id']})")
        
        stocks = conn.execute('SELECT * FROM stocks').fetchall()
        print(f"在庫レコード数: {len(stocks)}")
        
        conn.close()
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == '__main__':
    fix_database() 