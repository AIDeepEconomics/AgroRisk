"""
Flask web application for the Dynamic Risk Map project.
This module handles the web routes and serves the UI.
"""
import os
import json
import sys
from flask import Flask, render_template, jsonify, request, Blueprint
import pandas as pd
import geopandas as gpd
import csv
import json
import csv
from data.map_rendering import create_risk_map, create_animated_risk_map

# Agregar el módulo de análisis de riesgos al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules/risk_analysis'))

# Initialize Flask app
app = Flask(__name__)

# Load data
def load_data():
    """Load all necessary data files for the application"""
    parcels_file = 'data/parcels.geojson'
    climate_file = 'data/climate_risk_30days.csv'
    yield_file = 'data/yield_predictions.csv'
    insurance_file = 'data/insurance_products.csv'
    
    # Load parcels
    parcels_gdf = gpd.read_file(parcels_file)
    
    # Load climate data
    climate_data = pd.read_csv(climate_file, encoding='utf-8')
    
    # Load yield predictions
    yield_predictions = pd.read_csv(yield_file, encoding='utf-8')
    
    # Load insurance products
    insurance_products = pd.read_csv(insurance_file, encoding='utf-8')
    
    return parcels_gdf, climate_data, yield_predictions, insurance_products

# Load data on startup
parcels_gdf, climate_data, yield_predictions, insurance_products = load_data()

