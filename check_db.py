import sqlite3

def check_database():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    
    print("=== ユーザーテーブル ===")
    users = conn.execute('SELECT * FROM users').fetchall()
    for user in users:
        print(f"ID: {user['id']}, ユーザー名: {user['username']}")
    
    print("\n=== 商品テーブル ===")
    products = conn.execute('SELECT * FROM products').fetchall()
    for product in products:
        print(f"ID: {product['id']}, 商品名: {product['name']}, ユーザーID: {product['user_id']}")
    
    print("\n=== 在庫テーブル ===")
    stocks = conn.execute('SELECT * FROM stocks').fetchall()
    for stock in stocks:
        print(f"ID: {stock['id']}, 商品ID: {stock['product_id']}, 種類: {stock['type']}, 数量: {stock['qty']}, ユーザーID: {stock['user_id']}")
    
    conn.close()

if __name__ == '__main__':
    check_database() 