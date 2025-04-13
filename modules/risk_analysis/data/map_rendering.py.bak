"""
Map rendering module for the dynamic risk map application.
Contains functions for creating and styling maps.
"""
import folium
import branca.colormap as cm
from folium.plugins import TimestampedGeoJson


def create_risk_map(date_str, climate_data, parcels_gdf, risk_type='general', crop_type='all'):
    """
    Create a risk map for a specific date and risk type
    
    Parameters:
    date_str (str): Date string in format 'YYYY-MM-DD'
    climate_data (DataFrame): Climate risk data
    parcels_gdf (GeoDataFrame): Parcels data
    risk_type (str): Type of risk to display ('general', 'drought', 'flood', 'pest')
    crop_type (str): Type of crop to filter ('all', 'soja', 'maiz')
    
    Returns:
    folium.Map: Map with parcels colored by risk level
    """
    # Filter data for the selected date
    date_data = climate_data[climate_data['date'] == date_str]
    
    # If empty, use the earliest date
    if len(date_data) == 0:
        earliest_date = climate_data['date'].min()
        date_data = climate_data[climate_data['date'] == earliest_date]
        date_str = earliest_date
    
    # Verify required columns exist
    required_columns = ['parcel_id', 'date', 'drought_probability', 'flood_probability', 'hail_probability']
    missing_columns = [col for col in required_columns if col not in date_data.columns]
    if missing_columns:
        raise ValueError(f'Missing required columns in climate data: {missing_columns}')
    
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
    
    # Center coordinates for the Chacra parcels
    # Update map center to focus specifically on San Javier parcels
    map_center = [-32.71, -58.08]  # San Javier parcels center coordinates
    zoom_level = 13  # Slightly zoomed out to show all San Javier parcels
    
    # Create a basic map first
    m = folium.Map(
        location=map_center, 
        zoom_start=zoom_level,
        tiles='CartoDB positron',  # Start with a simple base layer
        zoom_control=True  # Enable native Leaflet zoom controls
    )
    
    # Define color scheme based on risk type
    if risk_type == 'drought':
        # Use yellow-orange-red color scheme for drought
        colormap = cm.LinearColormap(
            colors=['#ffeb3b', '#ffc107', '#ff9800', '#ff5722'],
            vmin=0, vmax=1,
            caption='Drought Risk Level'
        )
        map_title = 'Drought Risk Map'
    elif risk_type == 'flood':
        # Use blue color scheme for flood
        colormap = cm.LinearColormap(
            colors=['#e3f2fd', '#90caf9', '#42a5f5', '#1565c0'],
            vmin=0, vmax=1,
            caption='Flood Risk Level'
        )
        map_title = 'Flood Risk Map'
    elif risk_type == 'pest':
        # Use purple color scheme for pests
        colormap = cm.LinearColormap(
            colors=['#f3e5f5', '#ce93d8', '#ab47bc', '#7b1fa2'],
            vmin=0, vmax=1,
            caption='Pest Risk Level'
        )
        map_title = 'Pest Risk Map'
    else:
        # Default general risk (green-yellow-red)
        colormap = cm.LinearColormap(
            colors=['#4caf50', '#cddc39', '#ffeb3b', '#ff9800', '#f44336'],
            vmin=0, vmax=1,
            caption='Risk Level'
        )
        map_title = 'General Risk Map'
    
    m.add_child(colormap)
    
    # Add terrain tiles directly
    # Always add basemap tiles BEFORE parcels to ensure they display as background
    folium.TileLayer(
        'CartoDB positron',
        name='Light Map',
        attr='CartoDB'
    ).add_to(m)
    
    folium.TileLayer(
        'CartoDB dark_matter',
        name='Dark Map',
        attr='CartoDB'
    ).add_to(m)
    
    folium.TileLayer(
        'OpenStreetMap',
        name='Street Map',
        attr='OpenStreetMap'
    ).add_to(m)

    # Add satellite view
    folium.TileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        name='Satellite',
        attr='Esri',
        overlay=False
    ).add_to(m)

    # Apply crop type filter if not 'all'
    filtered_parcels = parcels_gdf
    if crop_type != 'all':
        if crop_type.lower() == 'soja':
            filtered_parcels = parcels_gdf[parcels_gdf['crop'].str.lower() == 'soja']
        elif crop_type.lower() == 'maiz':
            filtered_parcels = parcels_gdf[parcels_gdf['crop'].str.lower() == 'maiz']
    
    # Create dictionaries for quick lookup
    risk_map = dict(zip(date_data['parcel_id'], date_data['risk_level']))
    
    # Add GeoJSON parcels with styling based on risk level
    folium.GeoJson(
        filtered_parcels,
        name='Parcels',
        style_function=lambda feature: {
            'fillColor': colormap(risk_map.get(feature['properties']['id'], 0)),
            'color': 'black',
            'weight': 2,
            'fillOpacity': 0.49
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['id', 'area', 'soil_type', 'crop'],
            aliases=['Parcel ID:', 'Area (ha):', 'Soil Type:', 'Crop:'],
            localize=True,
            sticky=False,
            labels=True,
            style="""
                background-color: #F0EFEF;
                border: 2px solid black;
                border-radius: 3px;
                box-shadow: 3px;
            """,
            max_width=800,
        ),
        popup=folium.GeoJsonPopup(
            fields=['id', 'area', 'soil_type', 'crop'],
            aliases=['Parcel ID:', 'Area (ha):', 'Soil Type:', 'Crop:'],
            localize=True,
            labels=True,
            style="""
                background-color: white;
                border: 2px solid black;
                border-radius: 3px;
                box-shadow: 3px;
            """,
            max_width=800,
        )
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add JavaScript for handling postMessage commands from parent window
    message_listener = """
    <script>
    // Listen for messages from the parent window
    window.addEventListener('message', function(event) {
        try {
            console.log('Message received in map iframe:', event.data);
            
            // Get the map object - with better error handling
            var mapContainer = document.querySelector('.folium-map');
            if (!mapContainer) {
                console.error('Map container not found');
                return;
            }
            
            var map = mapContainer._leaflet_map;
            if (!map) {
                console.error('Leaflet map not found');
                return;
            }
            
            // Process commands
            if (event.data && event.data.command) {
                console.log('Processing command:', event.data.command);
                
                switch(event.data.command) {
                    case 'zoomIn':
                        console.log('Executing zoom in');
                        map.zoomIn(1);  // Explicitly zoom in by 1 level
                        break;
                    case 'zoomOut':
                        console.log('Executing zoom out');
                        map.zoomOut(1);  // Explicitly zoom out by 1 level
                        break;
                    case 'resetMap':
                        console.log('Executing reset map');
                        // Reset to initial view with animation
                        map.flyTo([%s, %s], %s, {
                            animate: true,
                            duration: 0.5
                        });
                        break;
                    case 'toggleLayers':
                        console.log('Executing toggle layers');
                        // Toggle layer control visibility
                        var layerControl = document.querySelector('.leaflet-control-layers');
                        if (layerControl) {
                            if (layerControl.classList.contains('leaflet-control-layers-expanded')) {
                                layerControl.classList.remove('leaflet-control-layers-expanded');
                            } else {
                                layerControl.classList.add('leaflet-control-layers-expanded');
                            }
                        } else {
                            console.error('Layer control not found');
                        }
                        break;
                }
            }
        } catch (error) {
            console.error('Error handling map command:', error);
        }
    });
    </script>
    """ % (map_center[0], map_center[1], zoom_level)
    
    m.get_root().html.add_child(folium.Element(message_listener))
    
    return m

def create_animated_risk_map(parcels_gdf, climate_data, risk_type='general', crop_type='all'):
    """
    Create an animated risk map showing changes over time
    
    Parameters:
    parcels_gdf (GeoDataFrame): Parcels data
    climate_data (DataFrame): Climate risk data
    risk_type (str): Type of risk to display ('general', 'drought', 'flood', 'pest')
    crop_type (str): Type of crop to filter ('all', 'soja', 'maiz')
    
    Returns:
    folium.Map: Map with time-based animation
    """
    # Define color scheme based on risk type
    if risk_type == 'drought':
        # Use yellow-orange-red color scheme for drought
        colormap = cm.LinearColormap(
            colors=['#ffeb3b', '#ffc107', '#ff9800', '#ff5722'],
            vmin=0, vmax=1,
            caption='Drought Risk Level'
        )
        map_title = 'Drought Risk Map'
    elif risk_type == 'flood':
        # Use blue color scheme for flood
        colormap = cm.LinearColormap(
            colors=['#e3f2fd', '#90caf9', '#42a5f5', '#1565c0'],
            vmin=0, vmax=1,
            caption='Flood Risk Level'
        )
        map_title = 'Flood Risk Map'
    elif risk_type == 'pest':
        # Use purple color scheme for pests
        colormap = cm.LinearColormap(
            colors=['#f3e5f5', '#ce93d8', '#ab47bc', '#7b1fa2'],
            vmin=0, vmax=1,
            caption='Pest Risk Level'
        )
        map_title = 'Pest Risk Map'
    else:
        # Default general risk (green-yellow-red)
        colormap = cm.LinearColormap(
            colors=['#4caf50', '#cddc39', '#ffeb3b', '#ff9800', '#f44336'],
            vmin=0, vmax=1,
            caption='Risk Level'
        )
        map_title = 'General Risk Map'
    
    # Prepare features for TimestampedGeoJson
    features = []
    
    # Get unique dates
    dates = sorted(climate_data['date'].unique())
    
    # Center coordinates for the map
    map_center = [-32.71, -58.08]  # San Javier parcels center coordinates
    zoom_level = 13
    
    # Create a base map
    m = folium.Map(
        location=map_center,
        zoom_start=zoom_level,
        tiles='CartoDB positron',
        zoom_control=True  # Enable native Leaflet zoom controls
    )
    
    # Apply crop type filter if not 'all'
    filtered_parcels = parcels_gdf
    if crop_type != 'all':
        if crop_type.lower() == 'soja':
            filtered_parcels = parcels_gdf[parcels_gdf['crop'].str.lower() == 'soja']
        elif crop_type.lower() == 'maiz':
            filtered_parcels = parcels_gdf[parcels_gdf['crop'].str.lower() == 'maiz']
    
    # Add base GeoJSON of parcels
    folium.GeoJson(
        filtered_parcels,
        name='Parcels (Base)',
        style_function=lambda feature: {
            'fillColor': 'lightgray',
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.1
        }
    ).add_to(m)
    
    # Add colormap
    m.add_child(colormap)
    
    # Add terrain tiles directly
    folium.TileLayer(
        'CartoDB positron',
        name='Light Map',
        attr='CartoDB'
    ).add_to(m)
    
    folium.TileLayer(
        'CartoDB dark_matter',
        name='Dark Map',
        attr='CartoDB'
    ).add_to(m)
    
    folium.TileLayer(
        'OpenStreetMap',
        name='Street Map',
        attr='OpenStreetMap'
    ).add_to(m)

    # Add satellite view
    folium.TileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        name='Satellite',
        attr='Esri',
        overlay=False
    ).add_to(m)

    # Process each date
    for date_str in dates:
        # Filter data for this date
        date_data = climate_data[climate_data['date'] == date_str]
        
        # Calculate risk level if not present
        if 'risk_level' not in date_data.columns:
            if risk_type == 'drought':
                date_data['risk_level'] = date_data['drought_probability'] / 100.0
            elif risk_type == 'flood':
                date_data['risk_level'] = date_data['flood_probability'] / 100.0
            elif risk_type == 'pest':
                date_data['risk_level'] = date_data['hail_probability'] / 100.0
            else:
                date_data['risk_level'] = date_data['general_risk'] / 100.0
        
        # Create dictionaries for quick lookup
        risk_map = dict(zip(date_data['parcel_id'], date_data['risk_level']))
        alerts_map = dict(zip(date_data['parcel_id'], date_data['alert']))
        premium_map = dict(zip(date_data['parcel_id'], date_data['premium_ha']))
        category_map = dict(zip(date_data['parcel_id'], date_data['risk_category']))
        
        for idx, row in parcels_gdf.iterrows():
            parcel_id = row['id']
            risk_level = risk_map.get(parcel_id, 0)
            alert = alerts_map.get(parcel_id)
            premium = premium_map.get(parcel_id, 0)
            category = category_map.get(parcel_id, 'Unknown')
            
            # Set color based on risk level
            color = colormap(risk_level)
            
            # Create popup content
            popup_html = f'''
            <div style="width:200px">
                <h4>{parcel_id}</h4>
                <b>Area:</b> {row['area']} ha<br>
                <b>Soil type:</b> {row['soil_type']}<br>
                <b>Risk level:</b> {category} ({risk_level:.2f})<br>
                <b>Premium:</b> ${premium:.2f}/ha<br>
                <b>Total premium:</b> ${premium * row['area']:.2f}<br>
            '''
            
            if alert:
                popup_html += f'<div style="color:red;"><b>Alert:</b> {alert}</div>'
                
            popup_html += '</div>'
            
            # Create feature for this parcel at this time
            feature = {
                'type': 'Feature',
                'geometry': row['geometry'].__geo_interface__,
                'properties': {
                    'time': date_str,
                    'popup': popup_html,
                    'tooltip': parcel_id,
                    'style': {
                        'color': 'black',
                        'weight': 2,
                        'fillColor': color,
                        'fillOpacity': 0.49
                    }
                }
            }
            
            features.append(feature)
    
    # Create TimestampedGeoJson layer
    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': features},
        period='P1D',  # One day per step
        add_last_point=False,
        auto_play=False,
        loop=False,
        max_speed=1,
        loop_button=True,
        date_options='YYYY-MM-DD',
        time_slider_drag_update=True
    ).add_to(m)
    
    # Add JavaScript for handling postMessage commands from parent window
    message_listener = """
    <script>
    // Listen for messages from the parent window
    window.addEventListener('message', function(event) {
        try {
            console.log('Message received in map iframe:', event.data);
            
            // Get the map object - with better error handling
            var mapContainer = document.querySelector('.folium-map');
            if (!mapContainer) {
                console.error('Map container not found');
                return;
            }
            
            var map = mapContainer._leaflet_map;
            if (!map) {
                console.error('Leaflet map not found');
                return;
            }
            
            // Process commands
            if (event.data && event.data.command) {
                console.log('Processing command:', event.data.command);
                
                switch(event.data.command) {
                    case 'zoomIn':
                        console.log('Executing zoom in');
                        map.zoomIn(1);  // Explicitly zoom in by 1 level
                        break;
                    case 'zoomOut':
                        console.log('Executing zoom out');
                        map.zoomOut(1);  // Explicitly zoom out by 1 level
                        break;
                    case 'resetMap':
                        console.log('Executing reset map');
                        // Reset to initial view with animation
                        map.flyTo([%s, %s], %s, {
                            animate: true,
                            duration: 0.5
                        });
                        break;
                    case 'toggleLayers':
                        console.log('Executing toggle layers');
                        // Toggle layer control visibility
                        var layerControl = document.querySelector('.leaflet-control-layers');
                        if (layerControl) {
                            if (layerControl.classList.contains('leaflet-control-layers-expanded')) {
                                layerControl.classList.remove('leaflet-control-layers-expanded');
                            } else {
                                layerControl.classList.add('leaflet-control-layers-expanded');
                            }
                        } else {
                            console.error('Layer control not found');
                        }
                        break;
                }
            }
        } catch (error) {
            console.error('Error handling map command:', error);
        }
    });
    </script>
    """ % (map_center[0], map_center[1], zoom_level)
    
    m.get_root().html.add_child(folium.Element(message_listener))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m