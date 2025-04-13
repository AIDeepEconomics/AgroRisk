import os
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon
import folium
from folium.plugins import TimestampedGeoJson
import branca.colormap as cm
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
import pyproj
from functools import partial
from shapely.ops import transform
# Import map_rendering module
from data.map_rendering import create_risk_map, create_animated_risk_map
# Import data_generation module
from data.data_generation_new import generate_climate_data, generate_insurance_products, calculate_area_in_hectares

# Force folium to load all required plugins for terrain maps
folium.Map._default_js = [
    ('leaflet',
     'https://cdn.jsdelivr.net/npm/leaflet@1.6.0/dist/leaflet.js'),
    ('jquery',
     'https://code.jquery.com/jquery-1.12.4.min.js'),
    ('bootstrap',
     'https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/js/bootstrap.min.js'),
    ('awesome_markers',
     'https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.js'),
]

folium.Map._default_css = [
    ('leaflet_css',
     'https://cdn.jsdelivr.net/npm/leaflet@1.6.0/dist/leaflet.css'),
    ('bootstrap_css',
     'https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css'),
    ('bootstrap_theme_css',
     'https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap-theme.min.css'),
    ('awesome_markers_font_css',
     'https://maxcdn.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css'),
    ('awesome_markers_css',
     'https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.css'),
    ('awesome_rotate_css',
     'https://cdn.jsdelivr.net/gh/python-visualization/folium/folium/templates/leaflet.awesome.rotate.min.css'),
]

app = Flask(__name__)

# Directory for data
os.makedirs('data', exist_ok=True)

# Function to generate sample parcels with irregular shapes
def generate_parcels(n=7):
    parcels = []
    # Base coordinates for a region in Uruguay
    base_lat, base_lon = -32.8, -56.2
    
    # Soil types and their colors for background pattern
    soil_types = ['Franco-arcilloso', 'Arcilloso', 'Franco-arenoso', 'Limoso']
    
    for i in range(n):
        # Generate irregular shape for parcel
        points = []
        center_lat = base_lat + random.uniform(-0.1, 0.1)
        center_lon = base_lon + random.uniform(-0.1, 0.1)
        size = random.uniform(0.01, 0.03)
        
        # Create 4-7 points for polygon
        num_points = random.randint(4, 7)
        for j in range(num_points):
            angle = j * (2 * np.pi / num_points)
            # Vary radius for irregularity
            radius = size * random.uniform(0.8, 1.2)
            lat = center_lat + radius * np.cos(angle)
            lon = center_lon + radius * np.sin(angle)
            points.append((lon, lat))
        
        # Close polygon
        points.append(points[0])
        
        polygon = Polygon(points)
        
        # Calculate actual area in hectares using the polygon geometry
        area = calculate_area_in_hectares(polygon, center_lat)
        
        parcel = {
            'id': f'Field_{chr(65+i)}',
            'area': area,
            'soil_type': random.choice(soil_types),
            'crop': 'Soja',
            'base_risk': random.uniform(0.1, 0.7),
            'geometry': polygon
        }
        parcels.append(parcel)
    
    return gpd.GeoDataFrame(parcels, geometry='geometry')

# Initialize data
parcels_file = 'data/parcels.geojson'
climate_file = 'data/climate_risk_30days.csv'
yield_file = 'data/yield_predictions.csv'
insurance_file = 'data/insurance_products.csv'

# CRITICAL: We NEVER want to regenerate parcels if the file exists
# This is to preserve the custom Chacra parcels
if os.path.exists(parcels_file):
    parcels_gdf = gpd.read_file(parcels_file)
    print(f"Loaded existing parcels from {parcels_file}")
    
    # Recalculate areas based on actual geometries
    for idx, row in parcels_gdf.iterrows():
        # Get the centroid latitude for better projection
        centroid = row['geometry'].centroid
        lat_center = centroid.y
        
        # Update area with calculated value - convert to float first to avoid dtype warning
        parcels_gdf.at[idx, 'area'] = float(calculate_area_in_hectares(row['geometry'], lat_center))
        
else:
    # Only generate new parcels if file doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
    parcels_gdf = generate_parcels(7)
    parcels_gdf.to_file(parcels_file, driver='GeoJSON')
    print(f"Generated new parcels and saved to {parcels_file}")

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

# Load or generate climate data
if os.path.exists(climate_file):
    climate_data = pd.read_csv(climate_file)
    print(f"Loaded existing climate data from {climate_file}")
else:
    climate_data = generate_climate_data(parcels_gdf)
    climate_data.to_csv(climate_file, index=False)
    print(f"Generated new climate data and saved to {climate_file}")

# Load or generate yield predictions
# CRITICAL: We want to preserve existing yield predictions to maintain crop types
if os.path.exists(yield_file):
    yield_predictions = pd.read_csv(yield_file)
    print(f"Loaded existing yield predictions from {yield_file}")
