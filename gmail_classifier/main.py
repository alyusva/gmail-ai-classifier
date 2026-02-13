#!/usr/bin/env python3
"""
Gmail Classifier - CLI para clasificar automáticamente emails de Gmail usando IA.

Uso:
    python -m gmail_classifier.main extract     # Fase 1: Extraer emails
    python -m gmail_classifier.main classify    # Fase 2: Clasificar con Claude
    python -m gmail_classifier.main apply       # Fase 3: Aplicar etiquetas en Gmail
    python -m gmail_classifier.main stats       # Ver estadísticas
    python -m gmail_classifier.main dry-run     # Simular aplicación de etiquetas
"""
import argparse
import sys

from loguru import logger
from tabulate import tabulate

from . import config
from .db import init_db, get_stats, count_emails, count_unclassified


def setup_logging(verbose: bool = False):
    """Configura loguru."""
    logger.remove()
    level = "DEBUG" if verbose else config.LOG_LEVEL
    logger.add(sys.stderr, level=level, format="<green>{time:HH:mm:ss}</green> | <level>{level:^8}</level> | {message}")
    logger.add(
        str(config.LOG_FILE),
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
    )


def cmd_extract(args):
    """Fase 1: Extraer emails de Gmail."""
    from .extractor import extract_all_emails

    logger.info("=" * 60)
    logger.info("FASE 1: EXTRACCIÓN DE EMAILS")
    logger.info("=" * 60)

    max_emails = args.max if hasattr(args, "max") and args.max else None
    total = extract_all_emails(max_emails=max_emails)
    logger.info("Total extraídos: {}", total)


def cmd_classify(args):
    """Fase 2: Clasificar emails con Claude."""
    from .classifier import classify_all_emails

    logger.info("=" * 60)
    logger.info("FASE 2: CLASIFICACIÓN CON IA")
    logger.info("=" * 60)

    if not config.ANTHROPIC_API_KEY:
        logger.error(
            "ANTHROPIC_API_KEY no configurada.\n"
            "Ejecuta: export ANTHROPIC_API_KEY=sk-ant-..."
        )
        sys.exit(1)

    total = classify_all_emails()
    logger.info("Total clasificados: {}", total)


def cmd_apply(args):
    """Fase 3: Aplicar etiquetas en Gmail."""
    from .applier import apply_all_labels

    dry_run = args.dry_run if hasattr(args, "dry_run") else False
    batch_limit = args.limit if hasattr(args, "limit") else 0

    mode = "DRY RUN" if dry_run else "APLICACIÓN"
    logger.info("=" * 60)
    logger.info("FASE 3: {} DE ETIQUETAS", mode)
    logger.info("=" * 60)

    apply_all_labels(dry_run=dry_run, batch_limit=batch_limit)


def cmd_stats(args):
    """Muestra estadísticas de clasificación."""
    init_db()
    stats = get_stats()

    print("\n" + "=" * 60)
    print("📊 ESTADÍSTICAS DE CLASIFICACIÓN")
    print("=" * 60)

    summary = [
        ["Total emails extraídos", stats["total_emails"]],
        ["Clasificados", stats["classified"]],
        ["Pendientes de clasificar", stats["unclassified"]],
        ["Etiquetas aplicadas", stats["applied"]],
        ["Pendientes de aplicar", stats["pending_apply"]],
    ]
    print(tabulate(summary, headers=["Métrica", "Valor"], tablefmt="rounded_grid"))

    if stats["distribution"]:
        print("\n📋 DISTRIBUCIÓN POR CATEGORÍA:")
        print("-" * 45)
        dist_table = [
            [label, count, f"{count/stats['classified']*100:.1f}%"]
            for label, count in stats["distribution"].items()
        ]
        print(
            tabulate(
                dist_table,
                headers=["Categoría", "Emails", "%"],
                tablefmt="rounded_grid",
            )
        )
    else:
        print("\nNo hay clasificaciones aún. Ejecuta 'classify' primero.")

    print()


def cmd_dry_run(args):
    """Atajo para dry-run."""
    args.dry_run = True
    args.limit = args.limit if hasattr(args, "limit") else 50
    cmd_apply(args)


def cmd_reset(args):
    """Resetea la base de datos (con confirmación)."""
    target = args.target if hasattr(args, "target") else "all"

    if target == "all":
        confirm = input(
            "⚠️  Esto eliminará TODOS los datos (emails, clasificaciones, progreso).\n"
            "¿Estás seguro? (escribe 'SI' para confirmar): "
        )
        if confirm != "SI":
            print("Cancelado.")
            return
        config.DB_PATH.unlink(missing_ok=True)
        logger.info("Base de datos eliminada.")
    elif target == "classifications":
        confirm = input(
            "⚠️  Esto eliminará todas las clasificaciones (mantendrá emails extraídos).\n"
            "¿Estás seguro? (escribe 'SI' para confirmar): "
        )
        if confirm != "SI":
            print("Cancelado.")
            return
        from .db import get_db
        with get_db() as conn:
            conn.execute("DELETE FROM classifications")
        logger.info("Clasificaciones eliminadas.")
    elif target == "applied":
        from .db import get_db
        with get_db() as conn:
            conn.execute("UPDATE classifications SET applied = 0, applied_at = NULL")
        logger.info("Marcas de aplicación reseteadas.")


