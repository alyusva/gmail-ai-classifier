"""
Módulo de clasificación de emails usando Claude API (Anthropic).
"""
import json
import time

import anthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from . import config, db

SYSTEM_PROMPT = """Eres un asistente experto en organización de correo electrónico.
Tu tarea es clasificar emails en categorías basándote en su asunto (subject), remitente (sender) y snippet.

REGLAS:
1. Asigna exactamente 1 categoría principal por email (excepcionalmente 2 si claramente pertenece a dos).
2. Usa SOLO categorías de la taxonomía proporcionada.
3. Si un email no encaja bien en ninguna categoría, usa "Otros".
4. Sé consistente: el mismo tipo de remitente siempre debe ir a la misma categoría.
5. Prioriza la intención del email sobre el remitente (ej: un email de Amazon sobre un pedido = "Compras/Pedidos", un email promocional de Amazon = "Spam/Promociones").

Responde SOLO con un JSON array válido, sin texto adicional ni markdown."""

CLASSIFY_PROMPT_TEMPLATE = """Clasifica los siguientes {count} emails en las categorías disponibles.

CATEGORÍAS DISPONIBLES:
{taxonomy}

EMAILS A CLASIFICAR:
{emails_json}

Responde con un JSON array donde cada elemento tiene:
- "id": el id del email
- "labels": array con 1-2 categorías de la lista anterior
- "confidence": número entre 0.0 y 1.0 indicando tu confianza

Ejemplo de respuesta:
[
  {{"id": "abc123", "labels": ["Compras/Pedidos"], "confidence": 0.95}},
  {{"id": "def456", "labels": ["Newsletters"], "confidence": 0.88}}
]

Responde SOLO con el JSON array, sin texto adicional ni bloques de código."""


def get_client() -> anthropic.Anthropic:
    """Crea cliente de Anthropic."""
    api_key = config.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY no configurada. "
            "Exporta la variable de entorno: export ANTHROPIC_API_KEY=sk-..."
        )
    return anthropic.Anthropic(api_key=api_key)


def format_emails_for_prompt(emails: list[dict]) -> str:
    """Formatea emails para enviar a Claude de forma compacta."""
    compact = []
    for e in emails:
        compact.append(
            {
                "id": e["id"],
                "subject": (e.get("subject", "") or "")[:120],
                "sender": (e.get("sender", "") or "")[:80],
                "sender_email": (e.get("sender_email", "") or "")[:80],
                "snippet": (e.get("snippet", "") or "")[:150],
            }
        )
    return json.dumps(compact, ensure_ascii=False, indent=None)


def get_taxonomy_list() -> list[str]:
    """Obtiene la taxonomía actual (DB + defaults)."""
    saved = db.get_taxonomy()
    if saved:
        return list(saved.keys())
    return config.DEFAULT_TAXONOMY.copy()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=60),
)
def classify_batch(client: anthropic.Anthropic, emails: list[dict]) -> list[dict]:
    """Clasifica un batch de emails usando Claude."""
    taxonomy = get_taxonomy_list()
    taxonomy_str = "\n".join(f"- {t}" for t in taxonomy)

    prompt = CLASSIFY_PROMPT_TEMPLATE.format(
        count=len(emails),
        taxonomy=taxonomy_str,
        emails_json=format_emails_for_prompt(emails),
    )

    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    # Extraer texto de la respuesta
    text = response.content[0].text.strip()

    # Limpiar posibles backticks markdown
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    try:
        results = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error("Error parseando respuesta de Claude: {}", e)
        logger.debug("Respuesta raw: {}", text[:500])
        raise

    # Validar formato
    valid_labels = set(taxonomy)
    validated = []
    for r in results:
        if "id" not in r or "labels" not in r:
            continue
        # Filtrar labels que no estén en la taxonomía
        clean_labels = [l for l in r["labels"] if l in valid_labels]
        if not clean_labels:
            clean_labels = ["Otros"]
        validated.append(
            {
                "email_id": r["id"],
                "labels": clean_labels,
                "confidence": r.get("confidence", 0.0),
            }
        )

    return validated


def classify_all_emails():
    """Clasifica todos los emails no clasificados."""
    db.init_db()
    client = get_client()

    total_unclassified = db.count_unclassified()
    if total_unclassified == 0:
        logger.info("No hay emails pendientes de clasificar.")
        return

    logger.info("{} emails pendientes de clasificar", total_unclassified)

    batch_size = config.CLASSIFY_BATCH_SIZE
    total_classified = 0
    errors = 0

    pbar = tqdm(total=total_unclassified, desc="Clasificando", unit="emails")

    offset = 0
    while True:
        emails = db.get_unclassified_emails(limit=batch_size, offset=0)
        if not emails:
            break

        try:
            classifications = classify_batch(client, emails)
            if classifications:
                db.save_classifications(classifications)
                total_classified += len(classifications)
                pbar.update(len(classifications))

            # Rate limiting para la API de Anthropic
            time.sleep(1)

        except Exception as e:
            errors += 1
            logger.error("Error clasificando batch: {}", e)
            if errors > 10:
                logger.error("Demasiados errores consecutivos, deteniendo.")
                break
            time.sleep(5)
            continue

    pbar.close()

    logger.success(
        "Clasificación completada. {} emails clasificados, {} errores.",
        total_classified,
        errors,
    )

    # Mostrar estadísticas rápidas
    stats = db.get_stats()
    logger.info("Distribución de categorías:")
    for label, count in stats["distribution"].items():
        logger.info("  {}: {} emails", label, count)

    return total_classified
