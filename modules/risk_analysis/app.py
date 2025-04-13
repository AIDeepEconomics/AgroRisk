"""
Main application for the AgroSmartRisk Time-Series Analysis proof-of-concept.
This module integrates the database, API, and visualization components.
"""
from flask import Flask, render_template, jsonify, request, send_from_directory
from database.models import db, Parcel, RiskData, RiskAnalysis, WeatherData
from backend.api import risk_api
from backend.trend_analysis import (
    detect_change_points, perform_seasonal_decomposition,
    test_stationarity, forecast_arima, analyze_risk_patterns, calculate_risk_volatility
)
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for API requests
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Configure database
import os
app.instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(app.instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, "agrosmartrisk.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Print database path for debugging
print(f"Database path: {os.path.join(app.instance_path, 'agrosmartrisk.db')}")

# Initialize database
db.init_app(app)

# Register API blueprint
app.register_blueprint(risk_api, url_prefix='/api')

# Routes
@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('risk_analysis_integrated.html')

@app.route('/charts')
def charts():
    """Serve the static charts page"""
    return render_template('charts.html')

@app.route('/risk-analysis')
def risk_analysis():
    """Route for the new risk analysis page that matches index12.html design"""
    return render_template('risk_analysis_integrated.html')

@app.route('/risk-analysis-sidebar')
def risk_analysis_sidebar():
    """Route to serve the updated risk analysis page with sidebar menu structure"""
    return render_template('risk_analysis_integrated.html')

@app.route('/risk-analysis-exact')
def risk_analysis_exact():
    """Route to serve the risk analysis page with exact structure matching index12.html template"""
    return render_template('risk_analysis_integrated.html')

@app.route('/frontend')
def frontend_index():
    """Route to serve the updated frontend index.html with sidebar menu matching index12.html"""
    return render_template('risk_analysis_integrated.html')

@app.route('/templates/<path:path>')
def serve_template(path):
    """Serve template files"""
    return send_from_directory('templates', path)

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

# API routes for risk analysis frontend
@app.route('/api/parcels')
def get_parcels():
    """Get all parcels for dropdown selection"""
    try:
        parcels = Parcel.query.all()
        
        # Log for debugging
        print(f"Found {len(parcels)} parcels in the database")
        if parcels:
            for p in parcels[:3]:
                print(f"Sample parcel: ID={p.id}, Name={p.name}")
        
        return jsonify({
            'success': True,
            'data': [parcel.to_dict() for parcel in parcels],
            'count': len(parcels)
        })
    except Exception as e:
        print(f"Error in get_parcels: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error loading parcels data'
        }), 500

@app.route('/api/risk-data/<int:parcel_id>')
def get_risk_data(parcel_id):
    """Get risk data for a specific parcel with optional date range and risk type filter"""
    try:
        # Parse query parameters
        risk_type = request.args.get('risk_type', 'overall_risk')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Print debugging info
        print(f"Fetching risk data for parcel {parcel_id}, risk_type: {risk_type}, start_date: {start_date}, end_date: {end_date}")
        
        # Validate parcel exists
        parcel = Parcel.query.get_or_404(parcel_id)
        
        # Build query for risk data
        query = RiskData.query.filter(RiskData.parcel_id == parcel_id)
        
        # Apply date range filter if provided
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(RiskData.date >= start_date)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(RiskData.date <= end_date)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        # Order by date
        query = query.order_by(RiskData.date)
        
        # Execute query
        risk_data = query.all()
        
        print(f"Found {len(risk_data)} risk data records")
        
        if not risk_data:
            return jsonify({
                'success': True,
                'data': [],
                'parcel': parcel.to_dict(),
                'message': 'No risk data available for the specified parameters'
            })
        
        # Convert to dictionaries for JSON response
        data = []
        for item in risk_data:
            data.append({
                'id': item.id,
                'parcel_id': item.parcel_id,
                'date': item.date.strftime('%Y-%m-%d'),
                'drought_risk': item.drought_risk * 100 if item.drought_risk is not None else None,  # Convert to percentage
                'flood_risk': item.flood_risk * 100 if item.flood_risk is not None else None,
                'frost_risk': item.frost_risk * 100 if item.frost_risk is not None else None,
                'overall_risk': item.overall_risk * 100 if item.overall_risk is not None else None,
                'risk_type': getattr(item, 'risk_type', None)
            })
        
        return jsonify({
            'success': True,
            'data': data,
            'parcel': parcel.to_dict(),
            'count': len(data)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'An error occurred while fetching risk data'
        }), 500

