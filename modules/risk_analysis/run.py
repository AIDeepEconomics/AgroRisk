#!/usr/bin/env python
"""
Script para iniciar el mu00f3dulo de anu00e1lisis de riesgos como una aplicaciu00f3n independiente.
"""
import os
from app import app

if __name__ == '__main__':
    print("Iniciando el mu00f3dulo de Anu00e1lisis de Riesgos...")
    print("Acceda a la aplicaciu00f3n en http://localhost:5001/")
    app.run(debug=True, port=5001)
