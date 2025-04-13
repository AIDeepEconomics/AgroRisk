"""
Visualization components for the AgroSmartRisk Time-Series Analysis module.
This module provides functions for creating interactive visualizations of time series risk data.
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def create_time_series_plot(dates, values, title="Risk Time Series", risk_type="overall"):
    """
    Create a time series line plot for risk data.
    
    Args:
        dates (list): List of date strings in ISO format
        values (list): List of risk values
        title (str): Plot title
        risk_type (str): Type of risk being visualized
    
    Returns:
        str: JSON string containing the plotly figure
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Create a DataFrame for plotting
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # Define color based on risk type
    color_map = {
        'drought': '#ff9800',  # Orange
        'flood': '#2196f3',    # Blue
        'frost': '#00bcd4',    # Cyan
        'pest': '#9c27b0',     # Purple
        'overall': '#f44336'   # Red
    }
    
    color = color_map.get(risk_type, '#f44336')
    
    # Create the figure
    fig = go.Figure()
    
    # Add the time series line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['value'],
        mode='lines+markers',
        name=f'{risk_type.capitalize()} Risk',
        line=dict(color=color, width=2),
        marker=dict(size=6, color=color)
    ))
    
    # Add risk level regions
    fig.add_hrect(
        y0=0.7, y1=1.0,
        fillcolor="red", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="High Risk",
        annotation_position="right"
    )
    
    fig.add_hrect(
        y0=0.3, y1=0.7,
        fillcolor="orange", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="Medium Risk",
        annotation_position="right"
    )
    
    fig.add_hrect(
        y0=0, y1=0.3,
        fillcolor="green", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="Low Risk",
        annotation_position="right"
    )
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Risk Level',
        yaxis=dict(
            range=[0, 1],
            tickvals=[0, 0.3, 0.7, 1],
            ticktext=['0', '0.3', '0.7', '1']
        ),
        hovermode='x unified',
        template='plotly_white',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Add range slider
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    
    # Convert to JSON
    return json.dumps(fig.to_dict())

def create_trend_analysis_plot(dates, values, moving_avg, trend_line, window_size=7, title="Risk Trend Analysis", risk_type="overall"):
    """
    Create a plot showing risk values with moving average and trend line.
    
    Args:
        dates (list): List of date strings in ISO format
        values (list): List of risk values
        moving_avg (list): List of moving average values
        trend_line (list): List of trend line values
        window_size (int): Size of the moving average window
        title (str): Plot title
        risk_type (str): Type of risk being visualized
    
    Returns:
        str: JSON string containing the plotly figure
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Create a DataFrame for plotting
    df = pd.DataFrame({
        'date': dates,
        'value': values,
        'moving_avg': moving_avg,
        'trend_line': trend_line
    })
    
    # Define color based on risk type
    color_map = {
        'drought': '#ff9800',  # Orange
        'flood': '#2196f3',    # Blue
        'frost': '#00bcd4',    # Cyan
        'pest': '#9c27b0',     # Purple
        'overall': '#f44336'   # Red
    }
    
    color = color_map.get(risk_type, '#f44336')
    
    # Create the figure
    fig = go.Figure()
    
    # Add the raw data
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['value'],
        mode='lines+markers',
        name=f'{risk_type.capitalize()} Risk',
        line=dict(color=color, width=1, dash='dot'),
        marker=dict(size=5, color=color),
        opacity=0.7
    ))
    
    # Add the moving average
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['moving_avg'],
        mode='lines',
        name=f'{window_size}-Day Moving Avg',
        line=dict(color=color, width=3)
    ))
    
    # Add the trend line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['trend_line'],
        mode='lines',
        name='Trend Line',
        line=dict(color='black', width=2, dash='dash')
    ))
    
    # Add risk level regions
    fig.add_hrect(
        y0=0.7, y1=1.0,
        fillcolor="red", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="High Risk",
        annotation_position="right"
    )
    
    fig.add_hrect(
        y0=0.3, y1=0.7,
        fillcolor="orange", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="Medium Risk",
        annotation_position="right"
    )
    
    fig.add_hrect(
        y0=0, y1=0.3,
        fillcolor="green", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="Low Risk",
        annotation_position="right"
    )
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Risk Level',
        yaxis=dict(
            range=[0, 1],
            tickvals=[0, 0.3, 0.7, 1],
            ticktext=['0', '0.3', '0.7', '1']
        ),
        hovermode='x unified',
        template='plotly_white',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Add range slider
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    
    # Convert to JSON
    return json.dumps(fig.to_dict())

def create_risk_comparison_plot(dates, risk_data, title="Risk Factors Comparison"):
    """
    Create a plot comparing different risk factors over time.
    
    Args:
        dates (list): List of date strings in ISO format
        risk_data (dict): Dictionary with risk types as keys and lists of values as values
        title (str): Plot title
    
    Returns:
        str: JSON string containing the plotly figure
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Create the figure
    fig = go.Figure()
    
    # Define colors for each risk type
    colors = {
        'drought': '#ff9800',  # Orange
        'flood': '#2196f3',    # Blue
        'frost': '#00bcd4',    # Cyan
        'pest': '#9c27b0',     # Purple
        'overall': '#f44336'   # Red
    }
    
    # Add traces for each risk type
    for risk_type, values in risk_data.items():
        if risk_type in colors:
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines',
                name=f'{risk_type.capitalize()} Risk',
                line=dict(color=colors[risk_type], width=2)
            ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Risk Level',
        yaxis=dict(
            range=[0, 1],
            tickvals=[0, 0.3, 0.7, 1],
            ticktext=['0', '0.3', '0.7', '1']
        ),
        hovermode='x unified',
        template='plotly_white',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Add range slider
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    
    # Convert to JSON
    return json.dumps(fig.to_dict())

