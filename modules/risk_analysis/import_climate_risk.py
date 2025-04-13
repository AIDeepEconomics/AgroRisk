"""
Script to import climate risk data from CSV into the AgroSmartRisk database.
"""
import os
import csv
from datetime import datetime
from flask import Flask
from database.models import db, Parcel, RiskData

# Initialize Flask app (needed for database access)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agrosmartrisk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def import_climate_risk_data(csv_file_path, clear_existing=False):
    """Import climate risk data from CSV file into the database."""
    with app.app_context():
        # Optionally clear existing risk data
        if clear_existing:
            print("Warning: This will clear all existing risk data.")
            RiskData.query.delete()
            db.session.commit()
            print("Cleared existing risk data")
        
        # Track statistics
        total_rows = 0
        imported_rows = 0
        skipped_rows = 0
        new_parcels = 0
        
        # Process CSV file
        with open(csv_file_path, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            # Skip header if present
            # Try to detect header by checking if first row contains non-numeric values for risk columns
            first_row = next(csv_reader, None)
            if first_row:
                try:
                    # Try to convert risk values to integers
                    drought_risk = int(first_row[2])
                    # If we get here, it's probably data, not a header
                    rows = [first_row]  # Include first row in processing
                except (ValueError, IndexError):
                    # It's likely a header, skip it
                    print("Detected and skipped header row")
                    rows = []
            
            # Add the rest of the rows for processing
            rows.extend(csv_reader)
            
            for row in rows:
                total_rows += 1
                
                try:
                    # Parse CSV columns
                    parcel_name = row[0]
                    date_str = row[1]
                    
                    # Handle empty values
                    try:
                        drought_pct = int(row[2]) if row[2] else 0
                    except ValueError:
                        drought_pct = 0
                        
                    try:
                        flood_pct = int(row[3]) if row[3] else 0
                    except ValueError:
                        flood_pct = 0
                        
                    try:
                        frost_pct = int(row[4]) if row[4] else 0
                    except ValueError:
                        frost_pct = 0
                        
                    try:
                        overall_pct = int(row[5]) if row[5] else 0
                    except ValueError:
                        overall_pct = 0
                    
                    alert_message = row[6] if len(row) > 6 and row[6] else ""
                    risk_type = row[7] if len(row) > 7 and row[7] else ""
                    
                    # Find or create parcel
                    parcel = Parcel.query.filter_by(name=parcel_name).first()
                    if not parcel:
                        print(f"Creating new parcel: {parcel_name}")
                        # Create new parcel with dummy values
                        parcel = Parcel(
                            name=parcel_name,
                            area=10.0,  # Default area
                            soil_type="Unknown",
                            crop_type="Wheat",  # Default to Wheat
                            latitude=0.0,
                            longitude=0.0
                        )
                        db.session.add(parcel)
                        db.session.flush()  # Get parcel ID without committing
                        new_parcels += 1
                    
                    # Parse date
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # Check if risk data already exists for this parcel and date
                    existing_risk = RiskData.query.filter_by(
                        parcel_id=parcel.id,
                        date=date_obj
                    ).first()
                    
                    if existing_risk:
                        # Update existing entry
                        existing_risk.drought_risk = drought_pct / 100.0
                        existing_risk.flood_risk = flood_pct / 100.0
                        existing_risk.frost_risk = frost_pct / 100.0
                        existing_risk.overall_risk = overall_pct / 100.0
                        existing_risk.alert = alert_message
                        existing_risk.risk_type = risk_type
                        print(f"Updated risk data for {parcel_name} on {date_str}")
                    else:
                        # Create new risk data entry
                        risk_data = RiskData(
                            parcel_id=parcel.id,
                            date=date_obj,
                            drought_risk=drought_pct / 100.0,
                            flood_risk=flood_pct / 100.0,
                            frost_risk=frost_pct / 100.0,
                            pest_risk=0.0,  # Default value as not in CSV
                            overall_risk=overall_pct / 100.0,
                            alert=alert_message,
                            risk_type=risk_type
                        )
                        db.session.add(risk_data)
                        print(f"Added risk data for {parcel_name} on {date_str}")
                    
                    imported_rows += 1
                    
                    # Commit every 100 rows to avoid large transactions
                    if imported_rows % 100 == 0:
                        db.session.commit()
                        print(f"Committed {imported_rows} rows so far")
                    
                except Exception as e:
                    print(f"Error processing row: {row}")
                    print(f"Error details: {e}")
                    skipped_rows += 1
                    continue
            
            # Commit any remaining changes
            db.session.commit()
        
        print(f"\nImport completed. Total rows: {total_rows}")
        print(f"Imported: {imported_rows}, Skipped: {skipped_rows}")
        print(f"New parcels created: {new_parcels}")

def verify_import():
    """Verify that data was imported correctly"""
    with app.app_context():
        risk_count = RiskData.query.count()
        parcels = Parcel.query.all()
        
        print(f"\nVerification Results:")
        print(f"Total risk data records: {risk_count}")
        print(f"Total parcels: {len(parcels)}")
        
        print("\nParcels in database:")
        for parcel in parcels:
            risk_count = RiskData.query.filter_by(parcel_id=parcel.id).count()
            print(f"  {parcel.name} ({parcel.crop_type}): {risk_count} risk records")

if __name__ == '__main__':
    # Define absolute path to the CSV file
    csv_file_path = 'c:/Users/barbo/CascadeProjects/windsurf-project/data/climate_risk_30days.csv'
    
    # Ensure path exists
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}")
        abs_path = os.path.abspath(csv_file_path)
        print(f"Absolute path tried: {abs_path}")
        exit(1)
    
    print(f"Importing climate risk data from {csv_file_path}")
    # Set clear_existing=False to preserve existing data
    clear_existing = False
    
    # Run import
    import_climate_risk_data(csv_file_path, clear_existing=clear_existing)
    
    # Verify import
    verify_import()