@app.route('/api/risk-summary/<int:parcel_id>')
def get_risk_summary(parcel_id):
    """Get risk summary statistics for a specific parcel"""
    # Get recent risk data (last 30 days by default)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    risk_data = RiskData.query.filter_by(parcel_id=parcel_id)\
                            .filter(RiskData.date >= start_date)\
                            .filter(RiskData.date <= end_date)\
                            .all()
    
    if not risk_data:
        return jsonify({
            'message': 'No risk data available for this parcel',
            'parcel_id': parcel_id,
            'status': 'error'
        }), 404
    
    # Calculate average risk values
    drought_risks = [data.drought_risk for data in risk_data if data.drought_risk is not None]
    flood_risks = [data.flood_risk for data in risk_data if data.flood_risk is not None]
    frost_risks = [data.frost_risk for data in risk_data if data.frost_risk is not None]
    overall_risks = [data.overall_risk for data in risk_data if data.overall_risk is not None]
    
    # Prepare summary data
    summary = {
        'parcel_id': parcel_id,
        'drought_risk': sum(drought_risks) / len(drought_risks) if drought_risks else 0,
        'flood_risk': sum(flood_risks) / len(flood_risks) if flood_risks else 0,
        'frost_risk': sum(frost_risks) / len(frost_risks) if frost_risks else 0,
        'overall_risk': sum(overall_risks) / len(overall_risks) if overall_risks else 0,
        'period': f"{start_date} to {end_date}",
        'data_points': len(risk_data),
        'status': 'success'
    }
    
    return jsonify(summary)

@app.route('/api/risk-alerts/<int:parcel_id>')
def get_risk_alerts(parcel_id):
    """Get risk alerts for a specific parcel"""
    # Get recent risk data (last 30 days by default)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    risk_data = RiskData.query.filter_by(parcel_id=parcel_id)\
                            .filter(RiskData.date >= start_date)\
                            .filter(RiskData.date <= end_date)\
                            .all()
    
    alerts = []
    
    # Create alerts for high risk values (above 0.7)
    for data in risk_data:
        if data.drought_risk and data.drought_risk > 0.7:
            alerts.append({
                'date': data.date.strftime('%Y-%m-%d'),
                'risk_type': 'drought',
                'risk_value': data.drought_risk,
                'message': f'High drought risk detected on {data.date.strftime("%Y-%m-%d")}',
                'severity': 'high'
            })
        
        if data.flood_risk and data.flood_risk > 0.7:
            alerts.append({
                'date': data.date.strftime('%Y-%m-%d'),
                'risk_type': 'flood',
                'risk_value': data.flood_risk,
                'message': f'High flood risk detected on {data.date.strftime("%Y-%m-%d")}',
                'severity': 'high'
            })
            
        if data.frost_risk and data.frost_risk > 0.7:
            alerts.append({
                'date': data.date.strftime('%Y-%m-%d'),
                'risk_type': 'frost',
                'risk_value': data.frost_risk,
                'message': f'High frost risk detected on {data.date.strftime("%Y-%m-%d")}',
                'severity': 'high'
            })
    
    return jsonify({
        'parcel_id': parcel_id,
        'alerts': alerts,
        'count': len(alerts),
        'status': 'success'
    })