else:
    # IMPORTANT: We are NO LONGER generating yield predictions here
    # Instead use data/update_crop_and_yield.py to generate this file
    print(f"Yield predictions file not found: {yield_file}")
    print(f"Please run data/update_crop_and_yield.py to generate it")
    # Create an empty DataFrame with the expected columns
    yield_predictions = pd.DataFrame(columns=[
        'parcel_id', 'date', 'predicted_yield', 'confidence',
        'drought_probability', 'flood_probability', 'hail_probability', 'crop'
    ])
    # yield_predictions = generate_yield_predictions(parcels_gdf)  # Commented out
    # yield_predictions.to_csv(yield_file, index=False)  # Commented out

# Load or generate insurance products
if os.path.exists(insurance_file):
    insurance_products = pd.read_csv(insurance_file)
    print(f"Loaded existing insurance products from {insurance_file}")
else:
    insurance_products = generate_insurance_products()
    insurance_products.to_csv(insurance_file, index=False)
    print(f"Generated new insurance products and saved to {insurance_file}")

# Flask Routes
@app.route('/')
def index():
    # Pass data to template
    dates = sorted(climate_data['date'].unique())
    alerts = climate_data.dropna(subset=['alert']).to_dict('records')
    
    return render_template(
        'index.html', 
        dates=dates,
        alerts=alerts,
        insurance_products=insurance_products.to_dict('records')
    )

@app.route('/map')
def map_view():
    date = request.args.get('date', climate_data['date'].min())
    risk_type = request.args.get('risk_type', 'general')
    
    # Create map using the imported module
    m = create_risk_map(date, climate_data, parcels_gdf, risk_type)
    
    # Save map to HTML string
    map_html = m.get_root().render()
    
    return map_html

@app.route('/animated_map')
def animated_map_view():
    """
    Route for displaying an animated risk map showing changes over time
    """
    risk_type = request.args.get('risk_type', 'general')
    
    # Create animated map using the imported module
    m = create_animated_risk_map(parcels_gdf, climate_data, risk_type)
    
    # Save map to HTML string
    map_html = m.get_root().render()
    
    return map_html

@app.route('/api/parcels')
def get_parcels():
    # Convert to GeoJSON for API response
    # But DO NOT save to file
    geojson = parcels_gdf.to_json()
    return geojson

@app.route('/api/risk_data')
def get_risk_data():
    date = request.args.get('date', climate_data['date'].min())
    parcel_id = request.args.get('parcel_id', None)
    
    # Filter data
    filtered_data = climate_data[climate_data['date'] == date]
    
    if parcel_id:
        filtered_data = filtered_data[filtered_data['parcel_id'] == parcel_id]
    
    return jsonify(filtered_data.to_dict('records'))

@app.route('/api/yield_predictions')
def get_yield_predictions():
    date = request.args.get('date', yield_predictions['date'].min())
    parcel_id = request.args.get('parcel_id', None)
    
    # Filter data
    filtered_data = yield_predictions[yield_predictions['date'] == date]
    
    if parcel_id:
        filtered_data = filtered_data[filtered_data['parcel_id'] == parcel_id]
    
    # No need to merge with parcels data since crop information is already in the CSV file
    # Just return the filtered data as is, which already includes the crop column
    return jsonify(filtered_data.to_dict('records'))

# Create templates directory and HTML template
os.makedirs('templates', exist_ok=True)

