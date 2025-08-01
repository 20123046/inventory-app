import boto3
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def fix_s3_bucket():
    """S3バケットのパブリックアクセス設定を修正"""
    try:
        # AWS認証情報を取得
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'ap-northeast-1')
        s3_bucket_name = os.getenv('S3_BUCKET_NAME', 'inventory-app-images8')
        
        print("=== S3バケット設定修正 ===")
        
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
        
        # バケットのパブリックアクセス設定を確認
        try:
            response = s3_client.get_public_access_block(Bucket=s3_bucket_name)
            print(f"現在のパブリックアクセス設定:")
            print(f"  BlockPublicAcls: {response['PublicAccessBlockConfiguration']['BlockPublicAcls']}")
            print(f"  IgnorePublicAcls: {response['PublicAccessBlockConfiguration']['IgnorePublicAcls']}")
            print(f"  BlockPublicPolicy: {response['PublicAccessBlockConfiguration']['BlockPublicPolicy']}")
            print(f"  RestrictPublicBuckets: {response['PublicAccessBlockConfiguration']['RestrictPublicBuckets']}")
        except Exception as e:
            print(f"パブリックアクセス設定の取得に失敗: {e}")
        
        # バケットポリシーを設定してパブリック読み取りを許可
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{s3_bucket_name}/*"
                }
            ]
        }
        
        try:
            s3_client.put_bucket_policy(
                Bucket=s3_bucket_name,
                Policy=str(bucket_policy).replace("'", '"')
            )
            print(f"✓ バケットポリシーを設定しました")
        except Exception as e:
            print(f"バケットポリシーの設定に失敗: {e}")
        
        # パブリックアクセスブロックを無効化
        try:
            s3_client.put_public_access_block(
                Bucket=s3_bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': False,
                    'IgnorePublicAcls': False,
                    'BlockPublicPolicy': False,
                    'RestrictPublicBuckets': False
                }
            )
            print(f"✓ パブリックアクセスブロックを無効化しました")
        except Exception as e:
            print(f"パブリックアクセスブロックの設定に失敗: {e}")
        
        print(f"\n✓ S3バケット '{s3_bucket_name}' の設定が完了しました")
        print("画像がパブリックにアクセス可能になりました")
        
    except Exception as e:
        print(f"✗ S3バケット設定エラー: {e}")

if __name__ == '__main__':
    fix_s3_bucket() 