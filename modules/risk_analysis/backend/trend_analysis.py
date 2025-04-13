"""
Trend analysis module for the AgroSmartRisk Time-Series Analysis.
This module provides functions for analyzing trends in time series risk data.
"""
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def analyze_trend(dates, values, window_size=7):
    """
    Analyze trend in time series data.
    
    Args:
        dates (list): List of date strings in ISO format
        values (list): List of risk values
        window_size (int): Size of the moving average window
    
    Returns:
        dict: Dictionary containing trend analysis results
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Create a DataFrame for analysis
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Calculate moving average
    if len(df) >= window_size:
        df['moving_avg'] = df['value'].rolling(window=window_size).mean()
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
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_valid, y_valid)
            
            # Calculate trend line
            trend_line = slope * x + intercept
            
            # Calculate if trend is increasing or decreasing
            trend_direction = "increasing" if slope > 0 else "decreasing"
            trend_strength = abs(slope)
            
            # Calculate R-squared
            r_squared = r_value ** 2
            
            # Calculate statistical significance
            is_significant = p_value < 0.05
        else:
            trend_line = [None] * len(df)
            trend_direction = "insufficient data"
            trend_strength = 0
            r_squared = 0
            p_value = 1
            is_significant = False
    else:
        trend_line = [None] * len(df)
        trend_direction = "insufficient data"
        trend_strength = 0
        r_squared = 0
        p_value = 1
        is_significant = False
    
    # Prepare result
    result = {
        'dates': [d.isoformat() for d in df['date']],
        'values': df['value'].tolist(),
        'moving_average': df['moving_avg'].tolist(),
        'trend_line': [float(v) if v is not None else None for v in trend_line],
        'trend_direction': trend_direction,
        'trend_strength': float(trend_strength),
        'r_squared': float(r_squared),
        'p_value': float(p_value) if isinstance(p_value, (int, float)) else 1.0,
        'is_significant': bool(is_significant),
        'window_size': window_size
    }
    
    return result

def detect_change_points(dates, values, window_size=7):
    """
    Detect change points in time series data.
    
    Args:
        dates (list): List of date strings in ISO format
        values (list): List of risk values
        window_size (int): Size of the window for change point detection
    
    Returns:
        dict: Dictionary containing change point detection results
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Create a DataFrame for analysis
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Need at least 2*window_size data points for meaningful change point detection
    if len(df) < 2 * window_size:
        return {
            'dates': [d.isoformat() for d in df['date']],
            'values': df['value'].tolist(),
            'change_points': [],
            'change_magnitudes': [],
            'window_size': window_size
        }
    
    # Calculate rolling mean and standard deviation
    df['rolling_mean'] = df['value'].rolling(window=window_size).mean()
    df['rolling_std'] = df['value'].rolling(window=window_size).std()
    
    # Skip the first window_size rows (NaN values)
    df_valid = df.dropna()
    
    # Calculate z-scores for each point
    df_valid['z_score'] = (df_valid['value'] - df_valid['rolling_mean']) / df_valid['rolling_std']
    
    # Identify change points (points with absolute z-score > 2)
    change_points = []
    change_magnitudes = []
    
    for i in range(window_size, len(df)):
        if i < len(df) and not pd.isna(df.loc[i, 'value']):
            if i < len(df_valid) and abs(df_valid.iloc[i - window_size]['z_score']) > 2:
                change_points.append(df.loc[i, 'date'].isoformat())
                change_magnitudes.append(float(df_valid.iloc[i - window_size]['z_score']))
    
    # Prepare result
    result = {
        'dates': [d.isoformat() for d in df['date']],
        'values': df['value'].tolist(),
        'change_points': change_points,
        'change_magnitudes': change_magnitudes,
        'window_size': window_size
    }
    
    return result

