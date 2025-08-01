# 在庫管理システム

Flaskベースの在庫管理システムです。商品の登録、入出庫管理、画像アップロード機能を提供します。

## 機能

- ユーザー認証（ログイン・登録）
- グループ管理
- 商品マスタ管理
- 入出庫管理
- 在庫履歴表示
- 商品画像のAWS S3アップロード
- 在庫調整機能

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下の設定を行ってください：

```bash
# AWS S3設定
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=your-bucket-name

# Flask設定
SECRET_KEY=your-secret-key-here
```

### 3. データベースの初期化

```bash
python init_db.py
```

### 4. アプリケーションの起動

```bash
python app.py
```

ブラウザで `http://localhost:5000` にアクセスしてください。

## 使用方法

### 初回セットアップ

1. アプリケーションにアクセス
2. 「新規ユーザー登録」からアカウントを作成
3. ログインして商品を登録

### 主要機能

- **商品管理**: 商品の追加、編集、削除
- **入出庫管理**: 商品の入庫・出庫を記録
- **在庫確認**: 現在の在庫数を確認
- **履歴表示**: 入出庫履歴を表示
- **画像管理**: 商品画像のアップロード（AWS S3）

## トラブルシューティング

### データベースエラー

```bash
python check_db.py
```

### AWS S3設定エラー

1. AWS認証情報が正しく設定されているか確認
2. S3バケットが存在し、適切な権限が設定されているか確認
3. 環境変数が正しく読み込まれているか確認

### 画像アップロードエラー

- ファイル形式が対応しているか確認（PNG, JPG, JPEG, GIF）
- ファイルサイズが適切か確認
- AWS S3の設定を確認

## ファイル構成

```
inventory_app/
├── app.py              # メインアプリケーション
├── schema.sql          # データベーススキーマ
├── init_db.py          # データベース初期化
├── check_db.py         # データベースチェック
├── requirements.txt    # 依存関係
├── .env               # 環境変数（要作成）
└── templates/         # HTMLテンプレート
    ├── login.html
    ├── register.html
    ├── products.html
    └── ...
```

## 注意事項

- 本番環境では適切なセキュリティ設定を行ってください
- AWS認証情報は安全に管理してください
- 定期的にデータベースのバックアップを取ってください

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。 