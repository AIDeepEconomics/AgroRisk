"""
Direct visualization web application for AgroSmartRisk.
This is a standalone Flask application that reads data directly from the database
and renders visualizations using Plotly.
"""
import os
import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime
from flask import Flask, render_template, jsonify, Response

# Create Flask app
app = Flask(__name__, 
            template_folder='direct_templates',
            static_folder='direct_static')

# Database path
DB_PATH = os.path.join('instance', 'agrosmartrisk.db')

def get_db_connection():
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/parcels')
def get_parcels():
    """Get all parcels from the database."""
    conn = get_db_connection()
    parcels = conn.execute('SELECT * FROM parcels').fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    result = []
    for parcel in parcels:
        result.append({
            'id': parcel['id'],
            'name': parcel['name'],
            'area': parcel['area'],
            'soil_type': parcel['soil_type'],
            'crop_type': parcel['crop_type'],
            'latitude': parcel['latitude'],
            'longitude': parcel['longitude']
        })
    
    return jsonify({'parcels': result})

@app.route('/api/risk_data/<int:parcel_id>')
def get_risk_data(parcel_id):
    """Get risk data for a specific parcel."""
    conn = get_db_connection()
    
    # Query risk data for the specified parcel
    risk_data = conn.execute(
        'SELECT * FROM risk_data WHERE parcel_id = ? ORDER BY date', 
        (parcel_id,)
    ).fetchall()
    
    # Get parcel information
    parcel = conn.execute(
        'SELECT * FROM parcels WHERE id = ?',
        (parcel_id,)
    ).fetchone()
    
    conn.close()
    
    if not parcel:
        return jsonify({'error': 'Parcel not found'}), 404
    
    if not risk_data:
        return jsonify({'error': 'No risk data found for this parcel'}), 404
    
    # Convert to format suitable for Plotly
    dates = []
    drought_risk = []
    flood_risk = []
    frost_risk = []
    pest_risk = []
    overall_risk = []
    
    for record in risk_data:
        dates.append(record['date'])
        drought_risk.append(record['drought_risk'] * 100)  # Convert to percentage
        flood_risk.append(record['flood_risk'] * 100)
        frost_risk.append(record['frost_risk'] * 100)
        pest_risk.append(record['pest_risk'] * 100)
        overall_risk.append(record['overall_risk'] * 100)
    
    parcel_info = {
        'id': parcel['id'],
        'name': parcel['name'],
        'area': parcel['area'],
        'soil_type': parcel['soil_type'],
        'crop_type': parcel['crop_type']
    }
    
    result = {
        'parcel': parcel_info,
        'dates': dates,
        'drought_risk': drought_risk,
        'flood_risk': flood_risk,
        'frost_risk': frost_risk,
        'pest_risk': pest_risk,
        'overall_risk': overall_risk
    }
    
    return jsonify(result)

@app.route('/api/monthly_risk/<int:parcel_id>')
def get_monthly_risk(parcel_id):
    """Get monthly average risk data for a specific parcel."""
    conn = get_db_connection()
    
    # Query to get monthly averages
    monthly_data = conn.execute('''
        SELECT 
            strftime('%m', date) as month,
            strftime('%Y', date) as year,
            AVG(drought_risk) as avg_drought,
            AVG(flood_risk) as avg_flood,
            AVG(frost_risk) as avg_frost,
            AVG(pest_risk) as avg_pest,
            AVG(overall_risk) as avg_overall
        FROM risk_data
        WHERE parcel_id = ?
        GROUP BY year, month
        ORDER BY year, month
    ''', (parcel_id,)).fetchall()
    
    conn.close()
    
    if not monthly_data:
        return jsonify({'error': 'No risk data found for this parcel'}), 404
    
    # Convert to format suitable for Plotly
    months = []
    drought_risk = []
    flood_risk = []
    frost_risk = []
    pest_risk = []
    overall_risk = []
    
    month_names = {
        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
    }
    
    for record in monthly_data:
        month_label = f"{month_names[record['month']]} {record['year']}"
        months.append(month_label)
        drought_risk.append(record['avg_drought'] * 100)
        flood_risk.append(record['avg_flood'] * 100)
        frost_risk.append(record['avg_frost'] * 100)
        pest_risk.append(record['avg_pest'] * 100)
        overall_risk.append(record['avg_overall'] * 100)
    
    result = {
        'months': months,
        'drought_risk': drought_risk,
        'flood_risk': flood_risk,
        'frost_risk': frost_risk,
        'pest_risk': pest_risk,
        'overall_risk': overall_risk
    }
    
    return jsonify(result)

@app.route('/api/risk_summary')
def get_risk_summary():
    """Get risk summary statistics across all parcels."""
    conn = get_db_connection()
    
    # Query to get overall risk statistics
    summary = conn.execute('''
        SELECT 
            p.id as parcel_id,
            p.name as parcel_name,
            p.crop_type,
            AVG(r.drought_risk) as avg_drought,
            AVG(r.flood_risk) as avg_flood,
            AVG(r.frost_risk) as avg_frost,
            AVG(r.pest_risk) as avg_pest,
            AVG(r.overall_risk) as avg_overall,
            MAX(r.overall_risk) as max_overall,
            MIN(r.overall_risk) as min_overall
        FROM risk_data r
        JOIN parcels p ON r.parcel_id = p.id
        GROUP BY p.id
        ORDER BY p.id
    ''').fetchall()
    
    conn.close()
    
    # Convert to list of dictionaries
    result = []
    for record in summary:
        result.append({
            'parcel_id': record['parcel_id'],
            'parcel_name': record['parcel_name'],
            'crop_type': record['crop_type'],
            'avg_drought': round(record['avg_drought'] * 100, 1),
            'avg_flood': round(record['avg_flood'] * 100, 1),
            'avg_frost': round(record['avg_frost'] * 100, 1),
            'avg_pest': round(record['avg_pest'] * 100, 1),
            'avg_overall': round(record['avg_overall'] * 100, 1),
            'max_overall': round(record['max_overall'] * 100, 1),
            'min_overall': round(record['min_overall'] * 100, 1)
        })
    
    return jsonify({'summary': result})

if __name__ == '__main__':
    # Create folders if they don't exist
    os.makedirs('direct_templates', exist_ok=True)
    os.makedirs('direct_static', exist_ok=True)
    
    # Run app
    app.run(host='0.0.0.0', port=8080, debug=True)