def perform_seasonal_decomposition(dates, values, period=30):
    """
    Perform seasonal decomposition of time series data.
    
    Args:
        dates (list): List of date strings in ISO format
        values (list): List of risk values
        period (int): Period for seasonal decomposition (e.g., 7 for weekly, 30 for monthly)
    
    Returns:
        dict: Dictionary containing seasonal decomposition results
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Create a DataFrame for analysis
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Need at least 2*period data points for meaningful seasonal decomposition
    if len(df) < 2 * period:
        return {
            'dates': [d.isoformat() for d in df['date']],
            'values': df['value'].tolist(),
            'trend': [],
            'seasonal': [],
            'residual': [],
            'period': period,
            'success': False,
            'message': f"Insufficient data for seasonal decomposition. Need at least {2 * period} data points."
        }
    
    # Set date as index
    df = df.set_index('date')
    
    try:
        # Perform seasonal decomposition
        result = seasonal_decompose(df['value'], model='additive', period=period)
        
        # Get components
        trend = result.trend
        seasonal = result.seasonal
        residual = result.resid
        
        # Handle NaN values
        trend = trend.fillna(method='bfill').fillna(method='ffill')
        seasonal = seasonal.fillna(method='bfill').fillna(method='ffill')
        residual = residual.fillna(method='bfill').fillna(method='ffill')
        
        # Prepare result
        decomposition_result = {
            'dates': [d.isoformat() for d in dates],
            'values': df['value'].tolist(),
            'trend': trend.tolist(),
            'seasonal': seasonal.tolist(),
            'residual': residual.tolist(),
            'period': period,
            'success': True,
            'message': "Seasonal decomposition successful."
        }
        
        return decomposition_result
    
    except Exception as e:
        # Return error message if decomposition fails
        return {
            'dates': [d.isoformat() for d in dates],
            'values': df['value'].tolist(),
            'trend': [],
            'seasonal': [],
            'residual': [],
            'period': period,
            'success': False,
            'message': f"Seasonal decomposition failed: {str(e)}"
        }

def test_stationarity(dates, values):
    """
    Test stationarity of time series data using Augmented Dickey-Fuller test.
    
    Args:
        dates (list): List of date strings in ISO format
        values (list): List of risk values
    
    Returns:
        dict: Dictionary containing stationarity test results
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Create a DataFrame for analysis
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Need at least 20 data points for meaningful stationarity test
    if len(df) < 20:
        return {
            'is_stationary': False,
            'p_value': 1.0,
            'critical_values': {},
            'success': False,
            'message': "Insufficient data for stationarity test. Need at least 20 data points."
        }
    
    try:
        # Perform Augmented Dickey-Fuller test
        result = adfuller(df['value'].dropna())
        
        # Extract results
        adf_statistic = result[0]
        p_value = result[1]
        critical_values = result[4]
        
        # Determine if the series is stationary
        is_stationary = p_value < 0.05
        
        # Prepare result
        stationarity_result = {
            'is_stationary': is_stationary,
            'adf_statistic': float(adf_statistic),
            'p_value': float(p_value),
            'critical_values': {k: float(v) for k, v in critical_values.items()},
            'success': True,
            'message': "Stationarity test successful."
        }
        
        return stationarity_result
    
    except Exception as e:
        # Return error message if test fails
        return {
            'is_stationary': False,
            'p_value': 1.0,
            'critical_values': {},
            'success': False,
            'message': f"Stationarity test failed: {str(e)}"
        }

