from flask import Flask, render_template, request, redirect, url_for, flash
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
    name_query = request.args.get('name', '').strip()
    sku_query = request.args.get('sku', '').strip()
    conn = get_db_connection()
    query = '''
        SELECT
            p.*,
            IFNULL(
                (SELECT SUM(CASE WHEN type='in' THEN qty ELSE 0 END) FROM stocks WHERE product_id = p.id), 0
            ) -
            IFNULL(
                (SELECT SUM(CASE WHEN type='out' THEN qty ELSE 0 END) FROM stocks WHERE product_id = p.id), 0
            ) AS stock_quantity
        FROM products p
        WHERE 1=1
    '''
    params = []
    if name_query:
        query += ' AND p.name LIKE ?'
        params.append(f'%{name_query}%')
    if sku_query:
        query += ' AND p.sku LIKE ?'
        params.append(f'%{sku_query}%')
    products = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('products.html', products=products, name_query=name_query, sku_query=sku_query)

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

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        unit = request.form['unit']
        conn.execute('UPDATE products SET name=?, sku=?, unit=? WHERE id=?', (name, sku, unit, product_id))
        conn.commit()
        conn.close()
        return redirect(url_for('products'))
    product = conn.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
    conn = get_db_connection()
    if request.method == 'POST':
        conn.execute('DELETE FROM products WHERE id=?', (product_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('products'))
    product = conn.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
    conn.close()
    return render_template('confirm_delete.html', product=product)

@app.route('/product_history/<int:product_id>')
def product_history(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
    history = conn.execute('SELECT * FROM stocks WHERE product_id=? ORDER BY rowid DESC', (product_id,)).fetchall()
    conn.close()
    return render_template('history.html', product=product, history=history)

@app.route('/adjust_stock/<int:product_id>', methods=['GET', 'POST'])
def adjust_stock(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
    # 現在庫数を計算
    stock_row = conn.execute('''
        SELECT
            IFNULL((SELECT SUM(CASE WHEN type='in' THEN qty ELSE 0 END) FROM stocks WHERE product_id = ?), 0) -
            IFNULL((SELECT SUM(CASE WHEN type='out' THEN qty ELSE 0 END) FROM stocks WHERE product_id = ?), 0) AS stock_quantity
    ''', (product_id, product_id)).fetchone()
    current_stock = stock_row['stock_quantity'] if stock_row else 0
    if request.method == 'POST':
        new_stock = int(request.form['new_stock'])
        diff = new_stock - current_stock
        if diff != 0:
            if diff > 0:
                conn.execute('INSERT INTO stocks (product_id, type, qty, note) VALUES (?, ?, ?, ?)', (product_id, 'in', diff, '在庫調整'))
            else:
                conn.execute('INSERT INTO stocks (product_id, type, qty, note) VALUES (?, ?, ?, ?)', (product_id, 'out', -diff, '在庫調整'))
            conn.commit()
        conn.close()
        return redirect(url_for('products'))
    conn.close()
    return render_template('adjust_stock.html', product=product, current_stock=current_stock)

if __name__ == '__main__':
    app.run(debug=True)