# Additional API endpoints for trend analysis
@app.route('/api/risk-data/change-points', methods=['GET'])
def get_change_points():
    """API endpoint for detecting change points in risk data"""
    # Parse query parameters
    parcel_id = request.args.get('parcel_id', type=int)
    risk_type = request.args.get('risk_type', 'overall')
    window = request.args.get('window', 7, type=int)
    
    if not parcel_id:
        return jsonify({'success': False, 'error': 'parcel_id is required'}), 400
    
    # Validate parcel exists
    parcel = Parcel.query.get_or_404(parcel_id)
    
    # Get risk data for the parcel
    risk_data = RiskData.query.filter(RiskData.parcel_id == parcel_id).order_by(RiskData.date).all()
    
    if not risk_data:
        return jsonify({'success': False, 'error': 'No risk data available for this parcel'}), 404
    
    # Prepare data for analysis
    dates = []
    values = []
    
    for data in risk_data:
        dates.append(data.date)
        if risk_type == 'drought':
            values.append(data.drought_risk)
        elif risk_type == 'flood':
            values.append(data.flood_risk)
        elif risk_type == 'frost':
            values.append(data.frost_risk)
        elif risk_type == 'pest':
            values.append(data.pest_risk)
        else:  # default to overall
            values.append(data.overall_risk)
    
    # Detect change points
    result = detect_change_points(dates, values, window_size=window)
    
    return jsonify({
        'success': True,
        'parcel': parcel.to_dict(),
        'risk_type': risk_type,
        'change_points': result
    })

@app.route('/api/risk-data/seasonal-decomposition', methods=['GET'])
def get_seasonal_decomposition():
    """API endpoint for seasonal decomposition of risk data"""
    # Parse query parameters
    parcel_id = request.args.get('parcel_id', type=int)
    risk_type = request.args.get('risk_type', 'overall')
    period = request.args.get('period', 30, type=int)
    
    if not parcel_id:
        return jsonify({'success': False, 'error': 'parcel_id is required'}), 400
    
    # Validate parcel exists
    parcel = Parcel.query.get_or_404(parcel_id)
    
    # Get risk data for the parcel
    risk_data = RiskData.query.filter(RiskData.parcel_id == parcel_id).order_by(RiskData.date).all()
    
    if not risk_data:
        return jsonify({'success': False, 'error': 'No risk data available for this parcel'}), 404
    
    # Prepare data for analysis
    dates = []
    values = []
    
    for data in risk_data:
        dates.append(data.date)
        if risk_type == 'drought':
            values.append(data.drought_risk)
        elif risk_type == 'flood':
            values.append(data.flood_risk)
        elif risk_type == 'frost':
            values.append(data.frost_risk)
        elif risk_type == 'pest':
            values.append(data.pest_risk)
        else:  # default to overall
            values.append(data.overall_risk)
    
    # Perform seasonal decomposition
    result = perform_seasonal_decomposition(dates, values, period=period)
    
    return jsonify({
        'success': True,
        'parcel': parcel.to_dict(),
        'risk_type': risk_type,
        'decomposition': result
    })

@app.route('/api/risk-data/stationarity', methods=['GET'])
def get_stationarity():
    """API endpoint for testing stationarity of risk data"""
    # Parse query parameters
    parcel_id = request.args.get('parcel_id', type=int)
    risk_type = request.args.get('risk_type', 'overall')
    
    if not parcel_id:
        return jsonify({'success': False, 'error': 'parcel_id is required'}), 400
    
    # Validate parcel exists
    parcel = Parcel.query.get_or_404(parcel_id)
    
    # Get risk data for the parcel
    risk_data = RiskData.query.filter(RiskData.parcel_id == parcel_id).order_by(RiskData.date).all()
    
    if not risk_data:
        return jsonify({'success': False, 'error': 'No risk data available for this parcel'}), 404
    
    # Prepare data for analysis
    dates = []
    values = []
    
    for data in risk_data:
        dates.append(data.date)
        if risk_type == 'drought':
            values.append(data.drought_risk)
        elif risk_type == 'flood':
            values.append(data.flood_risk)
        elif risk_type == 'frost':
            values.append(data.frost_risk)
        elif risk_type == 'pest':
            values.append(data.pest_risk)
        else:  # default to overall
            values.append(data.overall_risk)
    
    # Test stationarity
    result = test_stationarity(dates, values)
    
    return jsonify({
        'success': True,
        'parcel': parcel.to_dict(),
        'risk_type': risk_type,
        'stationarity': result
    })

