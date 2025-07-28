import sqlite3

def show_schema():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    print("=== テーブル一覧 ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"- {table[0]}")
    
    print("\n=== 各テーブルの構造 ===")
    for table in tables:
        table_name = table[0]
        print(f"\n--- {table_name} ---")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - {col[3]} - {col[4]} - {col[5]}")
    
    print("\n=== 外部キー制約 ===")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA foreign_key_list({table_name});")
        fks = cursor.fetchall()
        if fks:
            print(f"\n{table_name}の外部キー:")
            for fk in fks:
                print(f"  {fk[3]} -> {fk[2]}.{fk[4]}")
    
    conn.close()

if __name__ == '__main__':
    show_schema() 