# Routes
@app.route('/')
def index():
    """Main page of the application"""
    # Pass data to template
    dates = sorted(climate_data['date'].unique())
    
    # Check if 'alert' column exists before filtering
    if 'alert' in climate_data.columns:
        alerts = climate_data.dropna(subset=['alert']).to_dict('records')
    else:
        alerts = []  # No alerts if column doesn't exist
    
    # Get page number from request, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # Read yield predictions from CSV
    with open('data/yield_predictions.csv', 'r') as file:
        reader = csv.DictReader(file)
        yield_predictions = list(reader)
    
    # Calculate pagination values
    total_predictions = len(yield_predictions)
    total_pages = (total_predictions + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    
    return render_template(
        'index.html',
        dates=dates,
        alerts=alerts,
        insurance_products=insurance_products.to_dict('records'),
        yield_predictions=yield_predictions[start:end],
        current_page=page,
        total_pages=total_pages,
        total_predictions=total_predictions
    )

@app.route('/map')
def map_view():
    """Endpoint for generating and displaying the risk map"""
    date = request.args.get('date')
    risk_type = request.args.get('risk_type', 'general')
    crop_type = request.args.get('crop_type', 'all')
    
    if not date:
        date = (pd.Timestamp.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Create the map with the specified parameters
    risk_map = create_risk_map(date, climate_data, parcels_gdf, risk_type=risk_type, crop_type=crop_type)
    
    return risk_map.get_root().render()

@app.route('/map_data')
def map_data():
    """API endpoint to get map data in GeoJSON format for smooth transitions"""
    date = request.args.get('date')
    risk_type = request.args.get('risk_type', 'general')
    crop_type = request.args.get('crop_type', 'all')
    
    if not date:
        date = (pd.Timestamp.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Filter data for the selected date
    date_data = climate_data[climate_data['date'] == date]
    
    # If empty, use the earliest date
    if len(date_data) == 0:
        earliest_date = climate_data['date'].min()
        date_data = climate_data[climate_data['date'] == earliest_date]
    
    # Calculate risk_level if not present
    if 'risk_level' not in date_data.columns:
        if risk_type == 'drought':
            date_data['risk_level'] = date_data['drought_probability'] / 100.0
        elif risk_type == 'flood':
            date_data['risk_level'] = date_data['flood_probability'] / 100.0
        elif risk_type == 'pest':
            date_data['risk_level'] = date_data['hail_probability'] / 100.0
        else:
            date_data['risk_level'] = date_data['general_risk'] / 100.0
    
    # Apply crop type filter if not 'all'
    filtered_parcels = parcels_gdf
    if crop_type != 'all':
        if crop_type.lower() == 'soja':
            filtered_parcels = parcels_gdf[parcels_gdf['crop'].str.lower() == 'soja']
        elif crop_type.lower() == 'maiz':
            filtered_parcels = parcels_gdf[parcels_gdf['crop'].str.lower() == 'maiz']
    
    # Create dictionaries for quick lookup
    risk_map = dict(zip(date_data['parcel_id'], date_data['risk_level']))
    
    # Create GeoJSON features
    features = []
    for idx, row in filtered_parcels.iterrows():
        parcel_id = row['id']
        risk_level = risk_map.get(parcel_id, 0)
        
        # Create feature for this parcel
        feature = {
            'type': 'Feature',
            'geometry': row['geometry'].__geo_interface__,
            'properties': {
                'id': parcel_id,
                'risk_level': risk_level,
                'area': row['area'],
                'soil_type': row['soil_type'],
                'crop': row['crop']
            }
        }
        
        features.append(feature)
    
    # Return GeoJSON data
    return jsonify({
        'type': 'FeatureCollection',
        'features': features,
        'risk_type': risk_type,
        'date': date
    })

@app.route('/animated_map')
def animated_map_view():
    """Route for displaying an animated risk map showing changes over time"""
    risk_type = request.args.get('risk_type', 'general')
    crop_type = request.args.get('crop_type', 'all')
    
    # Create animated map using the imported module
    m = create_animated_risk_map(parcels_gdf, climate_data, risk_type=risk_type, crop_type=crop_type)
    
    # Save map to HTML string
    map_html = m.get_root().render()
    
    return map_html

@app.route('/api/parcels')
def get_parcels():
    """API endpoint for getting parcel data"""
    # Convert to GeoJSON for API response
    # But DO NOT save to file
    geojson = parcels_gdf.to_json()
    return geojson

@app.route('/api/risk_data')
def get_risk_data():
    """API endpoint for getting risk data"""
    date = request.args.get('date', climate_data['date'].min())
    parcel_id = request.args.get('parcel_id', None)
    
    # Filter data
    filtered_data = climate_data[climate_data['date'] == date]
    
    if parcel_id:
        filtered_data = filtered_data[filtered_data['parcel_id'] == parcel_id]
    
    # Convert to records (list of dicts)
    records = filtered_data.to_dict('records')
    
    # Ensure alerts are properly filtered (None, empty strings, NaN values, etc.)
    for record in records:
        # Convert NaN values to None (which becomes null in JSON)
        for key, value in record.items():
            # Check if value is a float and is NaN
            if isinstance(value, float) and pd.isna(value):
                record[key] = None
        
        # Specific handling for alert field
        if pd.isna(record.get('alert')) or not record.get('alert'):
            record['alert'] = None
    
    return jsonify(records)

@app.route('/api/yield_predictions')
def get_yield_predictions():
    """API endpoint for getting yield prediction data"""
    date = request.args.get('date', '')
    parcel_id = request.args.get('parcel_id', None)
    
    try:
        # Read data directly from CSV for the most up-to-date information
        with open('data/yield_predictions.csv', 'r') as file:
            reader = csv.DictReader(file)
            predictions_data = list(reader)
        
        # Filter by date if provided
        if date:
            predictions_data = [row for row in predictions_data if row.get('date') == date]
        
        # Filter by parcel_id if provided
        if parcel_id:
            predictions_data = [row for row in predictions_data if row.get('parcel_id') == parcel_id]
        
        # Enhance data with risk calculations
        for prediction in predictions_data:
            # Rename probability fields to risk for frontend consistency
            prediction['drought_risk'] = prediction.get('drought_probability', '0')
            prediction['flood_risk'] = prediction.get('flood_probability', '0')
            prediction['pest_risk'] = prediction.get('hail_probability', '0')  # Using hail as pest for now
            
            # Ensure all fields are present even if missing
            for field in ['predicted_yield', 'confidence', 'drought_risk', 'flood_risk', 'pest_risk', 'crop']:
                if field not in prediction or not prediction[field]:
                    prediction[field] = '0' if field != 'crop' else 'Unknown'
            
            # Convert numerical fields to float/int for JSON serialization
            try:
                prediction['predicted_yield'] = float(prediction['predicted_yield'])
                prediction['confidence'] = int(prediction['confidence'])
                prediction['drought_risk'] = float(prediction['drought_risk'])
                prediction['flood_risk'] = float(prediction['flood_risk'])
                prediction['pest_risk'] = float(prediction['pest_risk'])
            except (ValueError, TypeError):
                # Handle cases where conversion fails
                if not isinstance(prediction['predicted_yield'], (int, float)):
                    prediction['predicted_yield'] = 0.0
                if not isinstance(prediction['confidence'], (int, float)):
                    prediction['confidence'] = 0
                if not isinstance(prediction['drought_risk'], (int, float)):
                    prediction['drought_risk'] = 0.0
                if not isinstance(prediction['flood_risk'], (int, float)):
                    prediction['flood_risk'] = 0.0
                if not isinstance(prediction['pest_risk'], (int, float)):
                    prediction['pest_risk'] = 0.0
        
        print(f"API: Found {len(predictions_data)} yield predictions for date: {date}")
        return jsonify(predictions_data)
    except Exception as e:
        print(f"Error in yield predictions API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/risk_map')
def get_risk_map():
    date = request.args.get('date')
    risk_type = request.args.get('risk_type', 'general')
    crop_type = request.args.get('crop_type', 'all')
    
    if not date:
        return jsonify({'error': 'Date parameter is required'}), 400
    
    # Get GeoJSON for the given date and risk type
    try:
        geojson_path = os.path.join('data', 'parcels.geojson')
        with open(geojson_path, 'r') as f:
            geojson = json.load(f)
        
        # Apply crop type filter if specified
        if crop_type != 'all':
            filtered_features = []
            for feature in geojson['features']:
                if crop_type.lower() == 'soja':
                    if 'crop' in feature['properties'] and feature['properties']['crop'] and feature['properties']['crop'].lower() == 'soja':
                        filtered_features.append(feature)
                elif crop_type.lower() == 'maiz':
                    if 'crop' in feature['properties'] and feature['properties']['crop'] and feature['properties']['crop'].lower() == 'maiz':
                        filtered_features.append(feature)
            
            # Replace the features with the filtered list
            geojson['features'] = filtered_features
        
        # Apply risk level based on the selected risk type
        for feature in geojson['features']:
            if risk_type == 'drought':
                feature['properties']['risk_level'] = feature['properties'].get('drought_probability', 0) / 100
            elif risk_type == 'flood':
                feature['properties']['risk_level'] = feature['properties'].get('flood_probability', 0) / 100
            elif risk_type == 'pest':
                feature['properties']['risk_level'] = feature['properties'].get('pest_probability', 0) / 100
            else:
                # General risk is an average of all risk factors
                drought = feature['properties'].get('drought_probability', 0)
                flood = feature['properties'].get('flood_probability', 0)
                hail = feature['properties'].get('hail_probability', 0)
                pest = feature['properties'].get('pest_probability', 0)
                
                # Average all available risk factors
                total = 0
                count = 0
                for risk in [drought, flood, hail, pest]:
                    if risk > 0:
                        total += risk
                        count += 1
                
                if count > 0:
                    feature['properties']['risk_level'] = total / (count * 100)
                else:
                    feature['properties']['risk_level'] = 0
        
        return jsonify(geojson)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard_summary')
def dashboard_summary():
    try:
        # Get total number of parcels
        with open('data/parcels.geojson') as f:
            parcels_data = json.load(f)
            if 'features' not in parcels_data:
                raise ValueError("Invalid parcels.geojson format: missing 'features' key")
        total_parcels = len(parcels_data['features'])

        # Calculate high risk areas using base_risk > 0.35
        high_risk_areas = sum(1 for feature in parcels_data['features'] 
                             if feature.get('properties', {}).get('base_risk', 0) > 0.35)

        # Calculate insured parcels (assuming all are insured for now)
        insured_parcels = total_parcels

        # Calculate crop-specific metrics
        crop_metrics = {}
        try:
            with open('data/yield_predictions.csv') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise ValueError("Empty yield_predictions.csv file")

                required_fields = ['crop', 'predicted_yield', 'drought_probability', 'flood_probability', 'hail_probability']
                for field in required_fields:
                    if field not in reader.fieldnames:
                        raise ValueError(f"Missing required field in yield_predictions.csv: {field}")

                crop_data = {}
                for row in reader:
                    try:
                        crop = row['crop']
                        if crop not in crop_data:
                            crop_data[crop] = {
                                'yield_sum': 0,
                                'count': 0,
                                'risk_sum': {'drought': 0, 'flood': 0, 'pest': 0}
                            }
                        crop_data[crop]['yield_sum'] += float(row['predicted_yield'])
                        crop_data[crop]['count'] += 1
                        crop_data[crop]['risk_sum']['drought'] += float(row['drought_probability'])
                        crop_data[crop]['risk_sum']['flood'] += float(row['flood_probability'])
                        crop_data[crop]['risk_sum']['pest'] += float(row['hail_probability'])
                    except (ValueError, KeyError) as e:
                        print(f"Error processing row: {row}. Error: {str(e)}")
                        continue

                # Calculate averages
                for crop, data in crop_data.items():
                    crop_metrics[crop] = {
                        'average_yield': round(data['yield_sum'] / data['count'], 2),
                        'average_risks': {
                            'drought': round(data['risk_sum']['drought'] / data['count'], 2),
                            'flood': round(data['risk_sum']['flood'] / data['count'], 2),
                            'pest': round(data['risk_sum']['pest'] / data['count'], 2)
                        }
                    }
        except Exception as e:
            print(f"Error processing yield predictions: {str(e)}")
            crop_metrics = {}

        return jsonify({
            'total_parcels': total_parcels,
            'high_risk_areas': high_risk_areas,
            'insured_parcels': insured_parcels,
            'crop_metrics': crop_metrics
        })
    except Exception as e:
        print(f"Error in dashboard_summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard')
def get_dashboard_data():
    """API endpoint for getting dashboard overview data"""
    # Get latest statistics for dashboard overview
    stats = dashboard_summary()
    return jsonify(stats)

@app.route('/api/risk_analysis')
def get_risk_analysis():
    """API endpoint for getting risk analysis data"""
    # Analysis date can be specified or default to latest
    date = request.args.get('date', climate_data['date'].max())
    
    # Get aggregated risk statistics by risk type
    risk_stats = {
        'drought': climate_data[climate_data['date'] == date]['drought_risk'].mean(),
        'flood': climate_data[climate_data['date'] == date]['flood_risk'].mean(),
        'frost': climate_data[climate_data['date'] == date]['frost_risk'].mean(),
        'hail': climate_data[climate_data['date'] == date]['hail_risk'].mean(),
        'general': climate_data[climate_data['date'] == date]['overall_risk'].mean()
    }
    
    # Count parcels by risk level
    risk_levels = {
        'high': len(climate_data[(climate_data['date'] == date) & (climate_data['overall_risk'] > 0.7)]),
        'medium': len(climate_data[(climate_data['date'] == date) & (climate_data['overall_risk'].between(0.3, 0.7))]),
        'low': len(climate_data[(climate_data['date'] == date) & (climate_data['overall_risk'] < 0.3)])
    }
    
    return jsonify({
        'risk_stats': risk_stats,
        'risk_levels': risk_levels,
        'total_parcels': len(parcels_gdf)
    })

@app.route('/api/crop_performance')
def get_crop_performance():
    """API endpoint for getting crop performance data"""
    # Get date or default to latest
    date = request.args.get('date', yield_predictions['date'].max())
    
    # Group by crop and calculate averages
    crop_data = []
    for crop_type in parcels_gdf['crop'].unique():
        if pd.isna(crop_type):
            continue
            
        # Get parcels with this crop
        crop_parcels = parcels_gdf[parcels_gdf['crop'] == crop_type]['id'].tolist()
        
        # Get yield predictions for these parcels
        crop_yields = yield_predictions[
            (yield_predictions['date'] == date) & 
            (yield_predictions['parcel_id'].isin(crop_parcels))
        ]
        
        if not crop_yields.empty:
            crop_data.append({
                'crop': crop_type,
                'avg_yield': crop_yields['predicted_yield'].mean(),
                'avg_health': crop_yields['crop_health'].mean() if 'crop_health' in crop_yields.columns else None,
                'parcel_count': len(crop_parcels)
            })
    
    return jsonify(crop_data)

@app.route('/api/insurance_overview')
def get_insurance_overview():
    """API endpoint for getting insurance product overview"""
    # Simply return all insurance products
    return jsonify(insurance_products.to_dict('records'))

# Ensure the templates and static directories exist
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

# Ruta para acceder al módulo de análisis de riesgos
@app.route('/risk_analysis')
def risk_analysis():
    """Ruta para acceder al módulo de análisis de riesgos"""
    # Redireccionar a la página de análisis de riesgos
    return render_template('risk_analysis.html')

# Start the application
if __name__ == '__main__':
    print("Loading application data...")
    print(f"Loaded {len(parcels_gdf)} parcels")
    print(f"Loaded {len(climate_data)} climate data entries")
    print(f"Loaded {len(yield_predictions)} yield predictions")
    print("Starting Flask application on http://127.0.0.1:5000/")
    app.run(debug=True, port=5000)
