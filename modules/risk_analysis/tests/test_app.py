"""
Test script for the AgroSmartRisk Time-Series Analysis proof-of-concept.
This script tests the functionality of the application components.
"""
import os
import sys
import unittest
import json
import tempfile
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import application modules
from app import app, db, generate_sample_data
from database.models import Parcel, RiskData, WeatherData
from backend.trend_analysis import (
    analyze_trend, detect_change_points, perform_seasonal_decomposition,
    test_stationarity, forecast_arima, analyze_risk_patterns, calculate_risk_volatility
)

class AgroSmartRiskTestCase(unittest.TestCase):
    """Test case for the AgroSmartRisk application"""
    
    def setUp(self):
        """Set up test environment"""
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        # Create test client
        self.client = app.test_client()
        
        # Create database tables and generate sample data
        with app.app_context():
            db.create_all()
            generate_sample_data()
    
    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_index_route(self):
        """Test the index route"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_api_parcels(self):
        """Test the parcels API endpoint"""
        response = self.client.get('/api/parcels')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['data']), 0)
    
    def test_api_risk_data(self):
        """Test the risk data API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test risk data endpoint
        response = self.client.get(f'/api/risk-data/{parcel_id}')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertGreater(len(data['data']), 0)
    
    def test_api_time_series(self):
        """Test the time series API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test time series endpoint
        response = self.client.get(f'/api/risk-data/{parcel_id}/time-series')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertGreater(len(data['time_series']['dates']), 0)
        self.assertEqual(len(data['time_series']['dates']), len(data['time_series']['values']))
    
    def test_api_trend_analysis(self):
        """Test the trend analysis API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test trend analysis endpoint
        response = self.client.get(f'/api/risk-data/trend-analysis?parcel_id={parcel_id}&risk_type=overall&window=7')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertIn('trend_direction', data['analysis'])
        self.assertIn('trend_strength', data['analysis'])
        self.assertIn('r_squared', data['analysis'])
    
    def test_api_comparison(self):
        """Test the risk comparison API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test comparison endpoint
        response = self.client.get(f'/api/risk-data/comparison?parcel_id={parcel_id}')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertIn('drought', data['comparison'])
        self.assertIn('flood', data['comparison'])
        self.assertIn('frost', data['comparison'])
        self.assertIn('pest', data['comparison'])
        self.assertIn('overall', data['comparison'])
    
    def test_api_forecast(self):
        """Test the forecast API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test forecast endpoint
        response = self.client.get(f'/api/risk-data/forecast?parcel_id={parcel_id}&risk_type=overall&days=7')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertIn('historical', data)
        self.assertIn('forecast', data)
        self.assertEqual(len(data['forecast']['dates']), 7)
    
    def test_api_seasonal_analysis(self):
        """Test the seasonal analysis API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test seasonal analysis endpoint
        response = self.client.get(f'/api/risk-data/seasonal-analysis?parcel_id={parcel_id}&risk_type=overall')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertIn('monthly_analysis', data)
        self.assertIn('seasonal_analysis', data)
    
    def test_api_weather_correlation(self):
        """Test the weather correlation API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test weather correlation endpoint
        response = self.client.get(f'/api/risk-data/weather-correlation?parcel_id={parcel_id}&risk_type=overall')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertIn('correlations', data)
        self.assertIn('most_influential_factor', data)
    
    def test_api_change_points(self):
        """Test the change points API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test change points endpoint
        response = self.client.get(f'/api/risk-data/change-points?parcel_id={parcel_id}&risk_type=overall&window=7')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertIn('change_points', data)
    
    def test_api_seasonal_decomposition(self):
        """Test the seasonal decomposition API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test seasonal decomposition endpoint
        response = self.client.get(f'/api/risk-data/seasonal-decomposition?parcel_id={parcel_id}&risk_type=overall&period=30')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertIn('decomposition', data)
    
    def test_api_stationarity(self):
        """Test the stationarity API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test stationarity endpoint
        response = self.client.get(f'/api/risk-data/stationarity?parcel_id={parcel_id}&risk_type=overall')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertIn('stationarity', data)
    
    def test_api_arima_forecast(self):
        """Test the ARIMA forecast API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test ARIMA forecast endpoint
        response = self.client.get(f'/api/risk-data/arima-forecast?parcel_id={parcel_id}&risk_type=overall&days=7')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertIn('forecast', data)
    
    def test_api_risk_patterns(self):
        """Test the risk patterns API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test risk patterns endpoint
        response = self.client.get(f'/api/risk-data/risk-patterns?parcel_id={parcel_id}&risk_type=overall&threshold=0.7')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertIn('patterns', data)
    
    def test_api_volatility(self):
        """Test the volatility API endpoint"""
        # Get a parcel ID
        with app.app_context():
            parcel = Parcel.query.first()
            parcel_id = parcel.id
        
        # Test volatility endpoint
        response = self.client.get(f'/api/risk-data/volatility?parcel_id={parcel_id}&risk_type=overall&window=7')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel_id)
        self.assertIn('volatility', data)
    
    def test_trend_analysis_module(self):
        """Test the trend analysis module functions"""
        # Create sample data
        dates = [datetime.now() - timedelta(days=i) for i in range(100, 0, -1)]
        values = [0.5 + 0.003 * i + 0.1 * (i % 7) / 7 for i in range(100)]
        
        # Test analyze_trend function
        trend_result = analyze_trend(dates, values, window_size=7)
        self.assertIn('trend_direction', trend_result)
        self.assertIn('trend_strength', trend_result)
        self.assertIn('r_squared', trend_result)
        
        # Test detect_change_points function
        change_points_result = detect_change_points(dates, values, window_size=7)
        self.assertIn('change_points', change_points_result)
        
        # Test perform_seasonal_decomposition function
        seasonal_result = perform_seasonal_decomposition(dates, values, period=7)
        self.assertIn('success', seasonal_result)
        
        # Test test_stationarity function
        stationarity_result = test_stationarity(dates, values)
        self.assertIn('is_stationary', stationarity_result)
        
        # Test forecast_arima function
        forecast_result = forecast_arima(dates, values, forecast_days=7)
        self.assertIn('forecast_values', forecast_result)
        self.assertEqual(len(forecast_result['forecast_values']), 7)
        
        # Test analyze_risk_patterns function
        patterns_result = analyze_risk_patterns(dates, values, threshold=0.7)
        self.assertIn('high_risk_periods', patterns_result)
        
        # Test calculate_risk_volatility function
        volatility_result = calculate_risk_volatility(dates, values, window_size=7)
        self.assertIn('volatility', volatility_result)

if __name__ == '__main__':
    unittest.main()
