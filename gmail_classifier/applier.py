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


def ensure_labels_exist(
    service, categories: list[str] | None = None, dry_run: bool = False
) -> dict[str, str]:
    """
    Crea todas las etiquetas necesarias en Gmail: la label de marca
    `MARKER_LABEL` (p.ej. "IA", aplicada a todo email procesado para poder
    detectar correo nuevo sin base de datos) + una por categoría, sueltas de
    nivel superior (sin prefijo compartido — el "/" de categorías como
    "Bancos/Finanzas" es parte de su propio nombre, no un prefijo añadido).

    Retorna {categoría: gmail_label_id, "__marker__": gmail_label_id}.
    """
    if categories is None:
        # Uso local (CLI): categorías realmente presentes en las clasificaciones
        # + la taxonomía completa, para que siempre queden creadas de antemano.
        stats = db.get_stats()
        categories = sorted(
            set(stats["distribution"].keys())
            | set(config.DEFAULT_TAXONOMY)
            | {config.FALLBACK_CATEGORY}
        )

    existing = get_existing_labels(service)
    label_map = {}

    # Label de marca: indica "ya clasificado", no es padre de las categorías.
    if config.MARKER_LABEL in existing:
        marker_id = existing[config.MARKER_LABEL]
    elif dry_run:
        marker_id = "DRY_RUN_marker"
        logger.info("[DRY RUN] Se crearía etiqueta de marca: {}", config.MARKER_LABEL)
    else:
        marker_id = create_gmail_label(service, config.MARKER_LABEL)
        logger.info("Etiqueta de marca creada: {} ({})", config.MARKER_LABEL, marker_id)
        time.sleep(0.2)
    label_map["__marker__"] = marker_id

    for category in categories:
        if category in existing:
            label_id = existing[category]
            logger.debug("Etiqueta ya existe: {} ({})", category, label_id)
        elif dry_run:
            label_id = f"DRY_RUN_{category}"
            logger.info("[DRY RUN] Se crearía etiqueta: {}", category)
        else:
            label_id = create_gmail_label(service, category)
            logger.info("Etiqueta creada: {} ({})", category, label_id)
            time.sleep(0.2)

        label_map[category] = label_id
        db.save_taxonomy_label(category, label_id)

    return label_map


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15))
def apply_labels_to_message(
    service, msg_id: str, add_label_ids: list[str], remove_label_ids: list[str] | None = None
):
    """Aplica (y opcionalmente quita) etiquetas de un mensaje específico.

    `remove_label_ids` permite quitar labels gestionadas (marca/categorías)
    obsoletas del propio mensaje al re-clasificarlo, para que re-ejecutar el
    pipeline sea seguro y no vaya acumulando etiquetas viejas.

    Uso: correo nuevo procesado de uno en uno (p.ej. el cron de Vercel). Para
    el repaso masivo local, usa `batch_apply_labels`, mucho más rápido.
    """
    body = {"addLabelIds": add_label_ids, "removeLabelIds": remove_label_ids or []}
    service.users().messages().modify(
        userId="me", id=msg_id, body=body
    ).execute()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15))
def batch_apply_labels(
    service, msg_ids: list[str], add_label_ids: list[str], remove_label_ids: list[str] | None = None
):
    """Aplica el mismo conjunto de etiquetas a hasta 1000 mensajes en una
    sola llamada (`users.messages.batchModify`). Muchísimo más rápido que
    `apply_labels_to_message` uno a uno para un repaso masivo, siempre que
    los mensajes del lote compartan exactamente las mismas etiquetas a
    añadir/quitar (ver `apply_all_labels`, que agrupa por esa combinación)."""
    body = {
        "ids": msg_ids,
        "addLabelIds": add_label_ids,
        "removeLabelIds": remove_label_ids or [],
    }
    service.users().messages().batchModify(userId="me", body=body).execute()


