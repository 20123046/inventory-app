import sqlite3
import os

def check_products():
    try:
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        
        print("=== 商品テーブル詳細確認 ===")
        
        # 商品テーブルの構造確認
        cursor = conn.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        print("商品テーブルのカラム:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # 商品データの確認
        products = conn.execute('SELECT * FROM products').fetchall()
        print(f"\n商品数: {len(products)}")
        
        if products:
            for product in products:
                print(f"\n商品ID: {product['id']}")
                print(f"  商品名: {product['name']}")
                print(f"  SKU: {product['sku']}")
                print(f"  単位: {product['unit']}")
                print(f"  最低在庫数: {product['min_qty']}")
                print(f"  画像URL: {product['image_url']}")
                print(f"  グループID: {product['group_id']}")
                print(f"  作成者ID: {product['created_by']}")
                print(f"  作成日: {product['created_at']}")
        else:
            print("商品が登録されていません")
        
        # 在庫テーブルとの関連確認
        print("\n=== 在庫テーブルとの関連 ===")
        stocks = conn.execute('SELECT DISTINCT product_id FROM stocks').fetchall()
        if stocks:
            print("在庫テーブルに存在する商品ID:")
            for stock in stocks:
                print(f"  - 商品ID: {stock['product_id']}")
        else:
            print("在庫テーブルにデータがありません")
        
        conn.close()
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == '__main__':
    check_products() 