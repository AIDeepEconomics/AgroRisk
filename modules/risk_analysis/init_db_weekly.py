#!/usr/bin/env python
"""
Script para inicializar la base de datos del módulo de análisis de riesgos.
Esta versión modificada genera datos semanales en lugar de mensuales para una visualización más detallada.
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app import app, db
from database.models import Parcel, RiskData, WeatherData, RiskAnalysis

def init_db():
    """Inicializa la base de datos y carga datos de ejemplo con frecuencia semanal."""
    print("Inicializando la base de datos...")
    
    # Crear las tablas en la base de datos
    with app.app_context():
        db.create_all()
        print("Tablas creadas correctamente.")
        
        # Verificar si ya hay datos en la base de datos
        if Parcel.query.count() > 0:
            print("La base de datos ya contiene datos. Saltando la carga de datos de ejemplo.")
            return
        
        # Cargar datos de ejemplo
        print("Cargando datos de ejemplo...")
        
        # Crear parcelas de ejemplo
        parcels = [
            Parcel(name=f"Parcela {i}", area=np.random.uniform(5, 50), 
                   soil_type=np.random.choice(["Arcilloso", "Arenoso", "Franco", "Limoso"]),
                   crop_type=np.random.choice(["Maiz", "Soja", "Trigo", "Girasol"]),
                   latitude=np.random.uniform(-34.9, -34.5),
                   longitude=np.random.uniform(-58.5, -58.0))
            for i in range(1, 11)
        ]
        db.session.add_all(parcels)
        db.session.commit()
        print(f"Creadas {len(parcels)} parcelas de ejemplo.")
        
        # Crear datos de riesgo para cada parcela
        risk_data = []
        start_date = datetime.now() - timedelta(days=365)  # Datos del último año
        
        for parcel in parcels:
            # Generar datos para cada semana (en lugar de cada mes)
            for i in range(52):  # 52 semanas en un año
                date = (start_date + timedelta(days=7*i)).date()
                
                # Simular patrones estacionales (ajustado para semanas)
                season_factor = np.sin(np.pi * i / 26)  # Valor entre -1 y 1
                
                # Riesgos base con componente estacional
                drought_base = max(0, min(1, 0.3 + 0.2 * season_factor + np.random.normal(0, 0.1)))
                flood_base = max(0, min(1, 0.2 - 0.15 * season_factor + np.random.normal(0, 0.1)))
                frost_base = max(0, min(1, 0.1 - 0.3 * season_factor + np.random.normal(0, 0.05)))
                pest_base = max(0, min(1, 0.25 + 0.1 * season_factor + np.random.normal(0, 0.1)))
                
                # Ajustar riesgos según tipo de suelo y cultivo
                soil_factor = {"Arcilloso": 1.2, "Arenoso": 0.8, "Franco": 1.0, "Limoso": 1.1}[parcel.soil_type]
                crop_factor = {"Maiz": 1.0, "Soja": 1.1, "Trigo": 0.9, "Girasol": 1.2}[parcel.crop_type]
                
                drought_risk = max(0, min(1, drought_base * soil_factor))
                flood_risk = max(0, min(1, flood_base * (2 - soil_factor)))
                frost_risk = max(0, min(1, frost_base * crop_factor))
                pest_risk = max(0, min(1, pest_base * crop_factor))
                
                # Riesgo general como promedio ponderado
                overall_risk = max(0, min(1, (drought_risk*0.3 + flood_risk*0.3 + frost_risk*0.2 + pest_risk*0.2)))
                
                # Determinar si hay alerta
                alert = None
                if overall_risk > 0.7:
                    alert = "Alerta de riesgo alto"
                elif overall_risk > 0.5:
                    alert = "Precaución: riesgo moderado"
                
                # Determinar tipo de riesgo principal
                risks = {"drought": drought_risk, "flood": flood_risk, "frost": frost_risk, "pest": pest_risk}
                risk_type = max(risks, key=risks.get)
                
                # Crear registro de riesgo
                risk_data.append(
                    RiskData(
                        parcel_id=parcel.id,
                        date=date,
                        drought_risk=drought_risk,
                        flood_risk=flood_risk,
                        frost_risk=frost_risk,
                        pest_risk=pest_risk,
                        overall_risk=overall_risk,
                        alert=alert,
                        risk_type=risk_type
                    )
                )
        
        # Guardar datos de riesgo
        db.session.add_all(risk_data)
        db.session.commit()
        print(f"Creados {len(risk_data)} registros de riesgo.")
        
        print("Base de datos inicializada correctamente con datos semanales.")

if __name__ == "__main__":
    init_db()
