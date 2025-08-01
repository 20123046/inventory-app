import boto3
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def test_s3_connection():
    try:
        # AWS認証情報を取得
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'ap-northeast-1')
        s3_bucket_name = os.getenv('S3_BUCKET_NAME', 'inventory-app-images8')
        
        print("=== AWS S3設定テスト ===")
        print(f"Access Key ID: {aws_access_key[:10]}..." if aws_access_key else "Access Key ID: 未設定")
        print(f"Secret Access Key: {aws_secret_key[:10]}..." if aws_secret_key else "Secret Access Key: 未設定")
        print(f"Region: {aws_region}")
        print(f"Bucket Name: {s3_bucket_name}")
        
        if aws_access_key and aws_secret_key:
            # S3クライアントを作成
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            
            # バケットの存在確認
            try:
                response = s3_client.head_bucket(Bucket=s3_bucket_name)
                print(f"✓ バケット '{s3_bucket_name}' に正常にアクセスできました")
                
                # バケットの内容を確認
                try:
                    objects = s3_client.list_objects_v2(Bucket=s3_bucket_name, MaxKeys=5)
                    if 'Contents' in objects:
                        print(f"✓ バケット内のオブジェクト数: {len(objects['Contents'])}")
                        for obj in objects['Contents'][:3]:
                            print(f"  - {obj['Key']}")
                    else:
                        print("✓ バケットは空です")
                except Exception as e:
                    print(f"⚠️ バケット内容の確認でエラー: {e}")
                    
            except Exception as e:
                print(f"✗ バケット '{s3_bucket_name}' にアクセスできません: {e}")
                print("バケット名を確認してください")
        else:
            print("✗ AWS認証情報が設定されていません")
            
    except Exception as e:
        print(f"✗ AWS S3設定エラー: {e}")

if __name__ == '__main__':
    test_s3_connection() 