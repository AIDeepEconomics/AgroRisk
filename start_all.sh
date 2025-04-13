#!/bin/bash

# Script para iniciar todas las aplicaciones del sistema AgroSmartRisk
echo "Iniciando el sistema AgroSmartRisk..."

# Iniciar el mu00f3dulo principal AgroSmartRisk en segundo plano
echo "Iniciando la aplicaciu00f3n principal AgroSmartRisk en http://localhost:5000/"
python app.py &
PID_MAIN=$!

# Iniciar el mu00f3dulo de anu00e1lisis de riesgos en segundo plano
echo "Iniciando el mu00f3dulo de Anu00e1lisis de Riesgos en http://localhost:5001/"
cd modules/risk_analysis
python run.py &
PID_RISK=$!
cd ../..

echo "Ambas aplicaciones estu00e1n en ejecuciu00f3n."
echo "Aplicaciu00f3n principal: http://localhost:5000/"
echo "Mu00f3dulo de Anu00e1lisis de Riesgos: http://localhost:5001/"
echo ""
echo "Presione Ctrl+C para detener ambas aplicaciones."

# Funciu00f3n para manejar la seu00f1al de interrupciu00f3n (Ctrl+C)
function cleanup {
    echo ""
    echo "Deteniendo las aplicaciones..."
    kill $PID_MAIN
    kill $PID_RISK
    echo "Aplicaciones detenidas."
    exit 0
}

# Registrar la funciu00f3n de limpieza para la seu00f1al de interrupciu00f3n
trap cleanup SIGINT

# Mantener el script en ejecuciu00f3n
while true; do
    sleep 1
done