def create_forecast_plot(historical_dates, historical_values, forecast_dates, forecast_values, title="Risk Forecast", risk_type="overall"):
    """
    Create a plot showing historical risk data and forecast.
    
    Args:
        historical_dates (list): List of historical date strings in ISO format
        historical_values (list): List of historical risk values
        forecast_dates (list): List of forecast date strings in ISO format
        forecast_values (list): List of forecast risk values
        title (str): Plot title
        risk_type (str): Type of risk being visualized
    
    Returns:
        str: JSON string containing the plotly figure
    """
    # Convert dates to datetime objects if they are strings
    if historical_dates and isinstance(historical_dates[0], str):
        historical_dates = [datetime.fromisoformat(d) for d in historical_dates]
    
    if forecast_dates and isinstance(forecast_dates[0], str):
        forecast_dates = [datetime.fromisoformat(d) for d in forecast_dates]
    
    # Define color based on risk type
    color_map = {
        'drought': '#ff9800',  # Orange
        'flood': '#2196f3',    # Blue
        'frost': '#00bcd4',    # Cyan
        'pest': '#9c27b0',     # Purple
        'overall': '#f44336'   # Red
    }
    
    color = color_map.get(risk_type, '#f44336')
    
    # Create the figure
    fig = go.Figure()
    
    # Add the historical data
    fig.add_trace(go.Scatter(
        x=historical_dates,
        y=historical_values,
        mode='lines+markers',
        name='Historical Data',
        line=dict(color=color, width=2),
        marker=dict(size=6, color=color)
    ))
    
    # Add the forecast data
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_values,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='black', width=2, dash='dash'),
        marker=dict(size=6, color='black', symbol='diamond')
    ))
    
    # Add a vertical line separating historical and forecast data
    if historical_dates and forecast_dates:
        fig.add_vline(
            x=historical_dates[-1],
            line_width=1,
            line_dash="dash",
            line_color="gray",
            annotation_text="Forecast Start",
            annotation_position="top right"
        )
    
    # Add risk level regions
    fig.add_hrect(
        y0=0.7, y1=1.0,
        fillcolor="red", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="High Risk",
        annotation_position="right"
    )
    
    fig.add_hrect(
        y0=0.3, y1=0.7,
        fillcolor="orange", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="Medium Risk",
        annotation_position="right"
    )
    
    fig.add_hrect(
        y0=0, y1=0.3,
        fillcolor="green", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="Low Risk",
        annotation_position="right"
    )
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Risk Level',
        yaxis=dict(
            range=[0, 1],
            tickvals=[0, 0.3, 0.7, 1],
            ticktext=['0', '0.3', '0.7', '1']
        ),
        hovermode='x unified',
        template='plotly_white',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Convert to JSON
    return json.dumps(fig.to_dict())

