"""
Export database content to Excel file.
This script connects to the SQLite database and exports all tables to an Excel file.
"""
import os
import sqlite3
import pandas as pd
from datetime import datetime

# Database file path
DB_PATH = os.path.join('instance', 'agrosmartrisk.db')
# Output Excel files
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
EXCEL_FILE = f'agrosmartrisk_data_{timestamp}.xlsx'
RISK_DATA_FILE = f'risk_data_{timestamp}.xlsx'

def export_db_to_excel():
    """Export all tables in the database to an Excel file with multiple sheets."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return False
    
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    # Get list of tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} tables in the database")
    
    if not tables:
        print("No tables found in the database.")
        conn.close()
        return False
    
    # Create Excel writer
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        for table in tables:
            table_name = table[0]
            print(f"Exporting table: {table_name}")
            
            # Read the table into a DataFrame
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            
            # Write to Excel sheet
            df.to_excel(writer, sheet_name=table_name, index=False)
            
            # Print basic statistics
            print(f"  - Rows: {len(df)}")
            print(f"  - Columns: {len(df.columns)}")
            print(f"  - Column names: {', '.join(df.columns)}")
    
    # Export only risk data to a separate file
    export_risk_data(conn)
    
    conn.close()
    print(f"Data successfully exported to {EXCEL_FILE}")
    return True

def export_risk_data(conn):
    """Export only the risk_data table with joined parcel information."""
    print("\nExporting risk data to separate file...")
    
    # Query that joins risk_data with parcels to get more context
    query = """
    SELECT 
        r.id, r.parcel_id, p.name as parcel_name, p.crop_type, p.soil_type,
        r.date, r.drought_risk, r.flood_risk, r.frost_risk, r.pest_risk, r.overall_risk, 
        r.alert, r.created_at
    FROM risk_data r
    JOIN parcels p ON r.parcel_id = p.id
    ORDER BY r.parcel_id, r.date
    """
    
    try:
        risk_df = pd.read_sql_query(query, conn)
        
        # Add some basic analysis
        risk_df['date'] = pd.to_datetime(risk_df['date'])
        risk_df['month'] = risk_df['date'].dt.month
        risk_df['year'] = risk_df['date'].dt.year
        
        # Export to Excel
        with pd.ExcelWriter(RISK_DATA_FILE, engine='openpyxl') as writer:
            risk_df.to_excel(writer, sheet_name='Risk Data', index=False)
            
            # Create a pivot table for monthly averages by parcel
            pivot = pd.pivot_table(
                risk_df, 
                values=['drought_risk', 'flood_risk', 'frost_risk', 'pest_risk', 'overall_risk'],
                index=['parcel_id', 'parcel_name', 'month'],
                aggfunc='mean'
            )
            pivot.to_excel(writer, sheet_name='Monthly Averages')
            
            # Create a summary sheet with statistics per parcel
            summary = risk_df.groupby(['parcel_id', 'parcel_name', 'crop_type']).agg({
                'drought_risk': ['mean', 'min', 'max', 'std'],
                'flood_risk': ['mean', 'min', 'max', 'std'],
                'frost_risk': ['mean', 'min', 'max', 'std'],
                'pest_risk': ['mean', 'min', 'max', 'std'],
                'overall_risk': ['mean', 'min', 'max', 'std']
            })
            summary.to_excel(writer, sheet_name='Risk Summary')
        
        print(f"Risk data exported to {RISK_DATA_FILE}")
        print(f"  - Total risk data records: {len(risk_df)}")
        print(f"  - Data range: {risk_df['date'].min()} to {risk_df['date'].max()}")
        print(f"  - Number of parcels: {risk_df['parcel_id'].nunique()}")
        
    except Exception as e:
        print(f"Error exporting risk data: {e}")

if __name__ == "__main__":
    success = export_db_to_excel()
    if success:
        print("Export completed successfully!")
    else:
        print("Export failed.")
