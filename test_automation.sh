#!/bin/bash
# Script de prueba para verificar que la automatización funcionará

echo "🧪 PROBANDO AUTOMATIZACIÓN"
echo "=========================="
echo ""

# 1. Verificar que el script existe
if [ ! -f "automate_daily.sh" ]; then
    echo "❌ Error: automate_daily.sh no encontrado"
    exit 1
fi
echo "✅ Script encontrado"

# 2. Verificar permisos de ejecución
if [ ! -x "automate_daily.sh" ]; then
    echo "⚠️  Script no es ejecutable, corrigiendo..."
    chmod +x automate_daily.sh
fi
echo "✅ Permisos correctos"

# 3. Verificar directorio de logs
if [ ! -d "logs" ]; then
    echo "⚠️  Directorio logs no existe, creando..."
    mkdir logs
fi
echo "✅ Directorio logs existe"

# 4. Verificar entorno virtual (opcional)
if [ -d "venv" ]; then
    echo "✅ Entorno virtual encontrado"
else
    echo "⚠️  No se encontró entorno virtual (opcional)"
fi

# 5. Verificar .env
if [ ! -f ".env" ]; then
    echo "❌ Error: archivo .env no encontrado"
    exit 1
fi
echo "✅ Archivo .env existe"

# 6. Verificar dependencias
echo ""
echo "Verificando dependencias Python..."
python -c "import anthropic; import google.oauth2.credentials" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Dependencias instaladas"
else
    echo "❌ Error: faltan dependencias Python"
    echo "   Ejecuta: pip install -r requirements.txt"
    exit 1
fi

# 7. Ejecutar prueba seca
echo ""
echo "Ejecutando prueba (solo clasificar emails nuevos, sin aplicar etiquetas)..."
echo ""

python -m gmail_classifier.main stats

echo ""
echo "=========================="
echo "✅ TODO LISTO PARA AUTOMATIZAR"
echo ""
echo "Próximos pasos:"
echo "  1. Ejecuta: ./setup_automation.sh"
echo "  2. Elige tu método preferido (cron o launchd)"
echo "  3. ¡Relájate! Tus emails se clasificarán solos"
echo ""
