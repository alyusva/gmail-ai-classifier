#!/bin/bash
# Script de automatización diaria para clasificar emails nuevos

# Cambiar al directorio del proyecto
cd /Users/alvaroyustevalles/Downloads/gmail_classifier

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ejecutar clasificación y aplicación de etiquetas
echo "$(date): Iniciando clasificación automática..."
python -m gmail_classifier.main classify >> logs/auto_$(date +%Y%m%d).log 2>&1
python -m gmail_classifier.main apply >> logs/auto_$(date +%Y%m%d).log 2>&1
echo "$(date): Clasificación completada"
