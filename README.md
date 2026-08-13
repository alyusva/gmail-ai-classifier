# 📧 Gmail AI Classifier

**Clasificador personal de emails usando Claude AI** — organiza tu bandeja de Gmail automáticamente.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Anthropic Claude](https://img.shields.io/badge/AI-Claude%20Haiku%204.5-purple)](https://www.anthropic.com/)

## 🏗️ Arquitectura

Herramienta personal, sin base de datos externa, sin web, sin multi-usuario:

```
CLI local (una vez / bajo demanda)
  Gmail API ──► SQLite (local) ──► Claude API ──► Gmail Labels
    extract        almacena         classify        apply

Cron en Vercel (semanal, correo nuevo)
  Gmail API (solo -label:IA) ──► Claude API ──► Gmail Labels
```

- **CLI local** (`gmail_classifier/`): repaso completo de tu bandeja — extract → classify → stats → dry-run → apply. Usa SQLite para poder reanudar y revisar antes de aplicar nada.
- **Función cron en Vercel** (`api/classify_new.py`): una vez a la semana, busca correo que aún no tenga la label `IA` y lo clasifica. No usa ninguna base de datos: la propia label `IA` (aplicada a todo email procesado) es la marca de "ya visto".

## 📋 Requisitos previos

- Python 3.10+
- Una cuenta de Google (Gmail)
- Una API key de Anthropic ([console.anthropic.com](https://console.anthropic.com))
- (Solo para el cron) Una cuenta de [Vercel](https://vercel.com) y el [Vercel CLI](https://vercel.com/docs/cli)

## 🚀 Setup local paso a paso

### 1. Preparar entorno

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configurar Google Cloud Console (Gmail API)

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto (o usa uno existente)
3. **APIs & Services → Library** → busca **"Gmail API"** y habilítala
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
5. Si te pide configurar la pantalla de consentimiento:
   - Tipo: **External**
   - Nombre de la app: lo que quieras
   - Añade tu email como usuario de prueba
6. Tipo de aplicación: **Desktop app**
7. Descarga el JSON y guárdalo como **`credentials.json`** en la raíz del proyecto

> ⚠️ Al ser una app "en testing", Google limita a 100 usuarios — como solo eres tú, no hay problema. La primera vez que ejecutes `extract` se abrirá el navegador para autenticarte, y se guardará el token (con su refresh_token) en `data/token.json`.

### 3. Configurar API de Anthropic

```bash
cp .env.example .env
# Edita .env y añade tu ANTHROPIC_API_KEY
```

### 4. (Opcional) Ajustar taxonomía

Las 15 categorías por defecto están en `gmail_classifier/config.py` → `DEFAULT_TAXONOMY`, más una categoría oculta `Otros` (`FALLBACK_CATEGORY`) para correos que no encajan claramente en ninguna:

```
Bancos/Finanzas · Compras/Pedidos · Desarrollo/Tech · Formación/Educación ·
Gobierno/Administración · Hipoteca · Newsletters · Notificaciones/Alertas ·
Personal · Redes Sociales · Salud/Deporte · Spam/Promociones ·
Suscripciones/SaaS · Trabajo · Viajes/Transporte
```

## 📖 Uso — CLI local

### Flujo completo recomendado

```bash
# 1️⃣ Extraer emails (metadata: asunto/remitente/snippet, no el cuerpo)
python -m gmail_classifier.main extract

# 2️⃣ Clasificar con Claude
python -m gmail_classifier.main classify

# 3️⃣ Revisar la distribución ANTES de tocar Gmail
python -m gmail_classifier.main stats

# 4️⃣ Simular (dry-run) para ver qué haría, sin aplicar nada
python -m gmail_classifier.main dry-run --limit 100

# 5️⃣ Aplicar etiquetas en Gmail (de verdad)
python -m gmail_classifier.main apply

# 6️⃣ (Opcional) Borrar labels de categorías huérfanas (vacías, fuera de la taxonomía)
python -m gmail_classifier.main cleanup-labels
```

### Comandos disponibles

| Comando | Descripción |
|---------|-------------|
| `extract` | Descarga metadata de emails de Gmail a SQLite |
| `extract --max 500` | Extrae solo los primeros 500 emails (para testing) |
| `classify` | Clasifica emails no clasificados usando Claude |
| `stats` | Muestra estadísticas y distribución por categoría |
| `dry-run [--limit N]` | Simula la aplicación de etiquetas |
| `apply [--dry-run] [--limit N]` | Aplica las etiquetas en Gmail |
| `cleanup-labels [--dry-run]` | Borra labels de categoría vacías fuera de la taxonomía actual |
| `reset {all,classifications,applied}` | Borra datos locales (con confirmación) |

Añade `-v` para modo verbose: `python -m gmail_classifier.main -v extract`

### ⏸️ Reanudación automática

Si `extract` o `classify` se interrumpen, vuelve a ejecutar el mismo comando — el progreso se guarda en SQLite (`data/emails.db`).

## 🏷️ Etiquetas en Gmail

Las categorías se crean como labels **sueltas de nivel superior** (`Trabajo`, `Bancos/Finanzas`, `Personal`...) — el "/" de algunas categorías es parte de su propio nombre, no un prefijo añadido. Además, cada email procesado recibe también la label de marca **`IA`** (no es padre de nada) como marca de "ya clasificado" — es lo que le permite a la función cron detectar correo nuevo sin necesitar ninguna base de datos:

```
IA                    ← marca, aplicada a TODO email procesado
Trabajo
Bancos/Finanzas
Personal
...
```

Puedes cambiar el nombre de la marca en `.env` → `MARKER_LABEL` (por defecto `IA`).

## 💰 Coste estimado (Claude Haiku 4.5)

Para **~20.000 emails** (batches de 50, `claude-haiku-4-5-20251001` a $1/$5 por millón de tokens input/output):

| Concepto | Estimación |
|----------|-----------|
| Batches de clasificación | ~400 llamadas |
| **Total estimado** | **~$3-8 USD** |
| Gmail API | Gratis |

El coste real depende de la longitud media de tus asuntos/snippets; revisa `response.usage` en los logs si quieres un número exacto para tu bandeja.

## 🌐 Cron semanal en Vercel

Una función Python (`api/classify_new.py`) que Vercel invoca una vez a la semana. Reutiliza el mismo código de clasificación que el CLI (`gmail_classifier/classifier.py`, `config.py`) — no hay una segunda taxonomía ni un segundo prompt que mantener sincronizados.

### Cómo funciona

1. Se autentica en Gmail con un **refresh_token** guardado como variable de entorno (sin flujo interactivo — ver más abajo cómo obtenerlo).
2. Asegura que existen la label de marca `IA` y las 15 de categoría.
3. Busca mensajes con `-label:IA` (correo que nunca ha sido procesado).
4. Los clasifica con Claude y aplica las etiquetas correspondientes.
5. Devuelve un resumen JSON (visible en `vercel logs`).

### Desplegar

1. **Obtén el refresh_token**: tras ejecutar `extract` en local al menos una vez, copia el campo `"refresh_token"` de `data/token.json` (nunca lo pegues en el chat ni lo subas a git).
2. **Configura las variables de entorno en Vercel**:

   ```bash
   vercel link
   vercel env add ANTHROPIC_API_KEY
   vercel env add ANTHROPIC_MODEL          # claude-haiku-4-5-20251001
   vercel env add GOOGLE_CLIENT_ID         # de credentials.json
   vercel env add GOOGLE_CLIENT_SECRET     # de credentials.json
   vercel env add GOOGLE_REFRESH_TOKEN     # de data/token.json
   vercel env add CRON_SECRET              # openssl rand -hex 32
   vercel env add MARKER_LABEL             # IA
   ```

3. **Despliega**:

   ```bash
   vercel deploy --prod
   ```

4. **Prueba manualmente** antes de dejar que el cron corra solo:

   ```bash
   curl -H "Authorization: Bearer $CRON_SECRET" \
     https://<tu-proyecto>.vercel.app/api/classify_new
   ```

5. **Verifica el cron** en el dashboard de Vercel → Project → Settings → Cron Jobs. La programación está en `vercel.json` (`0 6 * * 1` = lunes 06:00 UTC); cámbiala ahí si quieres otro día/hora.

## 🔧 Troubleshooting

**"credentials.json not found"**
→ Descarga el OAuth client JSON desde Google Cloud Console y colócalo en la raíz del proyecto.

**"ANTHROPIC_API_KEY no configurada"**
→ `export ANTHROPIC_API_KEY=sk-ant-...` o añádela a `.env`.

**"Token has been expired or revoked"**
→ Borra `data/token.json` y ejecuta `extract` de nuevo para re-autenticarte (y actualiza `GOOGLE_REFRESH_TOKEN` en Vercel con el nuevo valor).

**"Rate limit exceeded" (Gmail o Claude)**
→ El script ya tiene rate limiting incorporado; si persiste, reduce `CLASSIFY_BATCH_SIZE` en `.env` y reintenta.

**El cron de Vercel no clasifica nada**
→ Comprueba que `GOOGLE_REFRESH_TOKEN` sigue siendo válido y que las 4 variables de Google/Anthropic están puestas; revisa `vercel logs` para el error exacto.

## 🛡️ Seguridad

Ver [SECURITY.md](SECURITY.md) para el detalle completo. Resumen:

- `credentials.json`, `.env`, `data/` están en `.gitignore` — nunca se commitean.
- Los permisos de Gmail solicitados son mínimos: `gmail.modify` y `gmail.labels`. No puede enviar ni borrar emails.
- El secret del cron (`CRON_SECRET`) evita que `/api/classify_new` sea invocable públicamente.

## 📁 Estructura del proyecto

```
gmail_classifier/
├── credentials.json          ← Tu archivo de Google Cloud (NO commitear)
├── gmail_classifier/
│   ├── config.py             ← Taxonomía, modelo, configuración central
│   ├── db.py                 ← SQLite (uso local)
│   ├── extractor.py          ← Gmail API (descarga emails, uso local)
│   ├── classifier.py         ← Claude API (clasificación IA, compartido con Vercel)
│   ├── applier.py            ← Gmail API (aplica etiquetas, uso local)
│   ├── gmail_auth.py         ← Credenciales desde refresh_token (uso Vercel)
│   └── main.py                ← CLI principal
├── api/
│   └── classify_new.py       ← Función cron de Vercel (correo nuevo, semanal)
├── vercel.json                ← Configuración del cron
└── data/                      ← Auto-generado (SQLite, token, logs)
```

## 📝 Licencia

MIT License — ver [LICENSE](LICENSE).

## 👤 Autor

**Álvaro Yuste Valles** — [@alyusva](https://github.com/alyusva)
