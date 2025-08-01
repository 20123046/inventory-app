from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import boto3
from PIL import Image
import io
import os
from datetime import datetime
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# AWS S3設定
try:
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'ap-northeast-1')
    s3_bucket_name = os.getenv('S3_BUCKET_NAME', 'inventory-app-images8')
    
    print(f"環境変数読み込み状況:")
    print(f"  AWS_ACCESS_KEY_ID: {'設定済み' if aws_access_key else '未設定'}")
    print(f"  AWS_SECRET_ACCESS_KEY: {'設定済み' if aws_secret_key else '未設定'}")
    print(f"  AWS_REGION: {aws_region}")
    print(f"  S3_BUCKET_NAME: {s3_bucket_name}")
    
    if aws_access_key and aws_secret_key:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        s3_client.upload_fileobj('file_data', 'your-bucket-name', 'file.jpg')
        S3_BUCKET_NAME = s3_bucket_name
        S3_AVAILABLE = True
        print(f"AWS S3設定完了: バケット名={S3_BUCKET_NAME}")
        
        # S3バケットの存在確認
        try:
            s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
            print(f"✓ S3バケット '{S3_BUCKET_NAME}' にアクセス可能")
        except Exception as e:
            print(f"✗ S3バケット '{S3_BUCKET_NAME}' にアクセスできません: {e}")
            S3_AVAILABLE = False
    else:
        print("AWS認証情報が設定されていません")
        s3_client = None
        S3_BUCKET_NAME = None
        S3_AVAILABLE = False
except Exception as e:
    print(f"AWS S3設定エラー: {e}")
    s3_client = None
    S3_BUCKET_NAME = None
    S3_AVAILABLE = False

# Flask-Login設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, email, group_id, is_admin):
        self.id = id
        self.username = username
        self.email = email
        self.group_id = group_id
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    try:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            return User(user['id'], user['username'], user['email'], user['group_id'], user['is_admin'])
    except Exception as e:
        print(f"ユーザー読み込みエラー: {e}")
    finally:
        conn.close()
    return None

def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_default_group():
    """デフォルトグループを作成"""
    conn = get_db_connection()
    try:
        # グループが存在しない場合は作成
        existing_group = conn.execute('SELECT * FROM groups').fetchone()
        if not existing_group:
            conn.execute('INSERT INTO groups (name, description) VALUES (?, ?)', ('デフォルトグループ', 'システム初期化時に作成されたグループ'))
            conn.commit()
            group_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            return group_id
        return existing_group['id']
    except Exception as e:
        print(f"デフォルトグループ作成エラー: {e}")
        return None
    finally:
        conn.close()

