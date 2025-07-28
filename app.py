from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 本番環境では環境変数から取得

# Flask-Login設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'])
    return None

def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('products'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(user['id'], user['username'])
            login_user(user_obj)
            return redirect(url_for('products'))
        flash('ユーザー名またはパスワードが正しくありません')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            flash('このユーザー名は既に使用されています')
            conn.close()
            return render_template('register.html')
        password_hash = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        conn.close()
        flash('ユーザー登録が完了しました。ログインしてください。')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/products')
@login_required
def products():
    name_query = request.args.get('name', '').strip()
    sku_query = request.args.get('sku', '').strip()
    conn = get_db_connection()
    query = '''
        SELECT
            p.*,
            IFNULL(
                (SELECT SUM(CASE WHEN type='in' THEN qty ELSE 0 END) FROM stocks WHERE product_id = p.id AND user_id = ?), 0
            ) -
            IFNULL(
                (SELECT SUM(CASE WHEN type='out' THEN qty ELSE 0 END) FROM stocks WHERE product_id = p.id AND user_id = ?), 0
            ) AS stock_quantity
        FROM products p
        WHERE p.user_id = ?
    '''
    params = [current_user.id, current_user.id, current_user.id]
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
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        unit = request.form['unit']
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO products (name, sku, unit, user_id) VALUES (?, ?, ?, ?)',
            (name, sku, unit, current_user.id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('products'))
    return render_template('add_product.html')

@app.route('/stock', methods=['GET', 'POST'])
@login_required
def stock():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE user_id = ?', (current_user.id,)).fetchall()
    if request.method == 'POST':
        product_id = request.form['product_id']
        type_ = request.form['type']
        qty = int(request.form['qty'])
        note = request.form['note']
        conn.execute(
            'INSERT INTO stocks (product_id, type, qty, note, user_id) VALUES (?, ?, ?, ?, ?)',
            (product_id, type_, qty, note, current_user.id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('stock'))
    conn.close()
    return render_template('stock.html', products=products)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id=? AND user_id=?', (product_id, current_user.id)).fetchone()
    if not product:
        conn.close()
        return redirect(url_for('products'))
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        unit = request.form['unit']
        conn.execute('UPDATE products SET name=?, sku=?, unit=? WHERE id=? AND user_id=?', (name, sku, unit, product_id, current_user.id))
        conn.commit()
        conn.close()
        return redirect(url_for('products'))
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def delete_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id=? AND user_id=?', (product_id, current_user.id)).fetchone()
    if not product:
        conn.close()
        return redirect(url_for('products'))
    if request.method == 'POST':
        conn.execute('DELETE FROM products WHERE id=? AND user_id=?', (product_id, current_user.id))
        conn.commit()
        conn.close()
        return redirect(url_for('products'))
    conn.close()
    return render_template('confirm_delete.html', product=product)

@app.route('/product_history/<int:product_id>')
@login_required
def product_history(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id=? AND user_id=?', (product_id, current_user.id)).fetchone()
    if not product:
        conn.close()
        return redirect(url_for('products'))
    history = conn.execute('SELECT * FROM stocks WHERE product_id=? AND user_id=? ORDER BY rowid DESC', (product_id, current_user.id)).fetchall()
    conn.close()
    return render_template('history.html', product=product, history=history)

@app.route('/adjust_stock/<int:product_id>', methods=['GET', 'POST'])
@login_required
def adjust_stock(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id=? AND user_id=?', (product_id, current_user.id)).fetchone()
    if not product:
        conn.close()
        return redirect(url_for('products'))
    stock_row = conn.execute('''
        SELECT
            IFNULL((SELECT SUM(CASE WHEN type='in' THEN qty ELSE 0 END) FROM stocks WHERE product_id = ? AND user_id = ?), 0) -
            IFNULL((SELECT SUM(CASE WHEN type='out' THEN qty ELSE 0 END) FROM stocks WHERE product_id = ? AND user_id = ?), 0) AS stock_quantity
    ''', (product_id, current_user.id, product_id, current_user.id)).fetchone()
    current_stock = stock_row['stock_quantity'] if stock_row else 0
    if request.method == 'POST':
        new_stock = int(request.form['new_stock'])
        diff = new_stock - current_stock
        if diff != 0:
            if diff > 0:
                conn.execute('INSERT INTO stocks (product_id, type, qty, note, user_id) VALUES (?, ?, ?, ?, ?)', (product_id, 'in', diff, '在庫調整', current_user.id))
            else:
                conn.execute('INSERT INTO stocks (product_id, type, qty, note, user_id) VALUES (?, ?, ?, ?, ?)', (product_id, 'out', -diff, '在庫調整', current_user.id))
            conn.commit()
        conn.close()
        return redirect(url_for('products'))
    conn.close()
    return render_template('adjust_stock.html', product=product, current_stock=current_stock)

if __name__ == '__main__':
    app.run(debug=True)