def forecast_arima(dates, values, forecast_days=7):
    """
    Forecast time series data using ARIMA model.
    
    Args:
        dates (list): List of date strings in ISO format
        values (list): List of risk values
        forecast_days (int): Number of days to forecast
    
    Returns:
        dict: Dictionary containing forecast results
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Create a DataFrame for analysis
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Need at least 30 data points for meaningful ARIMA forecast
    if len(df) < 30:
        # Fall back to simple linear regression for small datasets
        return forecast_linear(dates, values, forecast_days)
    
    try:
        # Set date as index
        df = df.set_index('date')
        
        # Check stationarity
        stationarity_result = test_stationarity(dates, values)
        
        # Determine ARIMA parameters
        # If stationary, use (1,0,1), otherwise use (1,1,1)
        d = 0 if stationarity_result.get('is_stationary', False) else 1
        
        # Fit ARIMA model
        model = ARIMA(df['value'], order=(1, d, 1))
        model_fit = model.fit()
        
        # Generate forecast dates
        last_date = dates[-1]
        forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
        
        # Generate forecast
        forecast = model_fit.forecast(steps=forecast_days)
        
        # Ensure values are within 0-1 range
        forecast_values = np.clip(forecast, 0, 1)
        
        # Calculate confidence intervals
        conf_int = model_fit.get_forecast(steps=forecast_days).conf_int()
        lower_bound = np.clip(conf_int.iloc[:, 0], 0, 1)
        upper_bound = np.clip(conf_int.iloc[:, 1], 0, 1)
        
        # Prepare result
        forecast_result = {
            'historical_dates': [d.isoformat() for d in dates],
            'historical_values': values,
            'forecast_dates': [d.isoformat() for d in forecast_dates],
            'forecast_values': forecast_values.tolist(),
            'lower_bound': lower_bound.tolist(),
            'upper_bound': upper_bound.tolist(),
            'model': 'ARIMA',
            'parameters': {
                'p': 1,
                'd': d,
                'q': 1
            },
            'success': True,
            'message': "ARIMA forecast successful."
        }
        
        return forecast_result
    
    except Exception as e:
        # Fall back to linear regression if ARIMA fails
        print(f"ARIMA forecast failed: {str(e)}. Falling back to linear regression.")
        return forecast_linear(dates, values, forecast_days)

def forecast_linear(dates, values, forecast_days=7):
    """
    Forecast time series data using linear regression.
    
    Args:
        dates (list): List of date strings in ISO format
        values (list): List of risk values
        forecast_days (int): Number of days to forecast
    
    Returns:
        dict: Dictionary containing forecast results
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Create a DataFrame for analysis
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
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_valid, y_valid)
            
            # Generate forecast dates
            last_date = df['date'].max()
            forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
            
            # Generate forecast values
            forecast_x = np.arange(len(df), len(df) + forecast_days)
            forecast_values = slope * forecast_x + intercept
            
            # Calculate prediction intervals (approximate)
            # Using standard error of the regression for simplicity
            prediction_error = np.sqrt(np.sum((y_valid - (slope * x_valid + intercept))**2) / (len(x_valid) - 2))
            lower_bound = forecast_values - 1.96 * prediction_error
            upper_bound = forecast_values + 1.96 * prediction_error
            
            # Ensure values are within 0-1 range
            forecast_values = np.clip(forecast_values, 0, 1)
            lower_bound = np.clip(lower_bound, 0, 1)
            upper_bound = np.clip(upper_bound, 0, 1)
        else:
            # If not enough valid data, use the last value for forecasting
            last_value = df['value'].iloc[-1] if not pd.isna(df['value'].iloc[-1]) else 0.5
            last_date = df['date'].max()
            forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
            forecast_values = np.array([last_value] * forecast_days)
            lower_bound = np.array([max(0, last_value - 0.1)] * forecast_days)
            upper_bound = np.array([min(1, last_value + 0.1)] * forecast_days)
    else:
        # If not enough data, use a default value
        last_date = df['date'].max() if not df.empty else datetime.now().date()
        forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
        forecast_values = np.array([0.5] * forecast_days)  # Default to medium risk
        lower_bound = np.array([0.4] * forecast_days)
        upper_bound = np.array([0.6] * forecast_days)
    
    # Prepare result
    forecast_result = {
        'historical_dates': [d.isoformat() for d in dates],
        'historical_values': values,
        'forecast_dates': [d.isoformat() for d in forecast_dates],
        'forecast_values': forecast_values.tolist(),
        'lower_bound': lower_bound.tolist(),
        'upper_bound': upper_bound.tolist(),
        'model': 'Linear Regression',
        'parameters': {},
        'success': True,
        'message': "Linear regression forecast successful."
    }
    
    return forecast_result

