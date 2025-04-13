"""
Update the database schema for AgroSmartRisk to add the risk_type column.
"""
import os
import sqlite3

def add_risk_type_column(db_path):
    """Add risk_type column to the risk_data table"""
    print(f"\nUpdating database schema for: {db_path}")
    
    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if risk_type column already exists
        cursor.execute("PRAGMA table_info(risk_data)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'risk_type' in column_names:
            print("risk_type column already exists. No changes needed.")
        else:
            # Add the risk_type column
            cursor.execute("ALTER TABLE risk_data ADD COLUMN risk_type TEXT")
            conn.commit()
            print("Successfully added risk_type column to risk_data table.")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False

if __name__ == '__main__':
    # Path to both databases
    root_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'agrosmartrisk.db'))
    new_func_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance', 'agrosmartrisk.db'))
    
    print("Updating database schema for AgroSmartRisk...")
    print(f"Root database path: {root_db_path}")
    print(f"New functionality database path: {new_func_db_path}")
    
    # Update both databases
    root_success = add_risk_type_column(root_db_path)
    new_func_success = add_risk_type_column(new_func_db_path)
    
    print("\nDatabase schema update summary:")
    print(f"Root database updated: {'Success' if root_success else 'Failed'}")
    print(f"New functionality database updated: {'Success' if new_func_success else 'Failed'}")
    
    if root_success and new_func_success:
        print("\nAll database updates completed successfully.")
    else:
        print("\nWarning: Some database updates failed. Please check the logs above for details.")