@app.route('/api/risk-data/arima-forecast', methods=['GET'])
def get_arima_forecast():
    """API endpoint for ARIMA forecasting of risk data"""
    # Parse query parameters
    parcel_id = request.args.get('parcel_id', type=int)
    risk_type = request.args.get('risk_type', 'overall')
    days = request.args.get('days', 7, type=int)
    
    if not parcel_id:
        return jsonify({'success': False, 'error': 'parcel_id is required'}), 400
    
    # Validate parcel exists
    parcel = Parcel.query.get_or_404(parcel_id)
    
    # Get risk data for the parcel
    risk_data = RiskData.query.filter(RiskData.parcel_id == parcel_id).order_by(RiskData.date).all()
    
    if not risk_data:
        return jsonify({'success': False, 'error': 'No risk data available for this parcel'}), 404
    
    # Prepare data for analysis
    dates = []
    values = []
    
    for data in risk_data:
        dates.append(data.date)
        if risk_type == 'drought':
            values.append(data.drought_risk)
        elif risk_type == 'flood':
            values.append(data.flood_risk)
        elif risk_type == 'frost':
            values.append(data.frost_risk)
        elif risk_type == 'pest':
            values.append(data.pest_risk)
        else:  # default to overall
            values.append(data.overall_risk)
    
    # Perform ARIMA forecast
    result = forecast_arima(dates, values, forecast_days=days)
    
    return jsonify({
        'success': True,
        'parcel': parcel.to_dict(),
        'risk_type': risk_type,
        'forecast': result
    })

@app.route('/api/risk-data/risk-patterns', methods=['GET'])
def get_risk_patterns():
    """API endpoint for analyzing risk patterns"""
    # Parse query parameters
    parcel_id = request.args.get('parcel_id', type=int)
    risk_type = request.args.get('risk_type', 'overall')
    threshold = request.args.get('threshold', 0.7, type=float)
    
    if not parcel_id:
        return jsonify({'success': False, 'error': 'parcel_id is required'}), 400
    
    # Validate parcel exists
    parcel = Parcel.query.get_or_404(parcel_id)
    
    # Get risk data for the parcel
    risk_data = RiskData.query.filter(RiskData.parcel_id == parcel_id).order_by(RiskData.date).all()
    
    if not risk_data:
        return jsonify({'success': False, 'error': 'No risk data available for this parcel'}), 404
    
    # Prepare data for analysis
    dates = []
    values = []
    
    for data in risk_data:
        dates.append(data.date)
        if risk_type == 'drought':
            values.append(data.drought_risk)
        elif risk_type == 'flood':
            values.append(data.flood_risk)
        elif risk_type == 'frost':
            values.append(data.frost_risk)
        elif risk_type == 'pest':
            values.append(data.pest_risk)
        else:  # default to overall
            values.append(data.overall_risk)
    
    # Analyze risk patterns
    result = analyze_risk_patterns(dates, values, threshold=threshold)
    
    return jsonify({
        'success': True,
        'parcel': parcel.to_dict(),
        'risk_type': risk_type,
        'patterns': result
    })

@app.route('/api/risk-data/volatility', methods=['GET'])
def get_risk_volatility():
    """API endpoint for calculating risk volatility"""
    # Parse query parameters
    parcel_id = request.args.get('parcel_id', type=int)
    risk_type = request.args.get('risk_type', 'overall')
    window = request.args.get('window', 7, type=int)
    
    if not parcel_id:
        return jsonify({'success': False, 'error': 'parcel_id is required'}), 400
    
    # Validate parcel exists
    parcel = Parcel.query.get_or_404(parcel_id)
    
    # Get risk data for the parcel
    risk_data = RiskData.query.filter(RiskData.parcel_id == parcel_id).order_by(RiskData.date).all()
    
    if not risk_data:
        return jsonify({'success': False, 'error': 'No risk data available for this parcel'}), 404
    
    # Prepare data for analysis
    dates = []
    values = []
    
    for data in risk_data:
        dates.append(data.date)
        if risk_type == 'drought':
            values.append(data.drought_risk)
        elif risk_type == 'flood':
            values.append(data.flood_risk)
        elif risk_type == 'frost':
            values.append(data.frost_risk)
        elif risk_type == 'pest':
            values.append(data.pest_risk)
        else:  # default to overall
            values.append(data.overall_risk)
    
    # Calculate volatility
    result = calculate_risk_volatility(dates, values, window_size=window)
    
    return jsonify({
        'success': True,
        'parcel': parcel.to_dict(),
        'risk_type': risk_type,
        'volatility': result
    })

