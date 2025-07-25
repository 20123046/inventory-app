from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return '在庫管理アプリへようこそ！'

@app.route('/products')
def products():
    conn = get_db_connection()
    products = conn.execute('''
        SELECT
            p.*,
            IFNULL(
                (SELECT SUM(CASE WHEN type='in' THEN qty ELSE 0 END) FROM stocks WHERE product_id = p.id), 0
            ) -
            IFNULL(
                (SELECT SUM(CASE WHEN type='out' THEN qty ELSE 0 END) FROM stocks WHERE product_id = p.id), 0
            ) AS stock_quantity
        FROM products p
    ''').fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        unit = request.form['unit']

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO products (name, sku, unit) VALUES (?, ?, ?)',
            (name, sku, unit)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('products'))

    return render_template('add_product.html')
@app.route('/stock', methods=['GET', 'POST'])

def stock():
    conn = get_db_connection()

    # 商品一覧を取得（セレクトボックス用）
    products = conn.execute('SELECT * FROM products').fetchall()

    if request.method == 'POST':
        product_id = request.form['product_id']
        type_ = request.form['type']
        qty = int(request.form['qty'])
        note = request.form['note']

        conn.execute(
            'INSERT INTO stocks (product_id, type, qty, note) VALUES (?, ?, ?, ?)',
            (product_id, type_, qty, note)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('stock'))

    conn.close()
    return render_template('stock.html', products=products)
if __name__ == '__main__':
    app.run(debug=True)
