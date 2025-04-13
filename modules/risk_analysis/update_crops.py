"""
Script to update crop types in the AgroSmartRisk database.
This script changes all crop types to only include Maize, Wheat, and Soybeans.
"""
import os
import sqlite3
import random
from flask import Flask
from database.models import db, Parcel, RiskData

# Initialize Flask app (needed for database access)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agrosmartrisk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def update_crop_types():
    """Update all crop types in the database to use only Maize, Wheat, and Soybeans"""
    with app.app_context():
        # Get all parcels
        parcels = Parcel.query.all()
        print(f"Found {len(parcels)} parcels in database")
        
        # Count by crop type before update
        crop_count_before = {}
        for parcel in parcels:
            crop_count_before[parcel.crop_type] = crop_count_before.get(parcel.crop_type, 0) + 1
        
        print("Crop types before update:")
        for crop, count in crop_count_before.items():
            print(f"  {crop}: {count}")
        
        # Update crop types
        updates = {
            "Corn": "Maize",
            "Rice": "Wheat",
            "Cotton": "Soybeans"
        }
        
        allowed_crops = ["Maize", "Wheat", "Soybeans"]
        
        for parcel in parcels:
            if parcel.crop_type in updates:
                parcel.crop_type = updates[parcel.crop_type]
            elif parcel.crop_type not in allowed_crops:
                # Assign a random crop type from allowed list
                parcel.crop_type = random.choice(allowed_crops)
        
        # Commit the changes
        db.session.commit()
        
        # Count by crop type after update
        crop_count_after = {}
        for parcel in Parcel.query.all():
            crop_count_after[parcel.crop_type] = crop_count_after.get(parcel.crop_type, 0) + 1
        
        print("\nCrop types after update:")
        for crop, count in crop_count_after.items():
            print(f"  {crop}: {count}")
        
        print("\nUpdate complete!")

if __name__ == '__main__':
    update_crop_types()
