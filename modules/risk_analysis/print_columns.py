"""
Print all column names in each table of the database.
"""
import sqlite3
import os

# Database file path
DB_PATH = os.path.join('instance', 'agrosmartrisk.db')

def print_database_columns():
    """Print all column names for each table in the database."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return False
    
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} tables in the database")
    
    # Print column names for each table
    for table in tables:
        table_name = table[0]
        print(f"\n=== Table: {table_name} ===")
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print(f"Number of columns: {len(columns)}")
        print("Column names:")
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, primary_key = col
            print(f"  - {col_name} (Type: {col_type})")
            
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]
        print(f"Number of rows: {row_count}")
        
        # Print sample data (first row)
        if row_count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
            sample = cursor.fetchone()
            print("Sample data (first row):")
            for i, col in enumerate(columns):
                col_name = col[1]
                sample_value = sample[i] if i < len(sample) else None
                print(f"  - {col_name}: {sample_value}")
    
    conn.close()
    return True

if __name__ == "__main__":
    print_database_columns()
