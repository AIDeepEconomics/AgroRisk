# data/data_generation.py - Versión mejorada
import os
import random
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from datetime import datetime, timedelta
import pyproj
from functools import partial
from shapely.ops import transform
import csv

def calculate_area_in_hectares(polygon, lat_center):
    """
    Calculate the area of a polygon in hectares
    polygon: shapely Polygon object
    lat_center: approximate latitude of the center point for projection
    """
    # Create a suitable projection for the area (UTM zone based on latitude)
    project = pyproj.Transformer.from_crs(
        'EPSG:4326',  # WGS84
        'EPSG:32721', # UTM zone 21S
        always_xy=True
    ).transform
    
    # Apply the projection to the polygon
    polygon_utm = transform(project, polygon)
    
    # Calculate area in square meters and convert to hectares
    area_m2 = polygon_utm.area
    area_ha = area_m2 / 10000  # 1 hectare = 10,000 m²
    
    return round(area_ha, 2)  # Round to 2 decimal places

def generate_parcels(n=7):
    """
    Generate sample parcels with irregular shapes
    n: number of parcels to generate
    """
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

def generate_climate_data(parcels_gdf, days=30):
    """
    Generate climate risk data for each parcel and day with improved risk calculation methodology
    parcels_gdf: GeoDataFrame containing parcel information
    days: number of days to generate data for
    """
    climate_data = []
    base_date = datetime.strptime('2025-01-15', '%Y-%m-%d')
    
    # Define impact severity factors for different crops and risk types
    impact_factors = {
        'Soja': {
            'drought': 0.40,  # 40% yield loss if drought occurs
            'flood': 0.70,    # 70% yield loss if flood occurs
            'pest': 0.25      # 25% yield loss if pest outbreak occurs
        },
        'Maiz': {
            'drought': 0.35,  # 35% yield loss if drought occurs
            'flood': 0.60,    # 60% yield loss if flood occurs
            'pest': 0.20      # 20% yield loss if pest outbreak occurs
        }
    }
    
    # Default impact factors if crop not in the dictionary
    default_impacts = {'drought': 0.40, 'flood': 0.60, 'pest': 0.25}
    
    # Administrative and operational cost factors for premium calculation
    admin_expense_factor = 0.15  # 15% for administrative expenses
    profit_margin_factor = 0.10  # 10% profit margin
    reinsurance_factor = 0.05    # 5% for reinsurance costs
    loading_factor = 1 + admin_expense_factor + profit_margin_factor + reinsurance_factor
    
    # Base crop values per hectare (USD)
    crop_values = {
        'Soja': 1200,  # $1,200 per hectare
        'Maiz': 1500   # $1,500 per hectare
    }
    default_value = 1000  # Default value if crop not specified
    
    for i, parcel in parcels_gdf.iterrows():
        # Base risk from parcel properties or random if not present
        base_risk = parcel.get('base_risk', random.uniform(0.1, 0.5))
        crop_type = parcel.get('crop', 'Soja')
        
        # Get crop-specific impact factors and value
        crop_impacts = impact_factors.get(crop_type, default_impacts)
        crop_value = crop_values.get(crop_type, default_value)
        
        # Risk tends to increase over time
        for day in range(days):
            date = base_date + timedelta(days=day)
            
            # General trend is increasing risk, but with periodic variations
            day_phase = (day % 7) / 7.0  # Weekly cycle
            season_phase = (day % 30) / 30.0  # Monthly cycle
            
            # Generate probability values with trends
            drought_prob = (0.2 + day * 0.01 + 0.1 * np.sin(day_phase * 2 * np.pi))
            flood_prob = (0.3 - day * 0.005 + 0.15 * np.sin(season_phase * 2 * np.pi))
            pest_prob = (0.1 + day * 0.003 + 0.05 * np.sin((day_phase + 0.5) * 2 * np.pi))
            
            # Add some randomness
            drought_prob = max(0.01, min(0.95, drought_prob + random.uniform(-0.1, 0.1)))
            flood_prob = max(0.01, min(0.95, flood_prob + random.uniform(-0.1, 0.1)))
            pest_prob = max(0.01, min(0.95, pest_prob + random.uniform(-0.05, 0.05)))
            
            # Implement strong negative correlation between drought and flood
            if drought_prob > 0.5:
                flood_prob = random.uniform(0.01, 0.05)
            elif flood_prob > 0.5:
                drought_prob = random.uniform(0.01, 0.05)
            
            # Combine with base risk
            drought_prob = (0.7 * drought_prob + 0.3 * base_risk)
            flood_prob = (0.7 * flood_prob + 0.3 * base_risk)
            pest_prob = (0.7 * pest_prob + 0.3 * base_risk)
            
            # Convert to percentage for storage (0-100)
            drought_probability = round(drought_prob * 100)
            flood_probability = round(flood_prob * 100)
            hail_probability = round(pest_prob * 100)  # "hail" in column name but used for pest risk
            
            # Calculate expected losses (risk) for each hazard
            drought_risk = drought_prob * crop_impacts['drought']
            flood_risk = flood_prob * crop_impacts['flood']
            pest_risk = pest_prob * crop_impacts['pest']
            
            # Calculate total risk using loss expectancy approach
            # This is the probability-weighted average of potential losses
            total_risk = drought_risk + flood_risk + pest_risk
            
            # For backward compatibility, store in general_risk as percentage
            general_risk = round(total_risk * 100)
            
            # Calculate premium using actuarial principles
            pure_premium = total_risk * crop_value  # Pure risk premium
            loaded_premium = pure_premium * loading_factor  # Add loading factors
            premium_ha = round(loaded_premium, 2)  # Premium per hectare
            
            # Risk category determination based on total risk
            risk_category = get_risk_category(total_risk)
            
            # Store individual risk levels (probabilities) for backward compatibility
            drought_risk_level = drought_prob
            flood_risk_level = flood_prob
            pest_risk_level = pest_prob
            
            # Combined risk level for map rendering (keep as value between 0-1)
            # Using maximum approach for visualization intensity
            risk_level = max(drought_risk, flood_risk, pest_risk)
            
            # Create record with all required fields
            record = {
                'parcel_id': parcel['id'],
                'date': date.strftime('%Y-%m-%d'),
                'drought_probability': drought_probability,
                'flood_probability': flood_probability,
                'hail_probability': hail_probability,
                'general_risk': general_risk,
                'alert': None,  # Will be populated if thresholds exceeded
                'alert_type': None,  # Will be populated if thresholds exceeded
                'risk_level': risk_level,  # For map rendering (normalized 0-1)
                'drought_risk_level': drought_risk_level,  # Keep for backward compatibility
                'flood_risk_level': flood_risk_level,  # Keep for backward compatibility
                'pest_risk_level': pest_risk_level,  # Keep for backward compatibility
                'premium_ha': premium_ha,  # Insurance premium per hectare
                'risk_category': risk_category  # Risk category label
            }
            
            # Add alert for high risk situations
            if drought_prob > 0.5:
                expected_loss = round(drought_prob * crop_impacts['drought'] * 100)
                record['alert'] = f'High drought risk: {drought_probability}% probability with estimated {expected_loss}% yield loss'
                record['alert_type'] = 'drought'
            elif flood_prob > 0.5:
                expected_loss = round(flood_prob * crop_impacts['flood'] * 100)
                record['alert'] = f'Flood warning: {flood_probability}% probability with estimated {expected_loss}% yield loss'
                record['alert_type'] = 'flood'
            elif pest_prob > 0.5:
                expected_loss = round(pest_prob * crop_impacts['pest'] * 100)
                record['alert'] = f'Pest outbreak: {hail_probability}% probability with estimated {expected_loss}% yield loss'
                record['alert_type'] = 'pest'
            
            climate_data.append(record)
    
    # Create DataFrame and ensure alert columns exist
    df = pd.DataFrame(climate_data)
    
    # Force these columns to exist
    if 'alert' not in df.columns:
        df['alert'] = None
    if 'alert_type' not in df.columns:
        df['alert_type'] = None
    if 'risk_level' not in df.columns:
        df['risk_level'] = df['general_risk'] / 100
    
    return df

def get_risk_category(risk_level):
    """
    Convert numerical risk level to category label based on expected loss
    risk_level: combined probability and impact (expected loss as a proportion)
    """
    if risk_level < 0.05:
        return "Low"
    elif risk_level < 0.10:
        return "Moderate"
    elif risk_level < 0.20:
        return "Medium"
    elif risk_level < 0.30:
        return "High"
    else:
        return "Extreme"

# ... rest of the module remains the same ...