def analyze_risk_patterns(dates, values, threshold=0.7):
    """
    Analyze patterns in risk data, identifying high-risk periods.
    
    Args:
        dates (list): List of date strings in ISO format
        values (list): List of risk values
        threshold (float): Threshold for high risk (default: 0.7)
    
    Returns:
        dict: Dictionary containing risk pattern analysis results
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Create a DataFrame for analysis
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Identify high-risk periods
    high_risk = df['value'] >= threshold
    
    # Find consecutive high-risk periods
    high_risk_periods = []
    current_period = None
    
    for i, (date, is_high_risk) in enumerate(zip(df['date'], high_risk)):
        if is_high_risk:
            if current_period is None:
                current_period = {'start_date': date, 'start_index': i, 'values': [df['value'].iloc[i]]}
            else:
                current_period['values'].append(df['value'].iloc[i])
        elif current_period is not None:
            current_period['end_date'] = df['date'].iloc[i-1]
            current_period['end_index'] = i-1
            current_period['duration'] = (current_period['end_date'] - current_period['start_date']).days + 1
            current_period['max_value'] = max(current_period['values'])
            current_period['avg_value'] = sum(current_period['values']) / len(current_period['values'])
            high_risk_periods.append(current_period)
            current_period = None
    
    # Handle case where the last period extends to the end of the data
    if current_period is not None:
        current_period['end_date'] = df['date'].iloc[-1]
        current_period['end_index'] = len(df) - 1
        current_period['duration'] = (current_period['end_date'] - current_period['start_date']).days + 1
        current_period['max_value'] = max(current_period['values'])
        current_period['avg_value'] = sum(current_period['values']) / len(current_period['values'])
        high_risk_periods.append(current_period)
    
    # Calculate summary statistics
    total_high_risk_days = sum(high_risk)
    percentage_high_risk = (total_high_risk_days / len(df)) * 100 if len(df) > 0 else 0
    
    # Format periods for JSON serialization
    formatted_periods = []
    for period in high_risk_periods:
        formatted_periods.append({
            'start_date': period['start_date'].isoformat(),
            'end_date': period['end_date'].isoformat(),
            'duration': period['duration'],
            'max_value': float(period['max_value']),
            'avg_value': float(period['avg_value'])
        })
    
    # Prepare result
    result = {
        'total_days': len(df),
        'high_risk_days': int(total_high_risk_days),
        'percentage_high_risk': float(percentage_high_risk),
        'high_risk_periods': formatted_periods,
        'threshold': threshold
    }
    
    return result

def calculate_risk_volatility(dates, values, window_size=7):
    """
    Calculate volatility (standard deviation) of risk values over time.
    
    Args:
        dates (list): List of date strings in ISO format
        values (list): List of risk values
        window_size (int): Size of the rolling window for volatility calculation
    
    Returns:
        dict: Dictionary containing volatility analysis results
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Create a DataFrame for analysis
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Calculate rolling standard deviation (volatility)
    df['volatility'] = df['value'].rolling(window=window_size).std()
    
    # Calculate overall volatility
    overall_volatility = df['value'].std()
    
    # Identify periods of high volatility (> 1.5 times the overall volatility)
    high_volatility_threshold = overall_volatility * 1.5
    high_volatility = df['volatility'] > high_volatility_threshold
    
    # Find consecutive high-volatility periods
    high_volatility_periods = []
    current_period = None
    
    for i, (date, is_high_vol) in enumerate(zip(df['date'][window_size-1:], high_volatility[window_size-1:])):
        idx = i + window_size - 1  # Adjust index to account for rolling window
        if is_high_vol:
            if current_period is None:
                current_period = {'start_date': date, 'start_index': idx, 'values': [df['volatility'].iloc[idx]]}
            else:
                current_period['values'].append(df['volatility'].iloc[idx])
        elif current_period is not None:
            current_period['end_date'] = df['date'].iloc[idx-1]
            current_period['end_index'] = idx-1
            current_period['duration'] = (current_period['end_date'] - current_period['start_date']).days + 1
            current_period['max_value'] = max(current_period['values'])
            current_period['avg_value'] = sum(current_period['values']) / len(current_period['values'])
            high_volatility_periods.append(current_period)
            current_period = None
    
    # Handle case where the last period extends to the end of the data
    if current_period is not None:
        current_period['end_date'] = df['date'].iloc[-1]
        current_period['end_index'] = len(df) - 1
        current_period['duration'] = (current_period['end_date'] - current_period['start_date']).days + 1
        current_period['max_value'] = max(current_period['values'])
        current_period['avg_value'] = sum(current_period['values']) / len(current_period['values'])
        high_volatility_periods.append(current_period)
    
    # Format periods for JSON serialization
    formatted_periods = []
    for period in high_volatility_periods:
        formatted_periods.append({
            'start_date': period['start_date'].isoformat(),
            'end_date': period['end_date'].isoformat(),
            'duration': period['duration'],
            'max_value': float(period['max_value']),
            'avg_value': float(period['avg_value'])
        })
    
    # Prepare result
    result = {
        'dates': [d.isoformat() for d in df['date']],
        'values': df['value'].tolist(),
        'volatility': df['volatility'].fillna(0).tolist(),
        'overall_volatility': float(overall_volatility),
        'high_volatility_threshold': float(high_volatility_threshold),
        'high_volatility_periods': formatted_periods,
        'window_size': window_size
    }
    
    return result