@app.route('/api/debug/parcels')
def debug_parcels():
    """Debug endpoint to check parcels in the database"""
    parcels = Parcel.query.all()
    count = len(parcels)
    sample = [p.to_dict() for p in parcels[:5]] if parcels else []
    
    return jsonify({
        'count': count,
        'sample': sample,
        'message': f'Found {count} parcels in the database',
        'database_path': app.config['SQLALCHEMY_DATABASE_URI']
    })

# Data generation functions for demo purposes
def generate_sample_data():
    """Generate sample data for the proof-of-concept"""
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Check if data already exists
        existing_parcels = Parcel.query.all()
        if len(existing_parcels) > 0:
            print(f"Sample data already exists. Found {len(existing_parcels)} parcels.")
            
            # Debug: Print out a few parcels to verify they exist
            for p in existing_parcels[:3]:
                print(f"Sample parcel: ID={p.id}, Name={p.name}, Crop={p.crop_type}")
                
            return
        
        print("No existing parcels found. Creating sample data...")
        
        # Generate parcels
        parcels = []
        for i in range(1, 31):  # Create 30 parcels
            parcel = Parcel(
                name=f"Agricultural Parcel {i}",
                area=random.uniform(5.0, 50.0),
                soil_type=random.choice(["Clay", "Loam", "Sandy", "Silt"]),
                crop_type=random.choice(["Maize", "Wheat", "Soybeans"]),
                latitude=random.uniform(35.0, 45.0),
                longitude=random.uniform(-100.0, -80.0)
            )
            db.session.add(parcel)
            parcels.append(parcel)
        
        try:
            db.session.commit()
            print(f"Successfully generated {len(parcels)} parcels")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating parcels: {str(e)}")
        
        # Generate risk data for the past 365 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)
        
        for parcel in parcels:
            # Generate base risk values with seasonal patterns
            dates = []
            drought_base = []
            flood_base = []
            frost_base = []
            pest_base = []
            
            current_date = start_date
            while current_date <= end_date:
                dates.append(current_date)
                
                # Day of year (0-365)
                day_of_year = current_date.timetuple().tm_yday
                
                # Seasonal patterns
                # Drought risk: Higher in summer
                drought_seasonal = 0.3 + 0.4 * np.sin(2 * np.pi * (day_of_year - 172) / 365)
                
                # Flood risk: Higher in spring
                flood_seasonal = 0.3 + 0.4 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
                
                # Frost risk: Higher in winter
                frost_seasonal = 0.3 + 0.4 * np.sin(2 * np.pi * (day_of_year - 355) / 365)
                
                # Pest risk: Higher in late spring/early summer
                pest_seasonal = 0.3 + 0.4 * np.sin(2 * np.pi * (day_of_year - 120) / 365)
                
                drought_base.append(max(0, min(1, drought_seasonal)))
                flood_base.append(max(0, min(1, flood_seasonal)))
                frost_base.append(max(0, min(1, frost_seasonal)))
                pest_base.append(max(0, min(1, pest_seasonal)))
                
                current_date += timedelta(days=1)
            
            # Add random variations and trends
            drought_risk = np.array(drought_base) + np.random.normal(0, 0.05, len(dates))
            flood_risk = np.array(flood_base) + np.random.normal(0, 0.05, len(dates))
            frost_risk = np.array(frost_base) + np.random.normal(0, 0.05, len(dates))
            pest_risk = np.array(pest_base) + np.random.normal(0, 0.05, len(dates))
            
            # Add some trends
            x = np.arange(len(dates))
            drought_trend = 0.0001 * x  # Slight increasing trend
            flood_trend = -0.0001 * x   # Slight decreasing trend
            
            drought_risk += drought_trend
            flood_risk += flood_trend
            
            # Ensure values are within 0-1 range
            drought_risk = np.clip(drought_risk, 0, 1)
            flood_risk = np.clip(flood_risk, 0, 1)
            frost_risk = np.clip(frost_risk, 0, 1)
            pest_risk = np.clip(pest_risk, 0, 1)
            
            # Calculate overall risk as weighted average
            overall_risk = 0.3 * drought_risk + 0.3 * flood_risk + 0.2 * frost_risk + 0.2 * pest_risk
            
            # Add some high-risk events
            for _ in range(5):
                event_start = random.randint(0, len(dates) - 14)
                event_duration = random.randint(3, 14)
                event_type = random.choice(["drought", "flood", "frost", "pest"])
                
                for i in range(event_start, min(event_start + event_duration, len(dates))):
                    if event_type == "drought":
                        drought_risk[i] = min(1.0, drought_risk[i] + random.uniform(0.2, 0.5))
                    elif event_type == "flood":
                        flood_risk[i] = min(1.0, flood_risk[i] + random.uniform(0.2, 0.5))
                    elif event_type == "frost":
                        frost_risk[i] = min(1.0, frost_risk[i] + random.uniform(0.2, 0.5))
                    elif event_type == "pest":
                        pest_risk[i] = min(1.0, pest_risk[i] + random.uniform(0.2, 0.5))
                    
                    # Recalculate overall risk
                    overall_risk[i] = 0.3 * drought_risk[i] + 0.3 * flood_risk[i] + 0.2 * frost_risk[i] + 0.2 * pest_risk[i]
            
            # Create risk data records
            for i, date in enumerate(dates):
                # Add alerts for high risk values
                alert = None
                if overall_risk[i] >= 0.8:
                    alert = "CRITICAL: Multiple severe risk factors detected"
                elif overall_risk[i] >= 0.7:
                    alert = "HIGH RISK: Immediate attention required"
                elif overall_risk[i] >= 0.6:
                    alert = "ELEVATED RISK: Monitor conditions closely"
                
                risk_data = RiskData(
                    parcel_id=parcel.id,
                    date=date,
                    drought_risk=float(drought_risk[i]),
                    flood_risk=float(flood_risk[i]),
                    frost_risk=float(frost_risk[i]),
                    pest_risk=float(pest_risk[i]),
                    overall_risk=float(overall_risk[i]),
                    alert=alert
                )
                db.session.add(risk_data)
            
            db.session.commit()
            print(f"Generated risk data for Parcel {parcel.id}")
        
        # Generate weather data
        for parcel in parcels:
            current_date = start_date
            while current_date <= end_date:
                # Day of year (0-365)
                day_of_year = current_date.timetuple().tm_yday
                
                # Seasonal temperature patterns
                temp_seasonal = 15 + 15 * np.sin(2 * np.pi * (day_of_year - 172) / 365)
                
                # Add random variations
                temp_min = temp_seasonal + random.uniform(-5, 0)
                temp_max = temp_seasonal + random.uniform(0, 5)
                
                # Precipitation (higher in spring/summer)
                precip_seasonal = 5 + 10 * np.sin(2 * np.pi * (day_of_year - 120) / 365)
                precipitation = max(0, precip_seasonal + random.uniform(-5, 5))
                
                # Humidity (higher with precipitation)
                humidity = 50 + 30 * (precipitation / 15) + random.uniform(-10, 10)
                humidity = max(0, min(100, humidity))
                
                # Wind speed
                wind_speed = random.uniform(0, 15)
                
                weather_data = WeatherData(
                    latitude=parcel.latitude,
                    longitude=parcel.longitude,
                    date=current_date,
                    temperature_min=temp_min,
                    temperature_max=temp_max,
                    precipitation=precipitation,
                    humidity=humidity,
                    wind_speed=wind_speed
                )
                db.session.add(weather_data)
                
                current_date += timedelta(days=1)
            
            db.session.commit()
            print(f"Generated weather data for Parcel {parcel.id}")
        
        print("Sample data generation complete")

# Main entry point
if __name__ == '__main__':
    # Generate sample data
    generate_sample_data()
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