def cleanup_orphan_labels(
    service, keep_categories: list[str], dry_run: bool = False
) -> list[str]:
    """Borra labels de categorías que ya gestionamos (según la tabla
    `taxonomy` local) pero que ya no están en `keep_categories` y no tienen
    ningún mensaje asociado — huérfanas de una taxonomía anterior. Como las
    categorías ahora son labels sueltas sin prefijo compartido, la única
    forma fiable de saber "qué label es nuestra" es lo que ya creamos
    nosotros mismos (tabla `taxonomy`), no el nombre de la label en Gmail.
    Devuelve los nombres borrados (o que se borrarían, en dry-run)."""
    known = db.get_taxonomy()  # {categoría: gmail_label_id} ya creadas alguna vez
    orphan_categories = set(known) - set(keep_categories)
    deleted = []

    for category in orphan_categories:
        label_id = known[category]

        try:
            detail = service.users().labels().get(userId="me", id=label_id).execute()
        except HttpError as e:
            if e.resp.status == 404:
                # Ya no existe en Gmail (p.ej. borrada a mano) — limpiar solo la BD.
                if not dry_run:
                    db.delete_taxonomy_label(category)
                deleted.append(category)
                continue
            raise

        msg_count = detail.get("messagesTotal", 0)
        if msg_count > 0:
            logger.warning(
                "Label huérfana {} tiene {} mensajes, no se borra automáticamente.",
                category,
                msg_count,
            )
            continue

        if dry_run:
            logger.info("[DRY RUN] Se borraría label vacía: {}", category)
        else:
            service.users().labels().delete(userId="me", id=label_id).execute()
            db.delete_taxonomy_label(category)
            logger.info("Label huérfana borrada: {}", category)
        deleted.append(category)

    return deleted


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

    marker_id = label_map.get("__marker__")
    marker_ids = {marker_id} if marker_id and not marker_id.startswith("DRY_RUN_") else set()

    # IDs de todas las labels que gestionamos (marca + categorías), para poder
    # detectar y quitar restos de una clasificación anterior sobre el mismo
    # mensaje al re-ejecutar el pipeline.
    managed_label_ids = {
        lid for lid in label_map.values() if lid and not lid.startswith("DRY_RUN_")
    }

    # Obtener clasificaciones pendientes
    with db.get_db() as conn:
        query = """
            SELECT c.email_id, c.labels, e.subject, e.sender, e.labels_original
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

    if dry_run:
        for row in rows:
            categories = json.loads(row["labels"])
            logger.info(
                "[DRY RUN] {} → [{}] | {}",
                row["subject"][:60],
                ", ".join(categories),
                row["sender"],
            )
            applied_count += 1
            pbar.update(1)
        pbar.close()
        logger.success("{} emails simulados, {} errores.", applied_count, error_count)
        return

    # Agrupar por la combinación exacta de labels a añadir/quitar, para poder
    # aplicar hasta 1000 mensajes por llamada con batchModify en vez de una
    # llamada por email (esto último tardaría horas para bandejas grandes).
    groups: dict[tuple[tuple[str, ...], tuple[str, ...]], list[str]] = {}
    for row in rows:
        email_id = row["email_id"]
        categories = json.loads(row["labels"])

        gmail_label_ids = [
            lid
            for cat in categories
            if (lid := label_map.get(cat)) and not lid.startswith("DRY_RUN_")
        ]
        add_label_ids = {*gmail_label_ids, *marker_ids}
        if not add_label_ids:
            continue

        current_ids = set(json.loads(row["labels_original"] or "[]"))
        remove_label_ids = (current_ids & managed_label_ids) - add_label_ids

        key = (tuple(sorted(add_label_ids)), tuple(sorted(remove_label_ids)))
        groups.setdefault(key, []).append(email_id)

    consecutive_chunk_errors = 0
    for (add_key, remove_key), email_ids in groups.items():
        for i in range(0, len(email_ids), 1000):
            chunk = email_ids[i : i + 1000]
            try:
                batch_apply_labels(service, chunk, list(add_key), list(remove_key))
                db.mark_as_applied(chunk)
                applied_count += len(chunk)
                consecutive_chunk_errors = 0
                time.sleep(0.3)  # Rate limiting entre llamadas batch
            except Exception as e:
                error_count += len(chunk)
                consecutive_chunk_errors += 1
                logger.error("Error en lote de {} emails: {}", len(chunk), e)
                if consecutive_chunk_errors > 5:
                    logger.error("Demasiados lotes fallidos seguidos, deteniendo.")
                    pbar.update(total - applied_count - error_count)
                    pbar.close()
                    logger.success(
                        "{} emails etiquetados, {} errores.", applied_count, error_count
                    )
                    return
            pbar.update(len(chunk))

    pbar.close()
    logger.success("{} emails etiquetados, {} errores.", applied_count, error_count)