def cmd_auto(args):
    """Ejecuta el flujo completo: extract → classify → apply."""
    import time
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("🤖 MODO AUTOMÁTICO - FLUJO COMPLETO")
    logger.info("=" * 60)

    # Fase 1: Extract (si no se salta)
    if not args.skip_extract:
        logger.info("\n📥 FASE 1/3: EXTRAYENDO EMAILS...")
        cmd_extract(args)
    else:
        logger.info("\n⏭️  Saltando extracción (--skip-extract)")

    # Fase 2: Classify
    logger.info("\n🧠 FASE 2/3: CLASIFICANDO CON IA...")
    cmd_classify(args)

    # Mostrar stats antes de aplicar
    logger.info("\n📊 ESTADÍSTICAS PREVIAS A APLICAR:")
    cmd_stats(args)

    # Fase 3: Apply (o dry-run)
    if args.dry_run:
        logger.info("\n🔍 FASE 3/3: SIMULACIÓN (DRY RUN)...")
        args.limit = 50  # Mostrar solo 50 en dry-run
        cmd_apply(args)
        logger.info("\n✅ Modo dry-run completado. Usa 'auto' sin --dry-run para aplicar.")
    else:
        logger.info("\n✅ FASE 3/3: APLICANDO ETIQUETAS EN GMAIL...")
        confirm = input("\n⚠️  ¿Aplicar etiquetas en Gmail? (escribe 'SI' para confirmar): ")
        if confirm != "SI":
            logger.info("Aplicación cancelada.")
            return
        cmd_apply(args)

    elapsed = time.time() - start_time
    logger.success(f"\n🎉 FLUJO COMPLETO TERMINADO en {elapsed/60:.1f} minutos")


def main():
    parser = argparse.ArgumentParser(
        description="📧 Gmail Classifier - Clasifica automáticamente tus emails con IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Flujo recomendado:
  🤖 Automático (TODO DE UNA VEZ):
     python -m gmail_classifier.main auto           # Extract → Classify → Apply
     python -m gmail_classifier.main auto --dry-run # Simular sin aplicar

  📝 Manual (PASO A PASO):
     1. python -m gmail_classifier.main extract        # Descargar emails
     2. python -m gmail_classifier.main classify       # Clasificar con Claude
     3. python -m gmail_classifier.main stats          # Revisar distribución
     4. python -m gmail_classifier.main dry-run        # Simular etiquetado
     5. python -m gmail_classifier.main apply          # Aplicar etiquetas
        """,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Modo verbose")

    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # Extract
    p_extract = subparsers.add_parser("extract", help="Extraer emails de Gmail")
    p_extract.add_argument(
        "--max", type=int, default=0, help="Máximo de emails a extraer (0=todos)"
    )

    # Classify
    p_classify = subparsers.add_parser("classify", help="Clasificar emails con Claude")

    # Apply
    p_apply = subparsers.add_parser("apply", help="Aplicar etiquetas en Gmail")
    p_apply.add_argument(
        "--dry-run", action="store_true", help="Simular sin aplicar cambios"
    )
    p_apply.add_argument(
        "--limit", type=int, default=0, help="Límite de emails a procesar"
    )

    # Stats
    p_stats = subparsers.add_parser("stats", help="Ver estadísticas")

    # Dry run (atajo)
    p_dry = subparsers.add_parser("dry-run", help="Simular aplicación de etiquetas")
    p_dry.add_argument(
        "--limit", type=int, default=50, help="Emails a mostrar en simulación"
    )

    # Reset
    p_reset = subparsers.add_parser("reset", help="Resetear datos")
    p_reset.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=["all", "classifications", "applied"],
        help="Qué resetear: all, classifications, applied",
    )

    # Auto (nuevo)
    p_auto = subparsers.add_parser("auto", help="Ejecuta todo el flujo automáticamente")
    p_auto.add_argument(
        "--max", type=int, default=0, help="Máximo de emails a extraer (0=todos)"
    )
    p_auto.add_argument(
        "--skip-extract", action="store_true", help="Saltar extracción (usar emails ya descargados)"
    )
    p_auto.add_argument(
        "--dry-run", action="store_true", help="Simular sin aplicar etiquetas"
    )

    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "extract": cmd_extract,
        "classify": cmd_classify,
        "apply": cmd_apply,
        "stats": cmd_stats,
        "dry-run": cmd_dry_run,
        "reset": cmd_reset,
        "auto": cmd_auto,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
