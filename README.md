# 📧 Gmail AI Classifier

**Clasificador inteligente de emails usando Claude AI** - Organiza automáticamente tu bandeja de Gmail con inteligencia artificial.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Anthropic Claude](https://img.shields.io/badge/AI-Claude%20Sonnet%204-purple)](https://www.anthropic.com/)

> 🚀 **Nuevo**: ¡Ahora con soporte para web app y despliegue en la nube!

## 🏗️ Arquitectura

```
Gmail API ──► SQLite (local) ──► Claude API ──► Gmail Labels
  extract        almacena         classify        apply
```

**3 fases independientes y reanudables:**

1. **Extract** → Descarga metadata de todos tus emails a SQLite local
2. **Classify** → Envía batches a Claude para clasificar por categorías
3. **Apply** → Crea etiquetas en Gmail y las aplica a cada email

## 📋 Requisitos previos

- Python 3.10+
- Una cuenta de Google (Gmail)
- Una API key de Anthropic ([console.anthropic.com](https://console.anthropic.com))

## 🚀 Setup paso a paso

### 1. Clonar y preparar entorno

```bash
cd gmail_classifier
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. Configurar Google Cloud Console (Gmail API)

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto (o usa uno existente)
3. Ve a **APIs & Services → Library**
4. Busca **"Gmail API"** y habilítala
5. Ve a **APIs & Services → Credentials**
6. Click en **"Create Credentials" → "OAuth client ID"**
7. Si te pide configurar la pantalla de consentimiento:
   - Tipo: **External**
   - Nombre de la app: "Gmail Classifier" (o lo que quieras)
   - Añade tu email como usuario de prueba
8. Tipo de aplicación: **Desktop app**
9. Descarga el JSON y guárdalo como **`credentials.json`** en la raíz del proyecto (junto a `requirements.txt`)

> ⚠️ **Importante**: Al ser una app "en testing", Google limita a 100 usuarios. Como solo eres tú, no hay problema. La primera vez que ejecutes `extract`, se abrirá el navegador para autenticarte.

### 3. Configurar API de Anthropic

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-tu-clave-aqui"
```

Para hacerlo persistente, añádelo a tu `.bashrc` / `.zshrc`:

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-tu-clave-aqui"' >> ~/.zshrc
```

### 4. (Opcional) Personalizar taxonomía

Edita `gmail_classifier/config.py` y modifica `DEFAULT_TAXONOMY` con tus categorías preferidas:

```python
DEFAULT_TAXONOMY = [
    "Newsletters",
    "Compras/Pedidos",
    "Bancos/Finanzas",
    "Trabajo/Dentsu",          # ← Personaliza
    "Trabajo/Anteriores",      # ← Personaliza
    "Redes Sociales",
    # ... etc
]
```

## 📖 Uso

### Flujo completo recomendado

```bash
# 1️⃣ Extraer emails (primera vez tarda ~30-60 min para 17K emails)
python -m gmail_classifier.main extract

# 2️⃣ Clasificar con Claude (~$2-5 USD para 17K emails)
python -m gmail_classifier.main classify

# 3️⃣ Revisar estadísticas ANTES de aplicar
python -m gmail_classifier.main stats

# 4️⃣ Simular (dry-run) para ver qué haría
python -m gmail_classifier.main dry-run --limit 100

# 5️⃣ Aplicar etiquetas en Gmail
python -m gmail_classifier.main apply
```

### Comandos disponibles

| Comando | Descripción |
|---------|-------------|
| `extract` | Descarga metadata de emails de Gmail a SQLite |
| `extract --max 500` | Extrae solo los primeros 500 emails (para testing) |
| `classify` | Clasifica emails no clasificados usando Claude |
| `stats` | Muestra estadísticas y distribución por categoría |
| `dry-run` | Simula la aplicación de etiquetas |
| `dry-run --limit 100` | Simula solo 100 emails |
| `apply` | Aplica las etiquetas en Gmail |
| `apply --dry-run` | Igual que dry-run |
| `apply --limit 1000` | Aplica solo a 1000 emails |
| `reset all` | Borra toda la base de datos |
| `reset classifications` | Borra solo clasificaciones (mantiene emails) |
| `reset applied` | Resetea marcas de "aplicado" para re-aplicar |

Añade `-v` para modo verbose: `python -m gmail_classifier.main -v extract`

### ⏸️ Reanudación automática

Si la extracción o clasificación se interrumpe (Ctrl+C, error de red, etc.), simplemente vuelve a ejecutar el mismo comando. El progreso se guarda automáticamente en SQLite.

## 💰 Coste estimado

Para **~17,700 emails** usando Claude Sonnet:

| Concepto | Estimación |
|----------|-----------|
| Batches de clasificación | ~354 llamadas |
| Tokens de input | ~3.5M tokens (~$10.5) |
| Tokens de output | ~350K tokens (~$5.25) |
| **Total estimado** | **~$15 USD** |
| Gmail API | Gratis |

> 💡 **Tip**: Para reducir costes, usa `claude-haiku-4-5-20251001` en `config.py` (~$1-2 USD total), con algo menos de precisión.

## 📁 Estructura del proyecto

```
gmail_classifier/
├── credentials.json          ← Tu archivo de Google Cloud (NO commitear)
├── requirements.txt
├── README.md
├── gmail_classifier/
│   ├── __init__.py
│   ├── config.py             ← Configuración central
│   ├── db.py                 ← SQLite (almacenamiento local)
│   ├── extractor.py          ← Gmail API (descarga emails)
│   ├── classifier.py         ← Claude API (clasificación IA)
│   ├── applier.py            ← Gmail API (aplica etiquetas)
│   └── main.py               ← CLI principal
└── data/                     ← Auto-generado
    ├── emails.db             ← Base de datos SQLite
    ├── token.json            ← Token OAuth2 (auto-generado)
    └── classifier.log        ← Logs
```

## 🏷️ Etiquetas en Gmail

Las etiquetas se crean bajo el prefijo **`AutoSort/`**:

```
AutoSort/
├── Newsletters
├── Compras/Pedidos
├── Bancos/Finanzas
├── Trabajo
├── Redes Sociales
├── ...
```

Puedes cambiar el prefijo en `config.py` → `LABEL_PREFIX`.

## 🔧 Troubleshooting

**"credentials.json not found"**
→ Descarga el OAuth client JSON desde Google Cloud Console y colócalo en la raíz del proyecto.

**"ANTHROPIC_API_KEY no configurada"**
→ `export ANTHROPIC_API_KEY=sk-ant-...`

**"Token has been expired or revoked"**
→ Borra `data/token.json` y ejecuta `extract` de nuevo para re-autenticarte.

**"Rate limit exceeded" (Gmail)**
→ El script ya tiene rate limiting. Si persiste, espera unos minutos y re-ejecuta.

**"Rate limit exceeded" (Claude)**
→ Aumenta el `time.sleep()` en `classifier.py` o reduce `CLASSIFY_BATCH_SIZE` en `config.py`.

## 🛡️ Seguridad

- `credentials.json` y `data/token.json` contienen credenciales sensibles → **no los subas a Git**
- Añade al `.gitignore`:

```gitignore
credentials.json
data/
*.db
```

- Los permisos solicitados son `gmail.modify` y `gmail.labels` (lectura + modificar etiquetas, NO puede enviar emails ni borrar)

## 🌐 Web App & Cloud Deployment

### Migrar a Supabase (Base de datos en la nube)

```bash
# Ver guía completa de migración
cat docs/SUPABASE_MIGRATION.md

# O ejecutar el script de migración
python scripts/migrate_to_supabase.py
```

**Beneficios**:
- ✅ Base de datos accesible desde cualquier lugar
- ✅ Backups automáticos
- ✅ Multi-usuario
- ✅ APIs automáticas

### Web App (Next.js + React)

```bash
# Instalar dependencias
cd web
npm install

# Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local con tus credenciales

# Iniciar en desarrollo
npm run dev

# Abrir http://localhost:3000
```

**Características de la web app**:
- 📊 Dashboard con estadísticas en tiempo real
- ⚙️ Configuración de categorías personalizadas
- 🏷️ Gestión de etiquetas
- 📈 Gráficos de distribución
- 🔄 Clasificación manual/automática
- 👤 Multi-usuario (próximamente)

### Deploy en la Nube

#### Opción 1: Vercel (Frontend + API Routes)

```bash
# Instalar Vercel CLI
npm i -g vercel

# Desde /web
cd web
vercel

# Configurar variables de entorno en Vercel Dashboard
# - SUPABASE_URL
# - SUPABASE_ANON_KEY
# - ANTHROPIC_API_KEY
```

#### Opción 2: Google Cloud Functions (Backend)

```bash
# Ver guía completa
cat cloud_function/README.md

# Deploy rápido
cd cloud_function
gcloud functions deploy gmail_classifier \
  --runtime python311 \
  --trigger-http \
  --entry-point classify_emails \
  --set-env-vars ANTHROPIC_API_KEY=xxx,SUPABASE_URL=xxx
```

## 🤖 Automatización Avanzada

Configura la clasificación automática de nuevos emails:

```bash
# Setup interactivo
./setup_automation.sh
```

**Opciones disponibles**:
- 📅 **Cron Job**: Ejecutar diariamente en tu Mac
- 🍎 **Launchd**: Servicio nativo de macOS (recomendado para local)
- ☁️ **Cloud Function**: Clasificación en tiempo real en la nube
- 🔔 **Gmail Push**: Trigger automático con nuevos emails

Ver guía completa: [AUTOMATION.md](AUTOMATION.md)

## 📈 Roadmap

- [x] Clasificación básica con IA
- [x] Auto-etiquetado en Gmail
- [x] CLI funcional
- [x] Automatización local
- [ ] Web app completa
- [ ] Migración a Supabase
- [ ] Multi-usuario
- [ ] Dashboard analytics
- [ ] Clasificación en tiempo real (Push Notifications)
- [ ] Filtros personalizados
- [ ] Exportar/importar configuración
- [ ] API REST pública
- [ ] Extensión de Chrome

## 💰 Costos Cloud

**Producción en cloud** (estimado mensual):
- **Anthropic API**: ~$0.15 por 100 emails
  - 1,000 emails/mes ≈ $1.50
  - 10,000 emails/mes ≈ $15
- **Supabase**: Gratis hasta 500MB + 2GB transferencia
- **Google Cloud Functions**: 2M invocaciones gratis/mes
- **Vercel**: Plan hobby gratis
- **Total**: ~$1-20/mes dependiendo del volumen

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.

## 👤 Autor

**Álvaro Yuste Valles**
- GitHub: [@alyusva](https://github.com/alyusva)

## 🙏 Agradecimientos

- [Anthropic](https://www.anthropic.com/) - Claude AI
- [Google](https://developers.google.com/gmail/api) - Gmail API
- [Supabase](https://supabase.com/) - Base de datos en la nube
- [Vercel](https://vercel.com/) - Hosting & deployment

---

⭐ **Si te ha sido útil, dale una estrella al repo!**

📧 **¿Quieres la versión cloud lista para usar?** Próximamente en [gmailclassifier.app](https://gmailclassifier.app)