with open('templates/index.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dynamic Risk Map for Microinsurance</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        #map-container {
            height: 500px;
            width: 100%;
            border: 2px solid #ccc;
            border-radius: 5px;
        }
        .risk-high {
            color: #f44336;
            font-weight: bold;
        }
        .risk-medium {
            color: #ff9800;
            font-weight: bold;
        }
        .risk-low {
            color: #4caf50;
            font-weight: bold;
        }
        .time-slider-container {
            padding: 10px 20px;
            background-color: #f8f9fa;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        .time-slider {
            width: 100%;
        }
        .slider-labels {
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
        }
        .play-button {
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="container mt-4 mb-4">
        <h1 class="text-center mb-4">Dynamic Risk Map for Agricultural Microinsurance</h1>
        
        <div class="row mb-3">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        Time Navigation
                    </div>
                    <div class="card-body">
                        <div class="time-slider-container">
                            <div class="d-flex align-items-center mb-2">
                                <button id="play-button" class="btn btn-sm btn-primary play-button">
                                    <i class="fa fa-play"></i> Play
                                </button>
                                <div class="w-100">
                                    <input type="range" class="form-range time-slider" id="time-slider" min="0" max="29" value="0">
                                </div>
                            </div>
                            <div class="slider-labels">
                                <span>Jan 15, 2025</span>
                                <span id="current-date">Jan 15, 2025</span>
                                <span>Feb 14, 2025</span>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <select id="date-selector" class="form-select">
                                    {% for date in dates %}
                                        <option value="{{ date }}">{{ date }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div class="col-md-6">
                                <select id="risk-type" class="form-select">
                                    <option value="general">General Risk</option>
                                    <option value="drought">Drought Risk</option>
                                    <option value="flood">Flood Risk</option>
                                    <option value="pest">Pest Risk</option>
                                </select>
                            </div>
                        </div>
                        <div class="row mt-3">
                            <div class="col-md-12">
                                <button id="animated-map-btn" class="btn btn-info w-100">
                                    <i class="fa fa-film"></i> View Animated Risk Map
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="map-container" class="mb-4">
            <iframe id="map-frame" width="100%" height="100%" frameborder="0"></iframe>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-4">
                    <div class="card-header bg-danger text-white">
                        Risk Alerts
                    </div>
                    <div class="card-body" id="alerts-container">
                        <div id="alerts-list">
                            {% if alerts %}
                                <ul class="list-group">
                                {% for alert in alerts %}
                                    <li class="list-group-item {% if 'HIGH ALERT' in alert.alert %}list-group-item-danger{% else %}list-group-item-warning{% endif %}">
                                        {{ alert.alert }} <small>({{ alert.date }})</small>
                                    </li>
                                {% endfor %}
                                </ul>
                            {% else %}
                                <p>No active alerts at this time.</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header bg-info text-white">
                        Yield Predictions
                    </div>
                    <div class="card-body">
                        <div id="yield-predictions">
                            Loading predictions...
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        Available Microinsurance Products
                    </div>
                    <div class="card-body">
                        <div class="accordion" id="insuranceAccordion">
                            {% for product in insurance_products %}
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{{ loop.index }}">
                                        {{ product.name }}
                                    </button>
                                </h2>
                                <div id="collapse{{ loop.index }}" class="accordion-collapse collapse" data-bs-parent="#insuranceAccordion">
                                    <div class="accordion-body">
                                        <p><strong>Coverage:</strong> Up to ${{ product.coverage }}/ha</p>
                                        <p><strong>Threshold:</strong> {{ product.threshold }}</p>
                                        <p><strong>Minimum Premium:</strong> ${{ product.min_premium }}/ha (varies by risk level)</p>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/js/all.min.js"></script>
    <script>
        // Global variables
        let allDates = [];
        let isPlaying = false;
        let animationInterval;
        
        // Load map with default parameters
        function loadMap(date, riskType) {
            const mapFrame = document.getElementById('map-frame');
            mapFrame.src = `/map?date=${date}&risk_type=${riskType}`;
        }
        
        // Load yield predictions for the selected date
        async function loadYieldPredictions(date) {
            try {
                const response = await fetch(`/api/yield_predictions?date=${date}`);
                const predictions = await response.json();
                
                if (predictions.length === 0) {
                    document.getElementById('yield-predictions').innerHTML = '<p>No predictions available for this date.</p>';
                    return;
                }
                
                let html = '<div class="table-responsive">';
                html += '<table class="table table-sm">';
                html += '<thead><tr><th>Parcel ID</th><th>Crop Type</th><th>Predicted Yield (ton/ha)</th><th>Confidence</th><th>Drought Risk</th><th>Flood Risk</th><th>Hail Risk</th></tr></thead>';
                html += '<tbody>';
                
                predictions.forEach(pred => {
                    const confidenceClass = pred.confidence > 70 ? 'bg-success text-white' : 
                                          pred.confidence > 50 ? 'bg-warning' : 'bg-danger text-white';
                    
                    html += `<tr>
                              <td>${pred.parcel_id}</td>
                              <td><strong>${pred.crop || 'Unknown'}</strong></td>
                              <td>${pred.predicted_yield}</td>
                              <td><span class="badge ${confidenceClass}">${pred.confidence}%</span></td>
                              <td>${pred.drought_probability}%</td>
                              <td>${pred.flood_probability}%</td>
                              <td>${pred.hail_probability}%</td>
                             </tr>`;
                });
                
                html += '</tbody></table></div>';
                document.getElementById('yield-predictions').innerHTML = html;
                
            } catch (error) {
                console.error('Error loading yield predictions:', error);
                document.getElementById('yield-predictions').innerHTML = '<p class="text-danger">Error loading predictions.</p>';
            }
        }
        
        // Load risk alerts for the selected date
        async function loadAlerts(date) {
            try {
                const response = await fetch(`/api/risk_data?date=${date}`);
                const data = await response.json();
                
                // Filter alerts (non-null)
                const alerts = data.filter(item => item.alert);
                
                if (alerts.length === 0) {
                    document.getElementById('alerts-list').innerHTML = '<p>No active alerts at this time.</p>';
                    return;
                }
                
                let html = '<ul class="list-group">';
                alerts.forEach(alert => {
                    const alertClass = alert.alert.includes('HIGH ALERT') ? 'list-group-item-danger' : 'list-group-item-warning';
                    html += `<li class="list-group-item ${alertClass}">${alert.alert}</li>`;
                });
                html += '</ul>';
                
                document.getElementById('alerts-list').innerHTML = html;
                
            } catch (error) {
                console.error('Error loading alerts:', error);
                document.getElementById('alerts-list').innerHTML = '<p class="text-danger">Error loading alerts.</p>';
            }
        }
        
        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            const dateSelector = document.getElementById('date-selector');
            const riskTypeSelector = document.getElementById('risk-type');
            const timeSlider = document.getElementById('time-slider');
            const playButton = document.getElementById('play-button');
            const currentDateDisplay = document.getElementById('current-date');
            const animatedMapBtn = document.getElementById('animated-map-btn');
            
            // Collect all available dates from the selector
            Array.from(dateSelector.options).forEach(option => {
                allDates.push(option.value);
            });
            
            // Set max value for slider based on number of dates
            if (allDates.length > 0) {
                timeSlider.max = allDates.length - 1;
            }
            
            // Load initial map
            loadMap(dateSelector.value, riskTypeSelector.value);
            loadYieldPredictions(dateSelector.value);
            loadAlerts(dateSelector.value);
            updateCurrentDateDisplay(dateSelector.value);
            
            // Update when date changes from dropdown
            dateSelector.addEventListener('change', function() {
                // Update slider position to match selected date
                const dateIndex = allDates.indexOf(this.value);
                if (dateIndex !== -1) {
                    timeSlider.value = dateIndex;
                }
                
                loadMap(this.value, riskTypeSelector.value);
                loadYieldPredictions(this.value);
                loadAlerts(this.value);
                updateCurrentDateDisplay(this.value);
            });
            
            // Update when slider changes
            timeSlider.addEventListener('input', function() {
                const selectedDate = allDates[this.value];
                if (selectedDate) {
                    // Update dropdown to match slider
                    dateSelector.value = selectedDate;
                    
                    loadMap(selectedDate, riskTypeSelector.value);
                    loadYieldPredictions(selectedDate);
                    loadAlerts(selectedDate);
                    updateCurrentDateDisplay(selectedDate);
                }
            });
            
            // Play/Pause animation
            playButton.addEventListener('click', function() {
                if (isPlaying) {
                    // Stop animation
                    clearInterval(animationInterval);
                    this.innerHTML = '<i class="fa fa-play"></i> Play';
                    isPlaying = false;
                } else {
                    // Start animation
                    this.innerHTML = '<i class="fa fa-pause"></i> Pause';
                    isPlaying = true;
                    
                    animationInterval = setInterval(() => {
                        let currentValue = parseInt(timeSlider.value);
                        const maxValue = parseInt(timeSlider.max);
                        
                        // Increment and loop if needed
                        currentValue = (currentValue >= maxValue) ? 0 : currentValue + 1;
                        
                        // Update slider value
                        timeSlider.value = currentValue;
                        
                        // Trigger the same actions as manual sliding
                        const selectedDate = allDates[currentValue];
                        if (selectedDate) {
                            dateSelector.value = selectedDate;
                            loadMap(selectedDate, riskTypeSelector.value);
                            loadYieldPredictions(selectedDate);
                            loadAlerts(selectedDate);
                            updateCurrentDateDisplay(selectedDate);
                        }
                    }, 1500); // Advance every 1.5 seconds
                }
            });
            
            // Update when risk type changes
            riskTypeSelector.addEventListener('change', function() {
                loadMap(dateSelector.value, this.value);
            });
            
            // Handle animated map button click
            animatedMapBtn.addEventListener('click', function() {
                const riskType = riskTypeSelector.value;
                // Open animated map in a new window
                window.open(`/animated_map?risk_type=${riskType}`, '_blank');
            });
            
            // Helper function to update the current date display
            function updateCurrentDateDisplay(dateString) {
                // Convert YYYY-MM-DD to more readable format
                const date = new Date(dateString);
                const options = { month: 'short', day: 'numeric', year: 'numeric' };
                currentDateDisplay.textContent = date.toLocaleDateString('en-US', options);
            }
        });
    </script>
</body>
</html>
    ''')

# Start the application
if __name__ == '__main__':
    print("Generating sample data...")
    print(f"Created {len(parcels_gdf)} parcels")
    print(f"Generated {len(climate_data)} climate data entries")
    print(f"Generated {len(yield_predictions)} yield predictions")
    print("Starting Flask application on http://127.0.0.1:5000/")
    app.run(debug=True, port=5000)
