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
DATA_DIR.mkdir(exist_ok=True)

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
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
CLASSIFY_BATCH_SIZE = int(os.getenv("CLASSIFY_BATCH_SIZE", "50"))  # emails por llamada a Claude

# === Taxonomía por defecto ===
DEFAULT_TAXONOMY = [
    "Newsletters",
    "Compras/Pedidos",
    "Bancos/Finanzas",
    "Trabajo",
    "Redes Sociales",
    "Suscripciones/SaaS",
    "Notificaciones/Alertas",
    "Personal",
    "Spam/Promociones",
    "Desarrollo/Tech",
    "Formación/Educación",
    "Viajes/Transporte",
    "Gobierno/Administración",
    "Salud",
    "Otros",
]

# === Label prefix en Gmail ===
LABEL_PREFIX = os.getenv("LABEL_PREFIX", "AutoSort")  # Las etiquetas se crean como "AutoSort/Categoria"

# === Logging ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = DATA_DIR / "classifier.log"
