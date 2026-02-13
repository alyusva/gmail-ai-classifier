# 🤖 Guía de Automatización - Gmail Classifier

## Opción 1: Cron Job Local (Recomendada - Más Simple) ⭐

Ejecuta la clasificación automáticamente cada día en tu Mac.

### Configuración:

1. **Abrir el editor de crontab**:
```bash
crontab -e
```

2. **Añadir una de estas líneas** (elige según cuándo quieras ejecutarlo):

```bash
# Cada día a las 8:00 AM
0 8 * * * /Users/alvaroyustevalles/Downloads/gmail_classifier/automate_daily.sh

# Cada día a las 22:00 (10 PM)
0 22 * * * /Users/alvaroyustevalles/Downloads/gmail_classifier/automate_daily.sh

# Cada 6 horas
0 */6 * * * /Users/alvaroyustevalles/Downloads/gmail_classifier/automate_daily.sh

# De lunes a viernes a las 9:00 AM
0 9 * * 1-5 /Users/alvaroyustevalles/Downloads/gmail_classifier/automate_daily.sh
```

3. **Guardar y salir** (en vim: `ESC` + `:wq`)

4. **Verificar que está configurado**:
```bash
crontab -l
```

### Ventajas:
- ✅ Muy simple de configurar
- ✅ No requiere servicios externos
- ✅ Gratis
- ✅ Total control

### Desventajas:
- ❌ Tu Mac debe estar encendido
- ❌ No es tiempo real (solo se ejecuta en los horarios programados)

---

## Opción 2: Launchd (Alternativa a Cron en Mac)

macOS prefiere usar `launchd` en lugar de cron. Más confiable.

### Archivo ya creado: `com.gmail.classifier.plist`

1. **Copiar el archivo a LaunchAgents**:
```bash
cp com.gmail.classifier.plist ~/Library/LaunchAgents/
```

2. **Cargar el servicio**:
```bash
launchctl load ~/Library/LaunchAgents/com.gmail.classifier.plist
```

3. **Verificar estado**:
```bash
launchctl list | grep gmail.classifier
```

4. **Para desactivarlo**:
```bash
launchctl unload ~/Library/LaunchAgents/com.gmail.classifier.plist
```

---

## Opción 3: Cloud Function (Google Cloud) - Tiempo Real

Para clasificación automática inmediata cuando llegan emails nuevos.

### Requisitos:
- Cuenta de Google Cloud (tiene capa gratuita)
- Gmail API con Pub/Sub habilitado

### Pasos:

1. **Habilitar Gmail Pub/Sub** en Google Cloud Console
2. **Crear Cloud Function** con el código en `cloud_function/`
3. **Configurar trigger** para Gmail topic

### Ventajas:
- ✅ Tiempo real (clasifica al recibir email)
- ✅ No necesitas tu Mac encendido
- ✅ Escala automáticamente

### Desventajas:
- ❌ Más complejo de configurar
- ❌ Requiere configuración en Google Cloud
- ❌ Puede tener coste (aunque mínimo con capa gratuita)

**📄 Instrucciones completas**: Ver `cloud_function/README.md`

---

## Opción 4: Gmail Apps Script - Más Integrado

Script que se ejecuta directamente dentro de Gmail.

### Pasos:

1. Ir a [script.google.com](https://script.google.com)
2. Crear nuevo proyecto
3. Copiar código de `apps_script/classifier.gs`
4. Configurar trigger periódico

### Ventajas:
- ✅ Se ejecuta en Gmail directamente
- ✅ No necesita servidor
- ✅ Gratis

### Desventajas:
- ❌ Limitaciones de cuota de Apps Script
- ❌ No puede usar Anthropic API directamente (necesita proxy)

---

## 📊 Comparación Rápida

| Característica | Cron/Launchd | Cloud Function | Apps Script |
|----------------|--------------|----------------|-------------|
| **Dificultad** | ⭐ Fácil | ⭐⭐⭐ Difícil | ⭐⭐ Media |
| **Coste** | Gratis | ~$0-5/mes | Gratis |
| **Tiempo real** | ❌ No | ✅ Sí | ⚠️ Parcial |
| **Mac encendido** | ✅ Necesario | ❌ No | ❌ No |
| **Setup** | 2 min | 30 min | 15 min |

---

## 🎯 Recomendación

**Para empezar**: Usa **Opción 1 (Cron)** o **Opción 2 (Launchd)**
- Simple, gratis, y funciona perfectamente para uso personal
- Si dejas tu Mac encendido, es la mejor opción

**Para producción/productizar**: Usa **Opción 3 (Cloud Function)**
- Si quieres venderlo como servicio
- Si necesitas tiempo real
- Si no puedes tener tu Mac encendido

---

## 🔧 Mantenimiento

**Ver logs de las ejecuciones automáticas**:
```bash
# Ver logs de hoy
cat logs/auto_$(date +%Y%m%d).log

# Ver todos los logs recientes
ls -lt logs/ | head -10

# Limpiar logs antiguos (más de 30 días)
find logs/ -name "auto_*.log" -mtime +30 -delete
```

**Ejecutar manualmente para probar**:
```bash
./automate_daily.sh
```

---

## ❓ FAQ

**¿Cuánto cuesta clasificar emails nuevos?**
- Anthropic cobra ~$3 por millón de tokens input, ~$15 por millón output
- Un email promedio: ~500 tokens
- 100 emails/día ≈ $0.15/día ≈ $4.50/mes

**¿Puedo pausar la automatización?**
```bash
# Con cron
crontab -e  # Comentar la línea con #

# Con launchd
launchctl unload ~/Library/LaunchAgents/com.gmail.classifier.plist
```

**¿Cómo sé si está funcionando?**
```bash
# Ver última ejecución
ls -lt logs/ | head -1
tail logs/auto_$(date +%Y%m%d).log
```
