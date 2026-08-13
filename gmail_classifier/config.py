"""
Configuración central del proyecto Gmail Classifier.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# === Rutas ===
# __file__ está en gmail_classifier/gmail_classifier/config.py
# .parent.parent nos lleva a la raíz del proyecto
PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
try:
    DATA_DIR.mkdir(exist_ok=True)
except OSError:
    # Filesystem de solo lectura (p.ej. la función serverless en Vercel, que
    # no usa SQLite ni credentials.json locales, solo la taxonomía/config).
    pass

DB_PATH = DATA_DIR / "emails.db"
CREDENTIALS_PATH = PROJECT_DIR / "credentials.json"
TOKEN_PATH = DATA_DIR / "token.json"

# === Cargar variables de entorno desde .env ===
# override=True hace que .env tenga prioridad sobre variables del sistema
ENV_FILE = PROJECT_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)

# === Gmail API ===
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]
GMAIL_BATCH_SIZE = 100  # emails por página de Gmail API
GMAIL_MAX_RESULTS_PER_PAGE = 500  # máximo permitido por Gmail API

# === Anthropic API ===
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
CLASSIFY_BATCH_SIZE = int(os.getenv("CLASSIFY_BATCH_SIZE", "50"))  # emails por llamada a Claude

# === Taxonomía por defecto ===
# "Otros" no se incluye aquí: es la categoría de último recurso para correos
# ambiguos (ver FALLBACK_CATEGORY), no una categoría objetivo del usuario.
DEFAULT_TAXONOMY = [
    "Bancos/Finanzas",
    "Compras/Pedidos",
    "Desarrollo/Tech",
    "Formación/Educación",
    "Gobierno/Administración",
    "Hipoteca",
    "Newsletters",
    "Notificaciones/Alertas",
    "Personal",
    "Redes Sociales",
    "Salud/Deporte",
    "Spam/Promociones",
    "Suscripciones/SaaS",
    "Trabajo",
    "Viajes/Transporte",
]
FALLBACK_CATEGORY = "Otros"
MAX_LABELS_PER_EMAIL = 2

# === Etiqueta de marca en Gmail ===
# Las categorías se crean como labels sueltas de nivel superior (p.ej.
# "Trabajo", "Bancos/Finanzas" — el "/" interno es parte del nombre de esa
# categoría, no un prefijo añadido). Además, todo email procesado recibe la
# label de marca MARKER_LABEL (p.ej. "IA"), que NO es padre de las demás,
# para poder detectar correo nuevo con una simple query de Gmail
# (-label:IA) sin necesitar ninguna base de datos externa.
MARKER_LABEL = os.getenv("MARKER_LABEL", "IA")

# === Logging ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = DATA_DIR / "classifier.log"
