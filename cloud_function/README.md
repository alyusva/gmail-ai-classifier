# ☁️ Gmail Classifier - Cloud Function

Esta carpeta contiene el código para desplegar el clasificador como una Cloud Function en Google Cloud Platform.

## 🎯 Cuándo usar esto

- ✅ Quieres clasificación en **tiempo real** (cuando llega un email)
- ✅ No quieres depender de tu Mac encendido
- ✅ Quieres **productizar** esto como servicio
- ✅ Tienes muchos emails entrantes diarios

## 💰 Costos Estimados

**Google Cloud (Capa Gratuita)**:
- Cloud Function: 2M invocaciones/mes gratis
- Pub/Sub: 10 GB/mes gratis

**Anthropic API**:
- ~$0.15 por 100 emails clasificados
- 1,000 emails/mes ≈ $1.50/mes

**Total estimado**: $0-5/mes dependiendo del volumen

## 📋 Requisitos

1. Cuenta de Google Cloud Platform
2. Proyecto con facturación habilitada (necesario para Cloud Functions)
3. Gmail API habilitada
4. Pub/Sub API habilitada

## 🚀 Setup Rápido

### 1. Instalar Google Cloud CLI

```bash
# En Mac con Homebrew
brew install --cask google-cloud-sdk

# Inicializar
gcloud init
```

### 2. Configurar el Proyecto

```bash
# Crear nuevo proyecto (o usar uno existente)
gcloud projects create gmail-classifier-XXXXX
gcloud config set project gmail-classifier-XXXXX

# Habilitar APIs necesarias
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable gmail.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Habilitar facturación (necesario para Cloud Functions)
# Ir a: https://console.cloud.google.com/billing
```

### 3. Configurar Gmail Push Notifications

```bash
# Crear topic de Pub/Sub
gcloud pubsub topics create gmail-notifications

# Dar permiso a Gmail para publicar en el topic
gcloud pubsub topics add-iam-policy-binding gmail-notifications \
    --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \
    --role=roles/pubsub.publisher

# Crear suscripción al topic
gcloud pubsub subscriptions create gmail-classifier-sub \
    --topic=gmail-notifications
```

### 4. Registrar Gmail Watch

```python
# Ejecutar este script una vez (ya incluido en setup_watch.py)
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

creds = Credentials.from_authorized_user_file('data/token.json')
service = build('gmail', 'v1', credentials=creds)

request = {
    'labelIds': ['INBOX'],
    'topicName': 'projects/gmail-classifier-XXXXX/topics/gmail-notifications'
}

result = service.users().watch(userId='me', body=request).execute()
print(f"Watch configurado: {result}")
# Se renueva automáticamente cada 7 días
```

### 5. Desplegar Cloud Function

```bash
# Desde el directorio cloud_function/
cd cloud_function

# Desplegar
gcloud functions deploy gmail_classifier \
    --runtime python311 \
    --trigger-topic gmail-notifications \
    --entry-point process_email \
    --set-env-vars ANTHROPIC_API_KEY=tu-api-key \
    --memory 512MB \
    --timeout 540s \
    --region us-central1
```

### 6. Verificar

```bash
# Ver logs
gcloud functions logs read gmail_classifier --limit 50

# Probar manualmente
gcloud functions call gmail_classifier \
    --data '{"message":{"data":"test"}}'
```

## 🔄 Mantenimiento

**Ver logs en tiempo real**:
```bash
gcloud functions logs read gmail_classifier --limit 100 --follow
```

**Actualizar variables de entorno**:
```bash
gcloud functions deploy gmail_classifier \
    --update-env-vars ANTHROPIC_API_KEY=nueva-key
```

**Pausar/Reactivar**:
```bash
# No hay forma directa de pausar, pero puedes eliminar y redesplegar
gcloud functions delete gmail_classifier
```

## 📊 Monitoreo

Ver estadísticas en Google Cloud Console:
- **Functions**: https://console.cloud.google.com/functions
- **Pub/Sub**: https://console.cloud.google.com/cloudpubsub
- **Logs**: https://console.cloud.google.com/logs

## ⚠️ Importante

- El Gmail Watch expira cada 7 días, necesitas renovarlo
- La Cloud Function tiene un timeout máximo de 9 minutos
- Procesa emails por lotes para optimizar costos
- Configura alertas de presupuesto en Google Cloud

## 🔐 Seguridad

- Las credenciales se almacenan en Secret Manager
- No expongas tu ANTHROPIC_API_KEY en el código
- Usa service accounts con permisos mínimos

## 📝 TODO para Productización

- [ ] Implementar renovación automática de Gmail Watch
- [ ] Añadir Cloud Scheduler para procesar por lotes
- [ ] Implementar retry logic con Dead Letter Queue
- [ ] Añadir monitoreo con Cloud Monitoring
- [ ] Implementar rate limiting
- [ ] Añadir tests unitarios
- [ ] CI/CD con Cloud Build
- [ ] Multi-tenant (varios usuarios)
- [ ] Dashboard de estadísticas
