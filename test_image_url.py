import requests
import sqlite3
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def test_image_url():
    """画像URLのアクセス可能性をテスト"""
    try:
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row
        
        # 画像URLがある商品を取得
        products = conn.execute('SELECT * FROM products WHERE image_url IS NOT NULL').fetchall()
        
        print("=== 画像URLテスト ===")
        
        for product in products:
            print(f"\n商品名: {product['name']}")
            print(f"画像URL: {product['image_url']}")
            
            try:
                # 画像URLにアクセス
                response = requests.get(product['image_url'], timeout=10)
                
                if response.status_code == 200:
                    print(f"✓ 画像に正常にアクセスできました (サイズ: {len(response.content)} bytes)")
                    
                    # Content-Typeを確認
                    content_type = response.headers.get('Content-Type', '')
                    print(f"  Content-Type: {content_type}")
                    
                    if 'image' in content_type:
                        print("✓ 正しい画像ファイルです")
                    else:
                        print("⚠️ Content-Typeが画像ではありません")
                        
                else:
                    print(f"✗ 画像にアクセスできません (ステータスコード: {response.status_code})")
                    
            except requests.exceptions.RequestException as e:
                print(f"✗ 画像アクセスエラー: {e}")
            except Exception as e:
                print(f"✗ 予期しないエラー: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == '__main__':
    test_image_url() 