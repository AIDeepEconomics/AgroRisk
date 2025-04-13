# data/data_generation.py
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
    Generate climate risk data for each parcel and day
    parcels_gdf: GeoDataFrame containing parcel information
    days: number of days to generate data for
    """
    climate_data = []
    base_date = datetime.strptime('2025-01-15', '%Y-%m-%d')
    
    for i, parcel in parcels_gdf.iterrows():
        # Base risk from parcel properties or random if not present
        base_risk = parcel.get('base_risk', random.uniform(0.1, 0.5))
        
        # Risk tends to increase over time
        for day in range(days):
            date = base_date + timedelta(days=day)
            
            # General trend is increasing risk, but with periodic variations
            day_phase = (day % 7) / 7.0  # Weekly cycle
            season_phase = (day % 30) / 30.0  # Monthly cycle
            
            # Generate risk values with trends
            drought_risk = (0.2 + day * 0.01 + 0.1 * np.sin(day_phase * 2 * np.pi))
            flood_risk = (0.3 - day * 0.005 + 0.15 * np.sin(season_phase * 2 * np.pi))
            pest_risk = (0.1 + day * 0.003 + 0.05 * np.sin((day_phase + 0.5) * 2 * np.pi))
            
            # Add some randomness
            drought_risk = max(0.01, min(0.95, drought_risk + random.uniform(-0.1, 0.1)))
            flood_risk = max(0.01, min(0.95, flood_risk + random.uniform(-0.1, 0.1)))
            pest_risk = max(0.01, min(0.95, pest_risk + random.uniform(-0.05, 0.05)))
            
            # Implement new rule: if drought risk > 50%, flood risk < 5% and vice versa
            if drought_risk > 0.5:
                flood_risk = random.uniform(0.01, 0.05)
            elif flood_risk > 0.5:
                drought_risk = random.uniform(0.01, 0.05)
            
            # Combine with base risk
            drought_risk = (0.7 * drought_risk + 0.3 * base_risk)
            flood_risk = (0.7 * flood_risk + 0.3 * base_risk)
            pest_risk = (0.7 * pest_risk + 0.3 * base_risk)
            
            # Calculate the general risk level (normalized to 0-1 scale)
            general_risk = (drought_risk + flood_risk + pest_risk) / 3
            
            # Create record with mandatory fields including alert and alert_type (initially empty)
            record = {
                'parcel_id': parcel['id'],
                'date': date.strftime('%Y-%m-%d'),
                'drought_probability': round(drought_risk * 100),
                'flood_probability': round(flood_risk * 100),
                'hail_probability': round(pest_risk * 100),
                'general_risk': round(general_risk * 100),
                'alert': None,  # Always include alert column but set to None by default
                'alert_type': None,  # Always include alert_type column but set to None by default
                'risk_level': general_risk,  # Add risk_level for map rendering (normalized 0-1)
                'drought_risk_level': drought_risk,  # Add drought specific risk level
                'flood_risk_level': flood_risk,  # Add flood specific risk level
                'pest_risk_level': pest_risk,  # Add pest specific risk level
                'premium_ha': round(general_risk * 300, 2),  # Insurance premium per hectare
                'risk_category': get_risk_category(general_risk)  # Risk category label
            }
            
            # Add alert for high risk situations
            if drought_risk > 0.5:
                record['alert'] = f'High drought risk: {round(drought_risk * 100)}%'
                record['alert_type'] = 'drought'
            elif flood_risk > 0.5:
                record['alert'] = f'Flood warning: {round(flood_risk * 100)}%'
                record['alert_type'] = 'flood'
            elif pest_risk > 0.5:
                record['alert'] = f'Pest outbreak: {round(pest_risk * 100)}%'
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
    """Convert numerical risk level to category label"""
    if risk_level < 0.2:
        return "Low"
    elif risk_level < 0.4:
        return "Moderate"
    elif risk_level < 0.6:
        return "Medium"
    elif risk_level < 0.8:
        return "High"
    else:
        return "Extreme"

def generate_insurance_products():
    """
    Generate available microinsurance products
    """
    products = [
        {
            'id': 'drought_ins',
            'name': 'Drought Microinsurance',
            'coverage': 800,  # Per hectare
            'threshold': 'Less than 40% field capacity for 10+ days',
            'min_premium': 45
        },
        {
            'id': 'flood_ins',
            'name': 'Flood Microinsurance',
            'coverage': 700,
            'threshold': 'Soil saturation for 5+ days',
            'min_premium': 40
        },
        {
            'id': 'frost_ins',
            'name': 'Late Frost Microinsurance',
            'coverage': 500,
            'threshold': 'Below 0°C post-emergence',
            'min_premium': 35
        },
        {
            'id': 'pest_ins',
            'name': 'Specific Pest Microinsurance',
            'coverage': 600,
            'threshold': 'Based on verified infestation level',
            'min_premium': 55
        }
    ]
    
    return pd.DataFrame(products)

# Function to load or generate parcels
def load_or_generate_parcels(parcels_file='data/parcels.geojson', n=7):
    """
    Load existing parcels from file or generate new ones if file doesn't exist
    
    Parameters:
    parcels_file (str): Path to the parcels GeoJSON file
    n (int): Number of parcels to generate if file doesn't exist
    
    Returns:
    GeoDataFrame: Parcels with geometry and attributes
    """
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
            
            # Update area with calculated value - ensure it's the right data type
            area_value = float(calculate_area_in_hectares(row['geometry'], lat_center))
            # Convert the area column to float type if it's not already
            if parcels_gdf['area'].dtype != 'float64':
                parcels_gdf['area'] = parcels_gdf['area'].astype(float)
            parcels_gdf.at[idx, 'area'] = area_value
            
    else:
        # Only generate new parcels if file doesn't exist
        if not os.path.exists(os.path.dirname(parcels_file)):
            os.makedirs(os.path.dirname(parcels_file), exist_ok=True)
        parcels_gdf = generate_parcels(n)
        parcels_gdf.to_file(parcels_file, driver='GeoJSON')
        print(f"Generated new parcels and saved to {parcels_file}")
    
    return parcels_gdf

# Function to initialize all data
def initialize_data(days=30, force_regenerate_climate=False, force_regenerate_yield=False):
    """
    Initialize all data for the dynamic risk map application
    
    Parameters:
    days (int): Number of days to generate data for
    force_regenerate_climate (bool): If True, regenerate climate data even if file exists
    force_regenerate_yield (bool): If True, regenerate yield predictions even if file exists
    
    Returns:
    tuple: (parcels_gdf, climate_data, yield_predictions, insurance_products)
    """
    # Load or generate parcels
    parcels_file = 'data/parcels.geojson'
    parcels_gdf = load_or_generate_parcels(parcels_file)
    
    # Climate data
    climate_file = 'data/climate_risk_30days.csv'
    if os.path.exists(climate_file) and not force_regenerate_climate:
        try:
            climate_data = pd.read_csv(climate_file)
            print(f"Loaded existing climate data from {climate_file}")
        except Exception as e:
            print(f"Error loading climate data: {e}. Regenerating...")
            climate_data = generate_climate_data(parcels_gdf, days)
            climate_data.to_csv(climate_file, index=False)
    else:
        climate_data = generate_climate_data(parcels_gdf, days)
        climate_data.to_csv(climate_file, index=False)
        print(f"Generated new climate data and saved to {climate_file}")
    
    # Yield predictions
    yield_file = 'data/yield_predictions.csv'
    if os.path.exists(yield_file) and not force_regenerate_yield:
        try:
            yield_predictions = pd.read_csv(yield_file)
            print(f"Loaded existing yield predictions from {yield_file}")
        except Exception as e:
            print(f"Error loading yield predictions: {e}. Regenerating...")
            update_yield_predictions()
            yield_predictions = pd.read_csv(yield_file)
    else:
        update_yield_predictions()
        yield_predictions = pd.read_csv(yield_file)
        print(f"Generated new yield predictions and saved to {yield_file}")
    
    # Insurance products
    insurance_file = 'data/insurance_products.csv'
    if os.path.exists(insurance_file):
        try:
            insurance_products = pd.read_csv(insurance_file)
            print(f"Loaded existing insurance products from {insurance_file}")
        except Exception as e:
            print(f"Error loading insurance products: {e}. Regenerating...")
            insurance_products = generate_insurance_products()
            insurance_products.to_csv(insurance_file, index=False)
    else:
        insurance_products = generate_insurance_products()
        insurance_products.to_csv(insurance_file, index=False)
        print(f"Generated new insurance products and saved to {insurance_file}")
    
    return parcels_gdf, climate_data, yield_predictions, insurance_products

# Function to update yield predictions that PRESERVES original crop types
def update_yield_predictions():
    """
    Update the yield_predictions.csv file to ensure:
    1. Original crop types are preserved (Maize and Soybean)
    2. Yield values are within the specified ranges for each location-crop combination
    3. Risk values (Drought, Flood, Hail) are different for each parcel with inverse correlation
    """
    # Define yield ranges for each location and crop
    yield_ranges = {
        "Paysandu": {
            "Soybean": (2.0, 2.5),
            "Soybeans": (2.0, 2.5),
            "Soja": (2.0, 2.5),
            "Maize": (6.0, 7.0),
            "Maiz": (6.0, 7.0)
        },
        "Tarariras": {
            "Soybean": (3.2, 4.0),
            "Soybeans": (3.2, 4.0),
            "Soja": (3.2, 4.0),
            "Maize": (8.0, 9.0),
            "Maiz": (8.0, 9.0)
        },
        "San_Javier": {
            "Soybean": (3.2, 4.0),
            "Soybeans": (3.2, 4.0),
            "Soja": (3.2, 4.0),
            "Maize": (8.0, 9.0),
            "Maiz": (8.0, 9.0)
        },
        "Dolores": {
            "Soybean": (2.8, 3.5),
            "Soybeans": (2.8, 3.5),
            "Soja": (2.8, 3.5),
            "Maize": (7.0, 8.0),
            "Maiz": (7.0, 8.0)
        }
    }
    
    # Default for any other locations
    default_range = {
        "Soybean": (2.5, 3.5),
        "Soybeans": (2.5, 3.5),
        "Soja": (2.5, 3.5),
        "Maize": (6.5, 7.5),
        "Maiz": (6.5, 7.5)
    }
    
    # Define risk base values for each region to maintain regional differences
    # but still allow for variation within constraints
    region_risk_bases = {
        "Paysandu": {"drought": 45, "flood": 35},
        "Tarariras": {"drought": 35, "flood": 45},
        "San_Javier": {"drought": 55, "flood": 25},
        "Dolores": {"drought": 40, "flood": 40},
        # Default for any other region
        "default": {"drought": 50, "flood": 30}
    }
    
    # Create the yield predictions file from scratch
    input_file = "data/parcels.geojson"
    output_file = "data/yield_predictions.csv"
    
    # Read the parcels data to get the original crop types and parcel IDs
    try:
        import geopandas as gpd
        parcels_df = gpd.read_file(input_file)
    except Exception as e:
        print(f"Error reading parcels file: {e}")
        return
    
    # Base date for predictions
    base_date = "2025-01-15"
    days = 30
    
    # List to store all predictions
    predictions = []
    
    # Add header
    header = ["parcel_id", "date", "predicted_yield", "confidence", 
              "drought_probability", "flood_probability", "hail_probability", "crop"]
    predictions.append(header)
    
    # For each parcel, generate predictions for each day
    for idx, parcel in parcels_df.iterrows():
        parcel_id = parcel['id']
        
        # PRESERVE THE ORIGINAL CROP - don't modify it
        original_crop = parcel['crop']
        
        # Debug print to check what crop is being read from the parcel
        print(f"Parcel {parcel_id} has crop: {original_crop}")
        
        # Extract location from parcel_id
        parts = parcel_id.split('_')
        location = parts[1] if len(parts) > 1 else "Unknown"
        
        # Get appropriate yield range based on location and crop
        location_ranges = yield_ranges.get(location, default_range)
        
        # Get the yield range for the specific crop type
        if original_crop == "Soja":
            # Use Soja range if available, otherwise use Soybean range
            min_yield, max_yield = location_ranges.get("Soja", default_range.get("Soja", (2.5, 3.5)))
        elif original_crop == "Maiz":
            # Use Maiz range if available, otherwise use Maize range
            min_yield, max_yield = location_ranges.get("Maiz", default_range.get("Maiz", (6.5, 7.5)))
        else:
            # For any other crop, use a default range
            min_yield, max_yield = default_range.get(original_crop, (2.5, 3.5))
        
        # Get the risk base values for this region
        risk_base = region_risk_bases.get(location, region_risk_bases["default"])
        
        # Create a parcel-specific variation within 10% of the region base
        parcel_seed = hash(parcel_id) % 1000
        random.seed(parcel_seed)
        
        # Generate parcel-specific risk baselines with up to 10% variation from region base
        parcel_drought_base = risk_base["drought"] * random.uniform(0.9, 1.1)
        
        # For each day, generate prediction
        for day in range(days):
            # Calculate date
            date_obj = datetime.strptime(base_date, "%Y-%m-%d") + timedelta(days=day)
            date = date_obj.strftime("%Y-%m-%d")
            
            # Calculate yield with slight decrease over time
            day_percentage = day / 30
            yield_reduction = (max_yield - min_yield) * day_percentage * 0.5
            predicted_yield = round(max(min_yield, max_yield - yield_reduction), 2)
            
            # Confidence decreases with time
            confidence = max(40, 85 - day)
            
            # Set a consistent seed for risk values
            day_seed = hash(f"{parcel_id}_{date}") % 10000
            random.seed(day_seed)
            
            # Daily risk variations
            daily_variation = random.uniform(0.95, 1.05)
            
            # Calculate drought risk with day progression factor
            day_factor = 1 + (day / 30) * 0.5  # Increases up to 50% over 30 days
            drought_risk = min(95, int(parcel_drought_base * day_factor * daily_variation))
            
            # Calculate flood risk with EXTREME negative correlation to drought
            drought_normalized = drought_risk / 100.0
            
            # Stronger inverse correlation - when drought is high, flood is very low
            if drought_normalized > 0.9:  # Very high drought
                flood_risk = max(1, int(5 * (1 - drought_normalized) ** 2))
            elif drought_normalized > 0.7:  # High drought
                flood_risk = max(1, int(10 * (1 - drought_normalized) ** 1.5))
            else:  # Normal to low drought
                flood_risk = max(1, int(50 * (1 - drought_normalized)))
            
            # Generate hail risk independently
            hail_risk = random.randint(5, 15)
            
            # Create row
            row = [
                parcel_id, 
                date, 
                str(predicted_yield),
                str(confidence), 
                str(drought_risk), 
                str(flood_risk), 
                str(hail_risk), 
                original_crop  # Keep the original crop type - should be Soja or Maiz from parcels.geojson
            ]
            
            predictions.append(row)
    
    # Write to the file
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(predictions)
    
    print(f"Created {output_file} with preserved crop types and risk values.")

# Add the risk correlation function from update_risk_correlation.py
def calculate_correlated_risks(drought_prob, flood_prob, hail_prob):
    """
    Calculate correlated risks with the following relationships:
    - Strong negative correlation between drought and flood
    - Moderate positive correlation between flood and hail
    """
    # Drought and flood correlation
    correlation_factor = 0.8  # 80% inverse relationship
    base_drought = drought_prob
    base_flood = flood_prob
    
    # Adjust flood probability based on drought
    flood_prob = base_flood * (1 - correlation_factor) + \
                (100 - base_drought) * correlation_factor
    
    # Adjust drought probability based on flood
    drought_prob = base_drought * (1 - correlation_factor) + \
                  (100 - base_flood) * correlation_factor
    
    # Moderate positive correlation between flood and hail
    hail_correlation = 0.4  # 40% relationship
    hail_prob = hail_prob * (1 - hail_correlation) + \
               base_flood * hail_correlation * 0.2  # Scaled down
    
    return round(drought_prob), round(flood_prob), round(hail_prob)

def update_risk_correlations(file_path):
    """
    Update risk correlations in the yield predictions CSV file
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Process each row to update risk correlations
        for i, row in df.iterrows():
            drought_prob = float(row['drought_probability'])
            flood_prob = float(row['flood_probability'])
            hail_prob = float(row['hail_probability'])
            
            # Calculate correlated risks
            drought_prob, flood_prob, hail_prob = calculate_correlated_risks(
                drought_prob, flood_prob, hail_prob)
            
            # Update the DataFrame
            df.at[i, 'drought_probability'] = drought_prob
            df.at[i, 'flood_probability'] = flood_prob
            df.at[i, 'hail_probability'] = hail_prob
        
        # Save the updated DataFrame back to the CSV file
        df.to_csv(file_path, index=False)
        print(f"Updated risk correlations in {file_path}")
    
    except Exception as e:
        print(f"Error updating risk correlations: {e}")

if __name__ == "__main__":
    # Update yield predictions
    update_yield_predictions()
    
    # Regenerate climate data with new alert thresholds
    parcels_gdf, climate_data, yield_predictions, insurance_products = initialize_data(force_regenerate_climate=True)
    
    # Uncomment to update risk correlations
    # update_risk_correlations("data/yield_predictions.csv")  # Update risk correlations
