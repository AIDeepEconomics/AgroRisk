"""
Script to update Parcel 2 to have crop type of Maize in the AgroSmartRisk database.
"""
import os
from flask import Flask
from database.models import db, Parcel

# Initialize Flask app (needed for database access)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agrosmartrisk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def update_parcel():
    """Update Parcel 2 to have crop type Maize"""
    with app.app_context():
        # Get Parcel 2
        parcel = Parcel.query.get(2)
        
        if parcel:
            print(f"Found Parcel 2: {parcel.name} with crop type: {parcel.crop_type}")
            
            # Update crop type
            previous_crop = parcel.crop_type
            parcel.crop_type = "Maize"
            
            # Commit the changes
            db.session.commit()
            
            print(f"Updated Parcel 2 crop type from {previous_crop} to Maize")
            
            # Verify the update
            updated_parcel = Parcel.query.get(2)
            print(f"Verification: Parcel 2 crop type is now {updated_parcel.crop_type}")
        else:
            print("Parcel 2 not found in the database")

if __name__ == '__main__':
    update_parcel()