def create_seasonal_analysis_plot(months, monthly_values, seasons, seasonal_values, title="Seasonal Risk Analysis", risk_type="overall"):
    """
    Create plots showing monthly and seasonal risk patterns.
    
    Args:
        months (list): List of month names
        monthly_values (list): List of monthly average risk values
        seasons (list): List of season names
        seasonal_values (list): List of seasonal average risk values
        title (str): Plot title
        risk_type (str): Type of risk being visualized
    
    Returns:
        str: JSON string containing the plotly figure
    """
    # Define color based on risk type
    color_map = {
        'drought': '#ff9800',  # Orange
        'flood': '#2196f3',    # Blue
        'frost': '#00bcd4',    # Cyan
        'pest': '#9c27b0',     # Purple
        'overall': '#f44336'   # Red
    }
    
    color = color_map.get(risk_type, '#f44336')
    
    # Create subplots: 1 row, 2 columns
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Monthly Average Risk", "Seasonal Average Risk"),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Add monthly data
    fig.add_trace(
        go.Bar(
            x=months,
            y=monthly_values,
            name="Monthly Average",
            marker_color=color
        ),
        row=1, col=1
    )
    
    # Add seasonal data
    season_colors = {
        'Winter': '#00bcd4',  # Cyan
        'Spring': '#4caf50',  # Green
        'Summer': '#ff9800',  # Orange
        'Fall': '#795548'     # Brown
    }
    
    season_color_list = [season_colors.get(season, color) for season in seasons]
    
    fig.add_trace(
        go.Bar(
            x=seasons,
            y=seasonal_values,
            name="Seasonal Average",
            marker_color=season_color_list
        ),
        row=1, col=2
    )
    
    # Update layout
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=False
    )
    
    # Update y-axes
    fig.update_yaxes(
        title_text="Risk Level",
        range=[0, 1],
        tickvals=[0, 0.3, 0.7, 1],
        ticktext=['0', '0.3', '0.7', '1'],
        row=1, col=1
    )
    
    fig.update_yaxes(
        title_text="Risk Level",
        range=[0, 1],
        tickvals=[0, 0.3, 0.7, 1],
        ticktext=['0', '0.3', '0.7', '1'],
        row=1, col=2
    )
    
    # Convert to JSON
    return json.dumps(fig.to_dict())

def create_weather_correlation_plot(correlations, title="Weather Factor Correlation with Risk", risk_type="overall"):
    """
    Create a bar plot showing correlation between weather factors and risk.
    
    Args:
        correlations (dict): Dictionary with weather factors as keys and correlation values as values
        title (str): Plot title
        risk_type (str): Type of risk being visualized
    
    Returns:
        str: JSON string containing the plotly figure
    """
    # Prepare data
    factors = list(correlations.keys())
    values = list(correlations.values())
    
    # Create colors based on correlation values (positive = blue, negative = red)
    colors = ['#2196f3' if v >= 0 else '#f44336' for v in values]
    
    # Create the figure
    fig = go.Figure()
    
    # Add the bar chart
    fig.add_trace(go.Bar(
        x=factors,
        y=values,
        marker_color=colors,
        text=[f"{v:.2f}" for v in values],
        textposition='auto'
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Weather Factor',
        yaxis_title='Correlation Coefficient',
        yaxis=dict(
            range=[-1, 1],
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=['-1', '-0.5', '0', '0.5', '1']
        ),
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Add reference lines
    fig.add_hline(y=0, line_width=1, line_dash="solid", line_color="gray")
    fig.add_hline(y=0.7, line_width=1, line_dash="dash", line_color="green", annotation_text="Strong Positive", annotation_position="right")
    fig.add_hline(y=-0.7, line_width=1, line_dash="dash", line_color="red", annotation_text="Strong Negative", annotation_position="right")
    
    # Convert to JSON
    return json.dumps(fig.to_dict())

def create_risk_heatmap(dates, parcels, risk_values, title="Risk Heatmap", risk_type="overall"):
    """
    Create a heatmap showing risk levels across multiple parcels over time.
    
    Args:
        dates (list): List of date strings in ISO format
        parcels (list): List of parcel names or IDs
        risk_values (list): 2D list of risk values [parcel][date]
        title (str): Plot title
        risk_type (str): Type of risk being visualized
    
    Returns:
        str: JSON string containing the plotly figure
    """
    # Convert dates to datetime objects if they are strings
    if dates and isinstance(dates[0], str):
        dates = [datetime.fromisoformat(d) for d in dates]
    
    # Format dates for display
    date_strings = [d.strftime('%Y-%m-%d') for d in dates]
    
    # Create the figure
    fig = go.Figure(data=go.Heatmap(
        z=risk_values,
        x=date_strings,
        y=parcels,
        colorscale=[
            [0, 'green'],
            [0.3, 'yellow'],
            [0.7, 'orange'],
            [1, 'red']
        ],
        zmin=0,
        zmax=1,
        colorbar=dict(
            title="Risk Level",
            tickvals=[0, 0.3, 0.7, 1],
            ticktext=["Low", "Medium", "High", "Extreme"]
        )
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Parcel',
        template='plotly_white',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Convert to JSON
    return json.dumps(fig.to_dict())