def upload_image_to_s3(image_file, product_id):
    """画像をS3にアップロード"""
    if not S3_AVAILABLE:
        print("AWS S3が利用できません")
        # ローカルファイルとして保存する代替処理
        try:
            import os
            upload_folder = 'static/uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            # ファイル名を生成
            file_extension = image_file.filename.rsplit('.', 1)[1].lower() if '.' in image_file.filename else 'jpg'
            file_name = f"product_{product_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
            file_path = os.path.join(upload_folder, file_name)
            
            # 画像をリサイズして保存
            image = Image.open(image_file)
            image.thumbnail((300, 300))
            image.save(file_path, quality=85)
            
            # 相対URLを返す
            image_url = f"/static/uploads/{file_name}"
            print(f"ローカルファイル保存成功: {image_url}")
            return image_url
        except Exception as e:
            print(f"ローカルファイル保存エラー: {e}")
            return None
    
    try:
        print(f"画像アップロード開始: 商品ID={product_id}")
        print(f"S3設定: バケット={S3_BUCKET_NAME}, リージョン={aws_region}")
        
        # 画像をリサイズ
        image = Image.open(image_file)
        print(f"画像サイズ: {image.size}")
        image.thumbnail((300, 300))  # 最大300x300にリサイズ
        print(f"リサイズ後サイズ: {image.size}")
        
        # 画像をバイトデータに変換
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr.seek(0)
        
        # S3にアップロード
        file_name = f"product_{product_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        print(f"アップロードファイル名: {file_name}")
        
        s3_client.upload_fileobj(
            img_byte_arr,
            S3_BUCKET_NAME,
            file_name,
            ExtraArgs={
                'ContentType': 'image/jpeg',
                'ACL': 'public-read'  # パブリック読み取りを許可
            }
        )
        
        # S3のURLを返す
        image_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file_name}"
        print(f"画像アップロード成功: {image_url}")
        return image_url
    except Exception as e:
        print(f"画像アップロードエラー: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

def delete_image_from_s3(image_url):
    """S3から画像を削除"""
    if not S3_AVAILABLE:
        return
    
    try:
        if image_url and 's3.amazonaws.com' in image_url:
            file_name = image_url.split('/')[-1]
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=file_name)
            print(f"S3から画像を削除: {file_name}")
    except Exception as e:
        print(f"画像削除エラー: {e}")

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
        group_id = int(request.form['group_id']) if request.form['group_id'] else None
        
        conn = get_db_connection()
        try:
            user = conn.execute('SELECT * FROM users WHERE username = ? AND group_id = ?', (username, group_id)).fetchone()
            if user and check_password_hash(user['password_hash'], password):
                user_obj = User(user['id'], user['username'], user['email'], user['group_id'], user['is_admin'])
                login_user(user_obj)
                return redirect(url_for('products'))
            flash('ユーザー名、パスワード、またはグループが正しくありません')
        except Exception as e:
            print(f"ログインエラー: {e}")
            flash('ユーザー名、パスワード、またはグループが正しくありません')
        finally:
            conn.close()
    
    # グループ一覧を取得
    conn = get_db_connection()
    try:
        groups = conn.execute('SELECT * FROM groups').fetchall()
    except Exception as e:
        print(f"グループ一覧取得エラー: {e}")
        groups = []
    finally:
        conn.close()
    return render_template('login.html', groups=groups)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        group_option = request.form.get('group_option', 'existing')
        
        conn = get_db_connection()
        try:
            # グループIDの決定
            group_id = None
            if group_option == 'existing':
                # 既存グループを選択
                group_id = int(request.form['group_id']) if request.form['group_id'] else None
                if not group_id:
                    group_id = create_default_group()
            elif group_option == 'new':
                # 新しいグループを作成
                new_group_name = request.form.get('new_group_name', '').strip()
                if new_group_name:
                    conn.execute('INSERT INTO groups (name, description) VALUES (?, ?)', 
                               (new_group_name, f'{username}が作成したグループ'))
                    conn.commit()
                    group_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                else:
                    flash('新しいグループ名を入力してください')
                    return render_template('register.html')
            
            existing_user = conn.execute('SELECT * FROM users WHERE username = ? AND group_id = ?', (username, group_id)).fetchone()
            if existing_user:
                flash('このユーザー名は既にこのグループで使用されています')
                return render_template('register.html')
            
            password_hash = generate_password_hash(password)
            # メールアドレスは空文字列で登録
            conn.execute('INSERT INTO users (username, password_hash, email, group_id) VALUES (?, ?, ?, ?)', 
                       (username, password_hash, '', group_id))
            conn.commit()
            flash('ユーザー登録が完了しました。ログインしてください。')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"ユーザー登録エラー: {e}")
            flash('ユーザー登録中にエラーが発生しました。')
            return render_template('register.html')
        finally:
            conn.close()
    
    # グループ一覧を取得
    conn = get_db_connection()
    try:
        groups = conn.execute('SELECT * FROM groups').fetchall()
    except Exception as e:
        print(f"グループ一覧取得エラー: {e}")
        groups = []
    finally:
        conn.close()
    return render_template('register.html', groups=groups)

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
    try:
        query = '''
            SELECT
                p.*,
                IFNULL(
                    (SELECT SUM(CASE WHEN type='in' THEN qty ELSE 0 END) FROM stocks WHERE product_id = p.id AND group_id = ?), 0
                ) -
                IFNULL(
                    (SELECT SUM(CASE WHEN type='out' THEN qty ELSE 0 END) FROM stocks WHERE product_id = p.id AND group_id = ?), 0
                ) AS stock_quantity
            FROM products p
            WHERE p.group_id = ?
        '''
        params = [current_user.group_id, current_user.group_id, current_user.group_id]
        if name_query:
            query += ' AND p.name LIKE ?'
            params.append(f'%{name_query}%')
        if sku_query:
            query += ' AND p.sku LIKE ?'
            params.append(f'%{sku_query}%')
        products = conn.execute(query, params).fetchall()
    except Exception as e:
        print(f"商品一覧取得エラー: {e}")
        products = []
    finally:
        conn.close()
    return render_template('products.html', products=products, name_query=name_query, sku_query=sku_query)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        sku = request.form['sku']
        unit = request.form['unit']
        min_qty = int(request.form['min_qty']) if request.form['min_qty'] else 0
        
        conn = get_db_connection()
        try:
            # 商品を先に作成してIDを取得
            conn.execute(
                'INSERT INTO products (name, sku, unit, min_qty, group_id, created_by) VALUES (?, ?, ?, ?, ?, ?)',
                (name, sku, unit, min_qty, current_user.group_id, current_user.id)
            )
            conn.commit()
            
            # 新しく作成された商品のIDを取得
            product_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # 画像がアップロードされた場合
            if 'image' in request.files and request.files['image'].filename:
                image_file = request.files['image']
                print(f"画像ファイル検出: {image_file.filename}")
                print(f"ファイルサイズ: {len(image_file.read())} bytes")
                image_file.seek(0)  # ファイルポインタをリセット
                
                if image_file and allowed_file(image_file.filename):
                    print(f"ファイル形式OK: {image_file.filename}")
                    image_url = upload_image_to_s3(image_file, product_id)
                    if image_url:
                        # 画像URLをデータベースに保存
                        conn.execute('UPDATE products SET image_url = ? WHERE id = ?', (image_url, product_id))
                        conn.commit()
                        print(f"データベースに画像URL保存: {image_url}")
                    else:
                        print("画像アップロードに失敗しましたが、商品は登録されました")
                else:
                    print(f"無効なファイル形式: {image_file.filename}")
            else:
                print("画像ファイルが選択されていません")
            
            flash('商品を追加しました')
            return redirect(url_for('products'))
        except Exception as e:
            print(f"商品追加エラー: {e}")
            flash('商品の追加中にエラーが発生しました。')
            return render_template('add_product.html')
        finally:
            conn.close()
    return render_template('add_product.html')

