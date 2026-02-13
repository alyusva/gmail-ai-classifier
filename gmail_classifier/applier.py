"""
Módulo para crear etiquetas en Gmail y aplicarlas a los emails clasificados.
"""
import json
import time

from googleapiclient.errors import HttpError
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from . import config, db
from .extractor import get_gmail_service


def get_existing_labels(service) -> dict[str, str]:
    """Obtiene las etiquetas existentes en Gmail. Retorna {nombre: id}."""
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])
    return {l["name"]: l["id"] for l in labels}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15))
def create_gmail_label(service, label_name: str) -> str:
    """Crea una etiqueta en Gmail y devuelve su ID."""
    body = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    try:
        result = service.users().labels().create(userId="me", body=body).execute()
        return result["id"]
    except HttpError as e:
        if e.resp.status == 409:
            # La etiqueta ya existe, buscarla
            existing = get_existing_labels(service)
            if label_name in existing:
                return existing[label_name]
        raise


def ensure_labels_exist(service, dry_run: bool = False) -> dict[str, str]:
    """
    Crea todas las etiquetas necesarias en Gmail.
    Retorna {categoría: gmail_label_id}.
    """
    # Obtener categorías necesarias desde las clasificaciones
    stats = db.get_stats()
    categories = list(stats["distribution"].keys())

    if not categories:
        logger.warning("No hay clasificaciones, no se crean etiquetas.")
        return {}

    existing = get_existing_labels(service)
    label_map = {}

    for category in categories:
        full_name = f"{config.LABEL_PREFIX}/{category}"

        if full_name in existing:
            label_id = existing[full_name]
            logger.debug("Etiqueta ya existe: {} ({})", full_name, label_id)
        elif dry_run:
            label_id = f"DRY_RUN_{category}"
            logger.info("[DRY RUN] Se crearía etiqueta: {}", full_name)
        else:
            label_id = create_gmail_label(service, full_name)
            logger.info("Etiqueta creada: {} ({})", full_name, label_id)
            time.sleep(0.2)

        label_map[category] = label_id
        db.save_taxonomy_label(category, label_id)

    return label_map


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15))
def apply_labels_to_message(service, msg_id: str, label_ids: list[str]):
    """Aplica etiquetas a un mensaje específico."""
    body = {"addLabelIds": label_ids, "removeLabelIds": []}
    service.users().messages().modify(
        userId="me", id=msg_id, body=body
    ).execute()


def apply_all_labels(dry_run: bool = False, batch_limit: int = 0):
    """
    Aplica las etiquetas clasificadas a todos los emails en Gmail.

    Args:
        dry_run: Si True, solo muestra qué haría sin aplicar cambios.
        batch_limit: Límite de emails a procesar (0 = todos).
    """
    db.init_db()
    service = get_gmail_service()

    # Asegurar que las etiquetas existen
    label_map = ensure_labels_exist(service, dry_run=dry_run)
    if not label_map:
        return

    # Obtener clasificaciones pendientes
    with db.get_db() as conn:
        query = """
            SELECT c.email_id, c.labels, e.subject, e.sender
            FROM classifications c
            JOIN emails e ON c.email_id = e.id
            WHERE c.applied = 0
        """
        if batch_limit > 0:
            query += f" LIMIT {batch_limit}"

        rows = conn.execute(query).fetchall()

    if not rows:
        logger.info("No hay clasificaciones pendientes de aplicar.")
        return

    total = len(rows)
    logger.info(
        "{} emails pendientes de etiquetar{}",
        total,
        " [DRY RUN]" if dry_run else "",
    )

    applied_count = 0
    error_count = 0

    pbar = tqdm(total=total, desc="Aplicando etiquetas", unit="emails")

    for row in rows:
        email_id = row["email_id"]
        categories = json.loads(row["labels"])
        subject = row["subject"][:60]

        # Mapear categorías a label IDs de Gmail
        gmail_label_ids = []
        for cat in categories:
            lid = label_map.get(cat)
            if lid and not lid.startswith("DRY_RUN_"):
                gmail_label_ids.append(lid)

        if dry_run:
            cats_str = ", ".join(categories)
            logger.info(
                "[DRY RUN] {} → [{}] | {}",
                subject,
                cats_str,
                row["sender"],
            )
            applied_count += 1
        else:
            if gmail_label_ids:
                try:
                    apply_labels_to_message(service, email_id, gmail_label_ids)
                    db.mark_as_applied([email_id])
                    applied_count += 1
                    time.sleep(0.05)  # Rate limiting
                except Exception as e:
                    error_count += 1
                    logger.error(
                        "Error etiquetando {} ({}): {}", email_id, subject, e
                    )
                    if error_count > 50:
                        logger.error("Demasiados errores, deteniendo.")
                        break

        pbar.update(1)

    pbar.close()

    action = "simulados" if dry_run else "etiquetados"
    logger.success(
        "{} emails {}, {} errores.", applied_count, action, error_count
    )
