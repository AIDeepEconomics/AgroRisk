"""
Plot risk data directly from the SQLite database.
This script creates matplotlib visualizations of risk data over time.
"""
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime

# Database file path
DB_PATH = os.path.join('instance', 'agrosmartrisk.db')

def plot_risk_data():
    """Retrieve data from SQLite and create plots for each parcel and risk type."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return False
    
    # Connect to database
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    # Get all parcels
    parcels_df = pd.read_sql_query("SELECT * FROM parcels", conn)
    print(f"Found {len(parcels_df)} parcels")
    
    # Folder for saving plots
    plots_dir = "risk_plots"
    os.makedirs(plots_dir, exist_ok=True)
    
    # Loop through all parcels
    for _, parcel in parcels_df.iterrows():
        parcel_id = parcel['id']
        parcel_name = parcel['name']
        
        print(f"\nPlotting data for {parcel_name} (ID: {parcel_id})")
        
        # Get risk data for this parcel
        query = f"""
        SELECT date, drought_risk, flood_risk, frost_risk, pest_risk, overall_risk 
        FROM risk_data 
        WHERE parcel_id = {parcel_id}
        ORDER BY date
        """
        risk_df = pd.read_sql_query(query, conn)
        
        print(f"Retrieved {len(risk_df)} risk data records")
        
        # Skip if no data
        if len(risk_df) == 0:
            print(f"No risk data for parcel {parcel_id}")
            continue
        
        # Convert date to datetime
        risk_df['date'] = pd.to_datetime(risk_df['date'])
        
        # Print data range
        print(f"Data range: {risk_df['date'].min()} to {risk_df['date'].max()}")
        
        # Print sample of the data
        print("Sample data (first 3 rows):")
        print(risk_df.head(3))
        
        # Create a plot for each risk type
        risk_types = ['drought_risk', 'flood_risk', 'frost_risk', 'pest_risk', 'overall_risk']
        colors = ['orange', 'blue', 'purple', 'green', 'red']
        
        # Create individual plots for each risk type
        for risk_type, color in zip(risk_types, colors):
            plt.figure(figsize=(12, 6))
            plt.plot(risk_df['date'], risk_df[risk_type] * 100, color=color, linewidth=2)
            
            # Format the plot
            plt.title(f"{risk_type.replace('_', ' ').title()} for {parcel_name}")
            plt.xlabel('Date')
            plt.ylabel('Risk Level (%)')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.ylim(0, 100)
            
            # Format x-axis date ticks
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
            plt.gcf().autofmt_xdate()
            
            # Save the plot
            filename = f"{plots_dir}/{parcel_id}_{risk_type}.png"
            plt.savefig(filename)
            plt.close()
            print(f"Saved plot to {filename}")
        
        # Create a combined plot with all risk types
        plt.figure(figsize=(14, 8))
        for risk_type, color in zip(risk_types, colors):
            plt.plot(risk_df['date'], risk_df[risk_type] * 100, color=color, 
                     linewidth=2, label=risk_type.replace('_', ' ').title())
        
        plt.title(f"All Risk Types for {parcel_name}")
        plt.xlabel('Date')
        plt.ylabel('Risk Level (%)')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.ylim(0, 100)
        
        # Format x-axis date ticks
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        plt.gcf().autofmt_xdate()
        
        # Save the combined plot
        filename = f"{plots_dir}/{parcel_id}_all_risks.png"
        plt.savefig(filename)
        plt.close()
        print(f"Saved combined plot to {filename}")
        
        # Create a heatmap of risk values over time
        plt.figure(figsize=(14, 6))
        
        # Prepare data for heatmap
        risk_matrix = risk_df[risk_types].values.T * 100
        
        # Create heatmap
        im = plt.imshow(risk_matrix, aspect='auto', cmap='RdYlGn_r', 
                      extent=[0, len(risk_df), 0, len(risk_types)], 
                      vmin=0, vmax=100)
        
        # Add colorbar
        cbar = plt.colorbar(im)
        cbar.set_label('Risk Level (%)')
        
        # Configure axes
        plt.yticks(np.arange(len(risk_types)) + 0.5, 
                 [rt.replace('_risk', '').title() for rt in risk_types])
        
        # Format x-axis with sample dates
        num_ticks = min(12, len(risk_df))
        indices = np.linspace(0, len(risk_df)-1, num_ticks, dtype=int)
        date_labels = [risk_df['date'].iloc[i].strftime('%Y-%m-%d') for i in indices]
        plt.xticks(indices, date_labels, rotation=45, ha='right')
        
        plt.title(f"Risk Heatmap for {parcel_name}")
        plt.tight_layout()
        
        # Save the heatmap
        filename = f"{plots_dir}/{parcel_id}_risk_heatmap.png"
        plt.savefig(filename)
        plt.close()
        print(f"Saved heatmap to {filename}")
    
    conn.close()
    print(f"\nAll plots saved to {plots_dir} directory")
    return True

def generate_statistics():
    """Generate statistical summary of risk data."""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return False
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    
    # Get statistics by parcel and risk type
    query = """
    SELECT 
        p.id as parcel_id, 
        p.name as parcel_name,
        p.crop_type,
        strftime('%m', r.date) as month,
        avg(r.drought_risk) as avg_drought,
        avg(r.flood_risk) as avg_flood,
        avg(r.frost_risk) as avg_frost,
        avg(r.pest_risk) as avg_pest,
        avg(r.overall_risk) as avg_overall,
        max(r.drought_risk) as max_drought,
        max(r.flood_risk) as max_flood,
        max(r.frost_risk) as max_frost,
        max(r.pest_risk) as max_pest,
        max(r.overall_risk) as max_overall
    FROM 
        risk_data r
    JOIN 
        parcels p ON r.parcel_id = p.id
    GROUP BY 
        p.id, strftime('%m', r.date)
    ORDER BY 
        p.id, month
    """
    
    stats_df = pd.read_sql_query(query, conn)
    
    # Convert month numbers to names
    month_names = {
        '01': 'January', '02': 'February', '03': 'March', 
        '04': 'April', '05': 'May', '06': 'June',
        '07': 'July', '08': 'August', '09': 'September', 
        '10': 'October', '11': 'November', '12': 'December'
    }
    stats_df['month_name'] = stats_df['month'].map(month_names)
    
    # Save statistics to CSV
    stats_file = "risk_statistics.csv"
    stats_df.to_csv(stats_file, index=False)
    print(f"Saved statistics to {stats_file}")
    
    # Create seasonal patterns plot
    plt.figure(figsize=(14, 8))
    
    # List of risk types to plot
    risk_cols = ['avg_drought', 'avg_flood', 'avg_frost', 'avg_pest', 'avg_overall']
    risk_labels = ['Drought', 'Flood', 'Frost', 'Pest', 'Overall']
    colors = ['orange', 'blue', 'purple', 'green', 'red']
    
    # Group by month and calculate average across all parcels
    monthly_avg = stats_df.groupby('month')[risk_cols].mean()
    
    # Sort by month number
    monthly_avg = monthly_avg.reindex(sorted(monthly_avg.index))
    
    # Get month names in order
    months = [month_names[m] for m in monthly_avg.index]
    
    # Plot each risk type
    for i, (col, label, color) in enumerate(zip(risk_cols, risk_labels, colors)):
        plt.subplot(2, 3, i+1)
        plt.bar(months, monthly_avg[col] * 100, color=color, alpha=0.7)
        plt.title(f"{label} Risk by Month")
        plt.ylabel("Average Risk (%)")
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig("seasonal_patterns.png")
    plt.close()
    print(f"Saved seasonal patterns plot to seasonal_patterns.png")
    
    conn.close()
    return True

if __name__ == "__main__":
    print("Generating plots from risk data...")
    plot_risk_data()
    
    print("\nGenerating statistics...")
    generate_statistics()
    
    print("\nProcess completed successfully!")
