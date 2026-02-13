#!/bin/bash
# Setup de automatización para Gmail Classifier

echo "🤖 CONFIGURACIÓN DE AUTOMATIZACIÓN - GMAIL CLASSIFIER"
echo "=================================================="
echo ""

echo "Selecciona tu método preferido:"
echo ""
echo "1. 📅 Cron Job (Simple - Recomendado para empezar)"
echo "2. 🍎 Launchd (Nativo de macOS - Más confiable)"
echo "3. ☁️  Cloud Function (Avanzado - Tiempo real)"
echo "4. 📖 Ver documentación completa"
echo "5. ❌ Cancelar"
echo ""

read -p "Elige una opción (1-5): " option

case $option in
    1)
        echo ""
        echo "📅 CONFIGURANDO CRON JOB"
        echo "========================"
        echo ""
        echo "Elige la frecuencia:"
        echo "1. Cada día a las 8:00 AM"
        echo "2. Cada día a las 22:00 (10 PM)"
        echo "3. Cada 6 horas"
        echo "4. De lunes a viernes a las 9:00 AM"
        echo "5. Personalizado"

        read -p "Opción (1-5): " freq

        case $freq in
            1) CRON_LINE="0 8 * * * $(pwd)/automate_daily.sh" ;;
            2) CRON_LINE="0 22 * * * $(pwd)/automate_daily.sh" ;;
            3) CRON_LINE="0 */6 * * * $(pwd)/automate_daily.sh" ;;
            4) CRON_LINE="0 9 * * 1-5 $(pwd)/automate_daily.sh" ;;
            5)
                read -p "Ingresa expresión cron: " custom_cron
                CRON_LINE="$custom_cron $(pwd)/automate_daily.sh"
                ;;
        esac

        echo ""
        echo "Se añadirá esta línea al crontab:"
        echo "$CRON_LINE"
        echo ""
        read -p "¿Continuar? (y/n): " confirm

        if [ "$confirm" = "y" ]; then
            (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
            echo "✅ Cron job configurado!"
            echo ""
            echo "Ver configuración actual:"
            crontab -l
        else
            echo "❌ Cancelado"
        fi
        ;;

    2)
        echo ""
        echo "🍎 CONFIGURANDO LAUNCHD"
        echo "======================="
        echo ""

        PLIST_FILE="$(pwd)/com.gmail.classifier.plist"
        LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

        if [ ! -d "$LAUNCH_AGENTS" ]; then
            mkdir -p "$LAUNCH_AGENTS"
        fi

        echo "Copiando archivo de configuración..."
        cp "$PLIST_FILE" "$LAUNCH_AGENTS/"

        echo "Cargando servicio..."
        launchctl load "$LAUNCH_AGENTS/com.gmail.classifier.plist"

        echo "✅ Launchd configurado!"
        echo ""
        echo "El clasificador se ejecutará todos los días a las 8:00 AM"
        echo ""
        echo "Comandos útiles:"
        echo "  Ver estado: launchctl list | grep gmail.classifier"
        echo "  Desactivar: launchctl unload $LAUNCH_AGENTS/com.gmail.classifier.plist"
        echo "  Ver logs: cat logs/launchd_stdout.log"
        ;;

    3)
        echo ""
        echo "☁️  CLOUD FUNCTION SETUP"
        echo "======================="
        echo ""
        echo "Para configurar Cloud Function, sigue la guía en:"
        echo "  📖 cloud_function/README.md"
        echo ""
        echo "Abriendo documentación..."

        if command -v open &> /dev/null; then
            open cloud_function/README.md
        else
            cat cloud_function/README.md
        fi
        ;;

    4)
        echo ""
        echo "📖 Abriendo documentación completa..."
        if command -v open &> /dev/null; then
            open AUTOMATION.md
        else
            cat AUTOMATION.md
        fi
        ;;

    5)
        echo "❌ Cancelado"
        exit 0
        ;;

    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo "✅ ¡Configuración completada!"
echo ""
echo "Ejecutar manualmente para probar:"
echo "  ./automate_daily.sh"
echo ""
echo "Ver logs:"
echo "  ls -lt logs/"
echo "  cat logs/auto_\$(date +%Y%m%d).log"
echo ""
