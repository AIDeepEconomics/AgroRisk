# AgroRisk - Plataforma Integrada de Gestiu00f3n de Riesgos Agru00edcolas

Esta plataforma integrada proporciona herramientas avanzadas para la gestiu00f3n de riesgos agru00edcolas, predicciones de rendimiento y productos de microseguro diseñados para pequeños agricultores. Cuenta con una arquitectura modular que permite la integraciu00f3n de diferentes funcionalidades especializadas, como mapas dinu00e1micos de riesgo y anu00e1lisis detallado de patrones de riesgo a lo largo del tiempo.

## Características

- Arquitectura modular para fácil extensión y mantenimiento
- Mapas interactivos de riesgo con visualización temporal
- Análisis avanzado de patrones de riesgo climático
- Predicciones de rendimiento de cultivos
- Recomendaciones de productos de microseguro
- Panel de control con alertas de riesgo y métricas de rendimiento
- Preservación de parcelas personalizadas en formato GeoJSON

## Requisitos

- Python 3.8+
- Flask
- GeoPandas
- Pandas
- Folium
- NumPy
- Shapely
- Matplotlib
- Plotly
- Scikit-learn
- Statsmodels
- SciPy
- PyProj
- Flask-SQLAlchemy

## Configuración

### Opción 1: Entorno Virtual (Recomendado)

1. Clonar el repositorio: `git clone https://github.com/AIDeepEconomics/AgroRisk.git`
2. Crear un entorno virtual:
   ```
   python3 -m venv agrorisk_env
   source agrorisk_env/bin/activate
   ```
3. Instalar los paquetes requeridos para ambos módulos:
   ```
   pip install flask pandas geopandas numpy shapely folium branca pyproj matplotlib scipy statsmodels flask_sqlalchemy
   ```
4. Ejecutar la aplicación integrada (con el entorno virtual activado):
   ```
   ./start_all.sh
   ```
5. Abrir el navegador y acceder a:
   - Aplicación principal: `http://localhost:5000`
   - Módulo de Análisis de Riesgos: `http://localhost:5001`

### Opción 2: Instalación Global

1. Clonar el repositorio: `git clone https://github.com/AIDeepEconomics/AgroRisk.git`
2. Instalar los paquetes requeridos (puede requerir permisos de administrador):
   ```
   pip install -r requirements.txt
   ```
   Nota: En algunos sistemas, puede ser necesario usar `--break-system-packages` si el sistema tiene un entorno Python gestionado externamente.
3. Ejecutar la aplicación integrada: `./start_all.sh`
4. Abrir el navegador y acceder a:
   - Aplicación principal: `http://localhost:5000`
   - Módulo de Análisis de Riesgos: `http://localhost:5001`

## Estructura del Proyecto

```
AgroRisk/
|-- app.py                # Aplicación principal
|-- data/                 # Datos para la aplicación principal
|-- static/               # Archivos estáticos (CSS, JS, imágenes)
|-- templates/            # Plantillas HTML
|-- modules/             # Módulos independientes
|   |-- risk_analysis/   # Módulo de análisis de riesgos
|       |-- app.py       # Aplicación Flask del módulo de análisis
|       |-- run.py       # Script para iniciar el módulo
|       |-- database/    # Modelos y configuración de base de datos
|       |-- backend/     # Lógica de análisis y procesamiento
|       |-- templates/   # Plantillas HTML específicas del módulo
|       |-- static/      # Archivos estáticos específicos del módulo
|-- start_all.sh         # Script para iniciar todos los módulos
|-- requirements.txt     # Dependencias del proyecto
|-- agrorisk_env/        # Entorno virtual (creado durante la configuración)
```

## Desarrollo de Nuevos Módulos

Para agregar un nuevo módulo al sistema:

1. Crear una nueva carpeta dentro de `modules/`
2. Implementar el módulo como una aplicación Flask independiente
3. Actualizar `start_all.sh` para iniciar el nuevo módulo
4. Agregar un enlace en la interfaz principal para acceder al nuevo módulo

## Estructura de Datos

La aplicación utiliza los siguientes archivos de datos:

- `data/parcels.geojson`: Contiene la información geográfica de las parcelas agrícolas
- `data/climate_risk_30days.csv`: Contiene datos de riesgo climático para un período de 30 días
- `data/yield_predictions.csv`: Contiene predicciones de rendimiento para cada parcela
- `data/insurance_products.csv`: Contiene información sobre los productos de seguro disponibles

## Contribución

Si deseas contribuir a este proyecto, por favor sigue estos pasos:

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios y haz commit (`git commit -am 'Añadir nueva funcionalidad'`)
4. Sube los cambios a tu fork (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## Nota Importante

El archivo `parcels.geojson` contiene parcelas personalizadas de Chacra que deben ser preservadas. La aplicación está diseñada para verificar si este archivo existe antes de generar nuevas parcelas aleatorias.

## Requisitos Específicos por Módulo

### Aplicación Principal (app.py)

Paquetes requeridos:
- Flask
- Pandas
- GeoPandas
- NumPy
- Shapely
- Folium
- Branca
- PyProj

### Módulo de Análisis de Riesgos (modules/risk_analysis)

Paquetes adicionales requeridos:
- Flask-SQLAlchemy
- SciPy
- Statsmodels
- Matplotlib

## Solución de Problemas

### Error "No module named..."

Si recibe errores de módulos faltantes al iniciar la aplicación, asegúrese de que todos los paquetes requeridos estén instalados en su entorno:

```
source agrorisk_env/bin/activate  # Activar el entorno virtual
pip install flask pandas geopandas numpy shapely folium branca pyproj matplotlib scipy statsmodels flask_sqlalchemy
```

### Error "Command 'python' not found"

Si el script start_all.sh falla con un error indicando que el comando 'python' no se encuentra, edite el script para usar 'python3' en su lugar:

```
# Cambiar en start_all.sh
python app.py &  -->  python3 app.py &
python run.py &  -->  python3 run.py &
```