def allowed_file(filename):
    """アップロード可能なファイル形式をチェック"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/stock', methods=['GET', 'POST'])
@login_required
def stock():
    conn = get_db_connection()
    try:
        products = conn.execute('SELECT * FROM products WHERE group_id = ?', (current_user.group_id,)).fetchall()
        if request.method == 'POST':
            product_id = request.form['product_id']
            type_ = request.form['type']
            qty = int(request.form['qty'])
            note = request.form['note']
            conn.execute(
                'INSERT INTO stocks (product_id, type, qty, note, group_id, created_by) VALUES (?, ?, ?, ?, ?, ?)',
                (product_id, type_, qty, note, current_user.group_id, current_user.id)
            )
            conn.commit()
        return render_template('stock.html', products=products)
    except Exception as e:
        print(f"在庫一覧取得エラー: {e}")
        return render_template('stock.html', products=[])
    finally:
        conn.close()

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    conn = get_db_connection()
    try:
        product = conn.execute('SELECT * FROM products WHERE id=? AND group_id=?', (product_id, current_user.group_id)).fetchone()
        if not product:
            return redirect(url_for('products'))
        if request.method == 'POST':
            name = request.form['name']
            sku = request.form['sku']
            unit = request.form['unit']
            min_qty = int(request.form['min_qty']) if request.form['min_qty'] else 0
            
            # 基本情報を更新
            conn.execute('UPDATE products SET name=?, sku=?, unit=?, min_qty=? WHERE id=? AND group_id=?', 
                        (name, sku, unit, min_qty, product_id, current_user.group_id))
            
            # 画像がアップロードされた場合
            if 'image' in request.files and request.files['image'].filename:
                image_file = request.files['image']
                print(f"画像ファイル検出（編集）: {image_file.filename}")
                print(f"ファイルサイズ（編集）: {len(image_file.read())} bytes")
                image_file.seek(0)  # ファイルポインタをリセット
                
                if image_file and allowed_file(image_file.filename):
                    print(f"ファイル形式OK（編集）: {image_file.filename}")
                    # 古い画像を削除
                    if product['image_url']:
                        delete_image_from_s3(product['image_url'])
                        print(f"古い画像を削除: {product['image_url']}")
                    
                    # 新しい画像をアップロード
                    image_url = upload_image_to_s3(image_file, product_id)
                    if image_url:
                        conn.execute('UPDATE products SET image_url = ? WHERE id = ?', (image_url, product_id))
                        print(f"新しい画像URLを保存: {image_url}")
                    else:
                        print("画像アップロードに失敗しましたが、商品情報は更新されました")
                else:
                    print(f"無効なファイル形式（編集）: {image_file.filename}")
            else:
                print("画像ファイルが選択されていません（編集）")
            
            conn.commit()
            flash('商品情報を更新しました')
            return redirect(url_for('products'))
        return render_template('edit_product.html', product=product)
    except Exception as e:
        print(f"商品編集エラー: {e}")
        flash('商品の編集中にエラーが発生しました。')
        return render_template('edit_product.html', product=product)
    finally:
        conn.close()

@app.route('/delete_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def delete_product(product_id):
    conn = get_db_connection()
    try:
        product = conn.execute('SELECT * FROM products WHERE id=? AND group_id=?', (product_id, current_user.group_id)).fetchone()
        if not product:
            return redirect(url_for('products'))
        if request.method == 'POST':
            # 画像がある場合はS3から削除
            if product['image_url']:
                delete_image_from_s3(product['image_url'])
            
            conn.execute('DELETE FROM products WHERE id=? AND group_id=?', (product_id, current_user.group_id))
            conn.commit()
            return redirect(url_for('products'))
        return render_template('confirm_delete.html', product=product)
    except Exception as e:
        print(f"商品削除エラー: {e}")
        flash('商品の削除中にエラーが発生しました。')
        return render_template('confirm_delete.html', product=product)
    finally:
        conn.close()

@app.route('/product_history/<int:product_id>')
@login_required
def product_history(product_id):
    conn = get_db_connection()
    try:
        product = conn.execute('SELECT * FROM products WHERE id=? AND group_id=?', (product_id, current_user.group_id)).fetchone()
        if not product:
            return redirect(url_for('products'))
        history = conn.execute('SELECT * FROM stocks WHERE product_id=? AND group_id=? ORDER BY rowid DESC', (product_id, current_user.group_id)).fetchall()
        return render_template('history.html', product=product, history=history)
    except Exception as e:
        print(f"商品履歴取得エラー: {e}")
        return render_template('history.html', product=None, history=[])
    finally:
        conn.close()

@app.route('/adjust_stock/<int:product_id>', methods=['GET', 'POST'])
@login_required
def adjust_stock(product_id):
    conn = get_db_connection()
    try:
        product = conn.execute('SELECT * FROM products WHERE id=? AND group_id=?', (product_id, current_user.group_id)).fetchone()
        if not product:
            return redirect(url_for('products'))
        stock_row = conn.execute('''
            SELECT
                IFNULL((SELECT SUM(CASE WHEN type='in' THEN qty ELSE 0 END) FROM stocks WHERE product_id = ? AND group_id = ?), 0) -
                IFNULL((SELECT SUM(CASE WHEN type='out' THEN qty ELSE 0 END) FROM stocks WHERE product_id = ? AND group_id = ?), 0) AS stock_quantity
        ''', (product_id, current_user.group_id, product_id, current_user.group_id)).fetchone()
        current_stock = stock_row['stock_quantity'] if stock_row else 0
        if request.method == 'POST':
            new_stock = int(request.form['new_stock'])
            diff = new_stock - current_stock
            if diff != 0:
                if diff > 0:
                    conn.execute('INSERT INTO stocks (product_id, type, qty, note, group_id, created_by) VALUES (?, ?, ?, ?, ?, ?)', (product_id, 'in', diff, '在庫調整', current_user.group_id, current_user.id))
                else:
                    conn.execute('INSERT INTO stocks (product_id, type, qty, note, group_id, created_by) VALUES (?, ?, ?, ?, ?, ?)', (product_id, 'out', -diff, '在庫調整', current_user.group_id, current_user.id))
                conn.commit()
            return redirect(url_for('products'))
        return render_template('adjust_stock.html', product=product, current_stock=current_stock)
    except Exception as e:
        print(f"在庫調整エラー: {e}")
        flash('在庫の調整中にエラーが発生しました。')
        return render_template('adjust_stock.html', product=product, current_stock=0)
    finally:
        conn.close()

# グループ管理機能（管理者用）
@app.route('/groups')
@login_required
def groups():
    if not current_user.is_admin:
        return redirect(url_for('products'))
    conn = get_db_connection()
    try:
        groups = conn.execute('SELECT * FROM groups').fetchall()
        return render_template('groups.html', groups=groups)
    except Exception as e:
        print(f"グループ一覧取得エラー: {e}")
        return render_template('groups.html', groups=[])
    finally:
        conn.close()

@app.route('/add_group', methods=['GET', 'POST'])
@login_required
def add_group():
    if not current_user.is_admin:
        return redirect(url_for('products'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO groups (name, description) VALUES (?, ?)', (name, description))
            conn.commit()
            return redirect(url_for('groups'))
        except Exception as e:
            print(f"グループ追加エラー: {e}")
            flash('グループの追加中にエラーが発生しました。')
            return render_template('add_group.html')
        finally:
            conn.close()
    return render_template('add_group.html')

if __name__ == '__main__':
    app.run(debug=True)
