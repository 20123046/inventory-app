import boto3
import os
from PIL import Image
import io
from datetime import datetime
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def create_test_image():
    """テスト用の画像を作成"""
    try:
        # 100x100のテスト画像を作成
        img = Image.new('RGB', (100, 100), color='red')
        
        # 画像をバイトデータに変換
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr.seek(0)
        
        return img_byte_arr
    except Exception as e:
        print(f"テスト画像作成エラー: {e}")
        return None

def test_image_upload():
    """画像アップロード機能をテスト"""
    try:
        # AWS認証情報を取得
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'ap-northeast-1')
        s3_bucket_name = os.getenv('S3_BUCKET_NAME', 'inventory-app-images8')
        
        print("=== 画像アップロードテスト ===")
        
        if not aws_access_key or not aws_secret_key:
            print("✗ AWS認証情報が設定されていません")
            return
        
        # S3クライアントを作成
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # テスト画像を作成
        test_image = create_test_image()
        if not test_image:
            print("✗ テスト画像の作成に失敗しました")
            return
        
        # テスト用の商品ID
        test_product_id = 8
        
        # S3にアップロード
        file_name = f"test_product_{test_product_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        print(f"画像をアップロード中: {file_name}")
        
        s3_client.upload_fileobj(
            test_image,
            s3_bucket_name,
            file_name,
            ExtraArgs={'ContentType': 'image/jpeg'}
        )
        
        # S3のURLを生成
        image_url = f"https://{s3_bucket_name}.s3.amazonaws.com/{file_name}"
        print(f"✓ 画像アップロード成功: {image_url}")
        
        # データベースに画像URLを保存
        import sqlite3
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        
        # 商品ID 8に画像URLを設定
        conn.execute('UPDATE products SET image_url = ? WHERE id = ?', (image_url, test_product_id))
        conn.commit()
        conn.close()
        
        print(f"✓ データベースに画像URLを保存しました")
        print(f"商品ID {test_product_id} に画像が設定されました")
        
        # 確認
        print("\n=== 確認 ===")
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        product = conn.execute('SELECT * FROM products WHERE id = ?', (test_product_id,)).fetchone()
        if product:
            print(f"商品名: {product['name']}")
            print(f"画像URL: {product['image_url']}")
        conn.close()
        
    except Exception as e:
        print(f"✗ 画像アップロードテストエラー: {e}")

if __name__ == '__main__':
    test_image_upload() 