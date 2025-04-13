"""
API endpoints for the AgroSmartRisk Time-Series Analysis module.
This module provides Flask routes for accessing and analyzing time series risk data.
"""
from flask import Blueprint, request, jsonify
from database.models import db, Parcel, RiskData, RiskAnalysis, WeatherData
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import func

# Create a Blueprint for the risk time series API
risk_api = Blueprint('risk_api', __name__)

@risk_api.route('/parcels', methods=['GET'])
def get_parcels():
    """Get all parcels or filter by parameters"""
    parcels = Parcel.query.all()
    return jsonify({
        'success': True,
        'count': len(parcels),
        'data': [parcel.to_dict() for parcel in parcels]
    })

@risk_api.route('/parcels/<int:parcel_id>', methods=['GET'])
def get_parcel(parcel_id):
    """Get a specific parcel by ID"""
    parcel = Parcel.query.get_or_404(parcel_id)
    return jsonify({
        'success': True,
        'data': parcel.to_dict()
    })

@risk_api.route('/risk-data', methods=['GET'])
def get_risk_data():
    """Get risk data with optional filtering by parcel_id, date range, and risk type"""
    # Parse query parameters
    parcel_id = request.args.get('parcel_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    risk_type = request.args.get('risk_type')  # drought, flood, frost, pest, overall
    
    # Build query
    query = RiskData.query
    
    # Apply filters if provided
    if parcel_id:
        query = query.filter(RiskData.parcel_id == parcel_id)
    
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
    
    # Execute query
    risk_data = query.order_by(RiskData.date).all()
    
    # Filter by risk type if specified
    if risk_type and risk_type in ['drought', 'flood', 'frost', 'pest', 'overall']:
        result_data = []
        for data in risk_data:
            data_dict = data.to_dict()
            filtered_data = {
                'id': data_dict['id'],
                'parcel_id': data_dict['parcel_id'],
                'date': data_dict['date'],
                'risk_value': data_dict[f'{risk_type}_risk'] if risk_type != 'overall' else data_dict['overall_risk'],
                'risk_type': risk_type,
                'created_at': data_dict['created_at']
            }
            result_data.append(filtered_data)
    else:
        result_data = [data.to_dict() for data in risk_data]
    
    return jsonify({
        'success': True,
        'count': len(result_data),
        'data': result_data
    })

@risk_api.route('/risk-data/<int:parcel_id>/time-series', methods=['GET'])
def get_risk_time_series(parcel_id):
    """Get time series risk data for a specific parcel"""
    # Parse query parameters
    risk_type = request.args.get('risk_type', 'overall')  # Default to overall risk
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Validate parcel exists
    parcel = Parcel.query.get_or_404(parcel_id)
    
    # Build query
    query = RiskData.query.filter(RiskData.parcel_id == parcel_id)
    
    # Apply date filters if provided
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
    
    # Execute query
    risk_data = query.order_by(RiskData.date).all()
    
    # Prepare time series data
    dates = []
    values = []
    
    for data in risk_data:
        dates.append(data.date.isoformat())
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
    
    return jsonify({
        'success': True,
        'parcel': parcel.to_dict(),
        'risk_type': risk_type,
        'time_series': {
            'dates': dates,
            'values': values
        }
    })

@risk_api.route('/risk-data/trend-analysis', methods=['GET'])
def get_risk_trend_analysis():
    """Analyze trends in risk data over time"""
    # Parse query parameters
    parcel_id = request.args.get('parcel_id', type=int)
    risk_type = request.args.get('risk_type', 'overall')
    window = request.args.get('window', 7, type=int)  # Moving average window size
    
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
    
    # Create DataFrame for analysis
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Calculate moving average
    if len(df) >= window:
        df['moving_avg'] = df['value'].rolling(window=window).mean()
    else:
        df['moving_avg'] = df['value']
    
    # Calculate trend (simple linear regression)
    if len(df) > 1:
        x = np.arange(len(df))
        y = df['value'].values
        
        # Handle NaN values
        mask = ~np.isnan(y)
        if np.sum(mask) > 1:  # Need at least 2 non-NaN values
            x_valid = x[mask]
            y_valid = y[mask]
            
            # Calculate slope and intercept
            slope, intercept = np.polyfit(x_valid, y_valid, 1)
            
            # Calculate trend line
            trend_line = slope * x + intercept
            
            # Calculate if trend is increasing or decreasing
            trend_direction = "increasing" if slope > 0 else "decreasing"
            trend_strength = abs(slope)
            
            # Calculate R-squared
            y_pred = slope * x_valid + intercept
            ss_total = np.sum((y_valid - np.mean(y_valid)) ** 2)
            ss_residual = np.sum((y_valid - y_pred) ** 2)
            r_squared = 1 - (ss_residual / ss_total) if ss_total != 0 else 0
        else:
            trend_line = [None] * len(df)
            trend_direction = "insufficient data"
            trend_strength = 0
            r_squared = 0
    else:
        trend_line = [None] * len(df)
        trend_direction = "insufficient data"
        trend_strength = 0
        r_squared = 0
    
    # Prepare result
    result = {
        'success': True,
        'parcel': parcel.to_dict(),
        'risk_type': risk_type,
        'analysis': {
            'dates': [d.isoformat() for d in df['date']],
            'values': df['value'].tolist(),
            'moving_average': df['moving_avg'].tolist(),
            'trend_line': [float(v) if v is not None else None for v in trend_line],
            'trend_direction': trend_direction,
            'trend_strength': float(trend_strength),
            'r_squared': float(r_squared),
            'window_size': window
        }
    }
    
    # Store analysis result in database
    analysis = RiskAnalysis(
        parcel_id=parcel_id,
        analysis_type='trend',
        risk_type=risk_type,
        start_date=df['date'].min(),
        end_date=df['date'].max(),
        result_data=result['analysis']
    )
    db.session.add(analysis)
    db.session.commit()
    
    return jsonify(result)

@risk_api.route('/risk-data/comparison', methods=['GET'])
def compare_risk_factors():
    """Compare different risk factors for a parcel over time"""
    # Parse query parameters
    parcel_id = request.args.get('parcel_id', type=int)
    
    if not parcel_id:
        return jsonify({'success': False, 'error': 'parcel_id is required'}), 400
    
    # Validate parcel exists
    parcel = Parcel.query.get_or_404(parcel_id)
    
    # Get risk data for the parcel
    risk_data = RiskData.query.filter(RiskData.parcel_id == parcel_id).order_by(RiskData.date).all()
    
    if not risk_data:
        return jsonify({'success': False, 'error': 'No risk data available for this parcel'}), 404
    
    # Prepare data for comparison
    dates = []
    drought_values = []
    flood_values = []
    frost_values = []
    pest_values = []
    overall_values = []
    
    for data in risk_data:
        dates.append(data.date.isoformat())
        drought_values.append(data.drought_risk)
        flood_values.append(data.flood_risk)
        frost_values.append(data.frost_risk)
        pest_values.append(data.pest_risk)
        overall_values.append(data.overall_risk)
    
    # Calculate correlations between risk factors
    df = pd.DataFrame({
        'drought': drought_values,
        'flood': flood_values,
        'frost': frost_values,
        'pest': pest_values,
        'overall': overall_values
    })
    
    correlations = {}
    for col1 in df.columns:
        for col2 in df.columns:
            if col1 != col2:
                corr = df[col1].corr(df[col2])
                correlations[f"{col1}_vs_{col2}"] = float(corr) if not pd.isna(corr) else 0
    
    return jsonify({
        'success': True,
        'parcel': parcel.to_dict(),
        'comparison': {
            'dates': dates,
            'drought': drought_values,
            'flood': flood_values,
            'frost': frost_values,
            'pest': pest_values,
            'overall': overall_values
        },
        'correlations': correlations
    })

@risk_api.route('/risk-data/forecast', methods=['GET'])
def forecast_risk():
    """Forecast risk values for future dates"""
    # Parse query parameters
    parcel_id = request.args.get('parcel_id', type=int)
    risk_type = request.args.get('risk_type', 'overall')
    days = request.args.get('days', 7, type=int)  # Number of days to forecast
    
    if not parcel_id:
        return jsonify({'success': False, 'error': 'parcel_id is required'}), 400
    
    # Validate parcel exists
    parcel = Parcel.query.get_or_404(parcel_id)
    
    # Get risk data for the parcel
    risk_data = RiskData.query.filter(RiskData.parcel_id == parcel_id).order_by(RiskData.date).all()
    
    if not risk_data:
        return jsonify({'success': False, 'error': 'No risk data available for this parcel'}), 404
    
    # Prepare data for forecasting
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
    
    # Create DataFrame for forecasting
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Simple forecasting using linear regression
    if len(df) > 1:
        x = np.arange(len(df))
        y = df['value'].values
        
        # Handle NaN values
        mask = ~np.isnan(y)
        if np.sum(mask) > 1:  # Need at least 2 non-NaN values
            x_valid = x[mask]
            y_valid = y[mask]
            
            # Calculate slope and intercept
            slope, intercept = np.polyfit(x_valid, y_valid, 1)
            
            # Generate forecast dates
            last_date = df['date'].max()
            forecast_dates = [last_date + timedelta(days=i+1) for i in range(days)]
            
            # Generate forecast values
            forecast_x = np.arange(len(df), len(df) + days)
            forecast_values = slope * forecast_x + intercept
            
            # Ensure values are within 0-1 range
            forecast_values = np.clip(forecast_values, 0, 1)
        else:
            # If not enough valid data, use the last value for forecasting
            last_value = df['value'].iloc[-1] if not pd.isna(df['value'].iloc[-1]) else 0.5
            last_date = df['date'].max()
            forecast_dates = [last_date + timedelta(days=i+1) for i in range(days)]
            forecast_values = [last_value] * days
    else:
        # If not enough data, use a default value
        last_date = df['date'].max() if not df.empty else datetime.now().date()
        forecast_dates = [last_date + timedelta(days=i+1) for i in range(days)]
        forecast_values = [0.5] * days  # Default to medium risk
    
    # Prepare result
    result = {
        'success': True,
        'parcel': parcel.to_dict(),
        'risk_type': risk_type,
        'historical': {
            'dates': [d.isoformat() for d in dates],
            'values': values
        },
        'forecast': {
            'dates': [d.isoformat() for d in forecast_dates],
            'values': [float(v) for v in forecast_values]
        }
    }
    
    # Store forecast in database
    analysis = RiskAnalysis(
        parcel_id=parcel_id,
        analysis_type='forecast',
        risk_type=risk_type,
        start_date=forecast_dates[0],
        end_date=forecast_dates[-1],
        result_data=result['forecast']
    )
    db.session.add(analysis)
    db.session.commit()
    
    return jsonify(result)

@risk_api.route('/risk-data/seasonal-analysis', methods=['GET'])
def seasonal_risk_analysis():
    """Analyze seasonal patterns in risk data"""
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
    
    # Create DataFrame for analysis
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Add month and season columns
    df['month'] = df['date'].apply(lambda x: x.month)
    df['season'] = df['month'].apply(lambda m: 
        'Winter' if m in [12, 1, 2] else
        'Spring' if m in [3, 4, 5] else
        'Summer' if m in [6, 7, 8] else
        'Fall'
    )
    
    # Calculate monthly averages
    monthly_avg = df.groupby('month')['value'].mean().reset_index()
    monthly_avg['month_name'] = monthly_avg['month'].apply(lambda m: datetime(2000, m, 1).strftime('%B'))
    
    # Calculate seasonal averages
    seasonal_avg = df.groupby('season')['value'].mean().reset_index()
    
    # Order seasons correctly
    season_order = {'Winter': 0, 'Spring': 1, 'Summer': 2, 'Fall': 3}
    seasonal_avg['order'] = seasonal_avg['season'].map(season_order)
    seasonal_avg = seasonal_avg.sort_values('order').drop('order', axis=1)
    
    # Prepare result
    result = {
        'success': True,
        'parcel': parcel.to_dict(),
        'risk_type': risk_type,
        'monthly_analysis': {
            'months': monthly_avg['month_name'].tolist(),
            'values': monthly_avg['value'].tolist()
        },
        'seasonal_analysis': {
            'seasons': seasonal_avg['season'].tolist(),
            'values': seasonal_avg['value'].tolist()
        }
    }
    
    # Store analysis result in database
    analysis = RiskAnalysis(
        parcel_id=parcel_id,
        analysis_type='seasonal',
        risk_type=risk_type,
        start_date=df['date'].min(),
        end_date=df['date'].max(),
        result_data={
            'monthly': result['monthly_analysis'],
            'seasonal': result['seasonal_analysis']
        }
    )
    db.session.add(analysis)
    db.session.commit()
    
    return jsonify(result)

@risk_api.route('/weather-data', methods=['GET'])
def get_weather_data():
    """Get weather data with optional filtering"""
    # Parse query parameters
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query
    query = WeatherData.query
    
    # Apply filters if provided
    if latitude and longitude:
        query = query.filter(
            WeatherData.latitude == latitude,
            WeatherData.longitude == longitude
        )
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(WeatherData.date >= start_date)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(WeatherData.date <= end_date)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    # Execute query
    weather_data = query.order_by(WeatherData.date).all()
    
    return jsonify({
        'success': True,
        'count': len(weather_data),
        'data': [data.to_dict() for data in weather_data]
    })

@risk_api.route('/risk-data/weather-correlation', methods=['GET'])
def analyze_weather_correlation():
    """Analyze correlation between weather data and risk factors"""
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
    
    # Get weather data for the parcel's location
    weather_data = WeatherData.query.filter(
        WeatherData.latitude == parcel.latitude,
        WeatherData.longitude == parcel.longitude
    ).order_by(WeatherData.date).all()
    
    if not weather_data:
        return jsonify({'success': False, 'error': 'No weather data available for this parcel location'}), 404
    
    # Prepare data for correlation analysis
    risk_df = pd.DataFrame([
        {
            'date': data.date,
            'risk_value': getattr(data, f'{risk_type}_risk') if risk_type != 'overall' else data.overall_risk
        }
        for data in risk_data
    ])
    
    weather_df = pd.DataFrame([
        {
            'date': data.date,
            'temp_min': data.temperature_min,
            'temp_max': data.temperature_max,
            'precipitation': data.precipitation,
            'humidity': data.humidity,
            'wind_speed': data.wind_speed
        }
        for data in weather_data
    ])
    
    # Merge dataframes on date
    merged_df = pd.merge(risk_df, weather_df, on='date', how='inner')
    
    if merged_df.empty:
        return jsonify({'success': False, 'error': 'No matching dates between risk and weather data'}), 404
    
    # Calculate correlations
    correlations = {}
    for weather_factor in ['temp_min', 'temp_max', 'precipitation', 'humidity', 'wind_speed']:
        corr = merged_df['risk_value'].corr(merged_df[weather_factor])
        correlations[weather_factor] = float(corr) if not pd.isna(corr) else 0
    
    # Find the most influential weather factor
    most_influential = max(correlations.items(), key=lambda x: abs(x[1]))
    
    return jsonify({
        'success': True,
        'parcel': parcel.to_dict(),
        'risk_type': risk_type,
        'correlations': correlations,
        'most_influential_factor': {
            'factor': most_influential[0],
            'correlation': most_influential[1]
        },
        'data_points': len(merged_df)
    })
