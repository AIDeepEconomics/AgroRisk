"""
Database models for the AgroSmartRisk Time-Series Analysis module.
This module defines the SQLAlchemy models for storing time series risk data.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Parcel(db.Model):
    """
    Model representing an agricultural parcel of land.
    """
    __tablename__ = 'parcels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    area = db.Column(db.Float, nullable=False)  # Area in hectares
    soil_type = db.Column(db.String(50))
    crop_type = db.Column(db.String(50))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    risk_data = db.relationship('RiskData', backref='parcel', lazy=True)
    
    def __repr__(self):
        return f'<Parcel {self.name}>'
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'area': self.area,
            'soil_type': self.soil_type,
            'crop_type': self.crop_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class RiskData(db.Model):
    """
    Model representing time series risk data for a parcel.
    """
    __tablename__ = 'risk_data'
    
    id = db.Column(db.Integer, primary_key=True)
    parcel_id = db.Column(db.Integer, db.ForeignKey('parcels.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    drought_risk = db.Column(db.Float)  # 0-1 scale
    flood_risk = db.Column(db.Float)    # 0-1 scale
    frost_risk = db.Column(db.Float)    # 0-1 scale
    pest_risk = db.Column(db.Float)     # 0-1 scale
    overall_risk = db.Column(db.Float)  # 0-1 scale
    alert = db.Column(db.String(255))   # Alert message if any
    risk_type = db.Column(db.String(50)) # Type of risk (drought, flood, frost)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('parcel_id', 'date', name='uix_risk_data_parcel_date'),
    )
    
    def __repr__(self):
        return f'<RiskData parcel_id={self.parcel_id} date={self.date}>'
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'parcel_id': self.parcel_id,
            'date': self.date.isoformat(),
            'drought_risk': self.drought_risk,
            'flood_risk': self.flood_risk,
            'frost_risk': self.frost_risk,
            'pest_risk': self.pest_risk,
            'overall_risk': self.overall_risk,
            'alert': self.alert,
            'risk_type': self.risk_type,
            'created_at': self.created_at.isoformat()
        }


class RiskAnalysis(db.Model):
    """
    Model representing risk analysis results for time series data.
    """
    __tablename__ = 'risk_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    parcel_id = db.Column(db.Integer, db.ForeignKey('parcels.id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)  # e.g., 'trend', 'seasonal', 'forecast'
    risk_type = db.Column(db.String(50), nullable=False)      # e.g., 'drought', 'flood', 'overall'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    result_data = db.Column(db.JSON)                          # Store analysis results as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RiskAnalysis parcel_id={self.parcel_id} type={self.analysis_type}>'
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'parcel_id': self.parcel_id,
            'analysis_type': self.analysis_type,
            'risk_type': self.risk_type,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'result_data': self.result_data,
            'created_at': self.created_at.isoformat()
        }


class WeatherData(db.Model):
    """
    Model representing time series weather data that influences risk factors.
    """
    __tablename__ = 'weather_data'
    
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    temperature_min = db.Column(db.Float)
    temperature_max = db.Column(db.Float)
    precipitation = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('latitude', 'longitude', 'date', name='uix_weather_location_date'),
    )
    
    def __repr__(self):
        return f'<WeatherData lat={self.latitude} lon={self.longitude} date={self.date}>'
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'date': self.date.isoformat(),
            'temperature_min': self.temperature_min,
            'temperature_max': self.temperature_max,
            'precipitation': self.precipitation,
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'created_at': self.created_at.isoformat()
        }
